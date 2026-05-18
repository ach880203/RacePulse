# -*- coding: utf-8 -*-
# =============================================================================
# feature_batch.py — 피처 배치 계산 서비스
# =============================================================================
# 배치 처리(Batch Processing)란?
#   하나씩 처리하는 대신 여러 건을 한꺼번에 묶어서 처리하는 방식입니다.
#   예: 경주 1개에 말이 10마리 출전 → 10마리 피처를 한 번에 계산합니다.
#
# pandas DataFrame이란?
#   표(테이블) 모양의 데이터를 파이썬에서 편리하게 다루는 자료구조입니다.
#   엑셀 시트와 비슷하다고 생각하면 됩니다.
#   예: DataFrame 컬럼 하나 = 피처 하나, 행 하나 = 말 1마리의 피처 벡터
# =============================================================================

# logging = 서버 로그를 기록하는 표준 라이브러리입니다.
import logging
# datetime/date = 날짜 범위 계산에 사용합니다.
from datetime import date, timedelta
# Any = 타입 힌트입니다.
from typing import Any

# pandas = 표 형태 데이터를 편리하게 다루는 라이브러리입니다.
import pandas as pd

# SQLAlchemy 도구들
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.models.race import Race, RaceEntry
from app.services.feature_engineering import FeatureEngineeringService

logger = logging.getLogger(__name__)


class FeatureBatchService:
    """특정 경주 또는 날짜 범위의 피처를 일괄 계산하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # FeatureEngineeringService를 내부에서 공유합니다.
        self.feature_svc = FeatureEngineeringService(db)

    async def calculate_all_features_for_race(self, race_id: int) -> dict[str, Any]:
        """특정 경주에 출전한 모든 말의 피처를 계산하고 저장합니다.

        @param race_id  피처를 계산할 경주 ID
        @return 계산 결과 요약 딕셔너리
        """
        # 해당 경주의 출전 명단 조회
        entries_stmt = select(RaceEntry).where(RaceEntry.race_id == race_id)
        entries = list((await self.db.scalars(entries_stmt)).all())

        if not entries:
            logger.warning("[배치 피처] race_id=%d 출전 명단 없음", race_id)
            return {"race_id": race_id, "processed": 0, "errors": 0}

        logger.info("[배치 피처] race_id=%d 출전마 %d마리 계산 시작", race_id, len(entries))

        processed = 0
        errors    = 0
        results: list[dict[str, Any]] = []

        for entry in entries:
            try:
                # 1. 피처 계산
                features = await self.feature_svc.build_feature_vector(entry.id)

                # 2. DB 저장
                await self.feature_svc.save_to_feature_store(
                    race_entry_id=entry.id,
                    race_id=race_id,
                    features=features,
                )

                # 배치 요약용으로 말번과 피처 개수를 기록합니다.
                results.append({
                    "race_entry_id": entry.id,
                    "gate_no":       entry.gate_no,
                    "feature_count": len(features),
                })
                processed += 1

            except Exception as exc:
                import traceback
                logger.error(
                    "[배치 피처] race_entry_id=%d 계산 실패:\n%s",
                    entry.id,
                    traceback.format_exc(),
                )
                # PostgreSQL 트랜잭션이 오염(aborted)된 상태를 복구합니다.
                # rollback 없이 계속하면 이후 entry들이 전부 InFailedSQLTransactionError로 연쇄 실패합니다.
                await self.db.rollback()
                errors += 1

        logger.info(
            "[배치 피처] race_id=%d 완료. 성공=%d, 실패=%d",
            race_id, processed, errors
        )

        # pandas DataFrame으로 결과 요약을 출력합니다.
        # DataFrame이란? 표(테이블) 형태의 데이터 구조입니다.
        if results:
            df = pd.DataFrame(results)
            logger.debug("\n%s", df.to_string(index=False))

        return {
            "race_id":   race_id,
            "processed": processed,
            "errors":    errors,
            "entries":   results,
        }

    async def recalculate_historical_features(
        self,
        start_date: date,
        end_date: date,
    ) -> dict[str, Any]:
        """날짜 범위 내 완료된 경주들의 피처를 일괄 재계산합니다.

        언제 사용하는가?
          피처 계산 로직이 변경됐을 때(FEATURE_VERSION이 올라갔을 때)
          과거 데이터를 새 로직으로 다시 계산해서 모델 재학습에 사용합니다.

        @param start_date 재계산 시작 날짜
        @param end_date   재계산 종료 날짜
        """
        logger.info(
            "[히스토리 배치] %s ~ %s 피처 재계산 시작",
            start_date.isoformat(), end_date.isoformat()
        )

        # 완료된 경주 ID 목록 조회
        from app.models.race import RaceStatusEnum
        races_stmt = (
            select(Race.id, Race.rc_date, Race.race_name)
            .where(
                and_(
                    Race.rc_date >= start_date,
                    Race.rc_date <= end_date,
                    Race.status == RaceStatusEnum.COMPLETED,
                )
            )
            .order_by(Race.rc_date)
        )
        races = list((await self.db.execute(races_stmt)).all())

        total_processed = 0
        total_errors    = 0

        for race_id, rc_date, race_name in races:
            try:
                result = await self.calculate_all_features_for_race(race_id)
                total_processed += result["processed"]
                total_errors    += result["errors"]
                logger.info(
                    "[히스토리 배치] %s %s 완료 (성공 %d)",
                    rc_date, race_name, result["processed"]
                )
            except Exception as exc:
                logger.error(
                    "[히스토리 배치] race_id=%d 실패: %s", race_id, exc
                )
                total_errors += 1

        logger.info(
            "[히스토리 배치] 전체 완료. 총 성공=%d, 총 실패=%d",
            total_processed, total_errors
        )
        return {
            "start_date":      start_date.isoformat(),
            "end_date":        end_date.isoformat(),
            "races_processed": len(races),
            "total_processed": total_processed,
            "total_errors":    total_errors,
        }
