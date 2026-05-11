# -*- coding: utf-8 -*-
# =============================================================================
# ml.py — ML 피처 계산 및 조회 API 라우터
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# date = 날짜 파라미터 파싱에 사용합니다.
from datetime import date

# FastAPI 도구들
from fastapi import APIRouter, Depends, HTTPException

# SQLAlchemy
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.core.database import get_db
from app.models.ml import MLFeatureStore
from app.models.race import RaceEntry
from app.services.feature_engineering import FeatureEngineeringService, FEATURE_VERSION
from app.services.feature_batch import FeatureBatchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml")


@router.post("/features/calculate/{race_id}")
async def calculate_race_features(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주에 출전한 모든 말의 ML 피처를 계산하고 저장합니다.

    완료 기준 1: POST /ml/features/calculate/1 → 피처 계산 성공

    @param race_id  피처를 계산할 경주 ID
    """
    batch_svc = FeatureBatchService(db)
    try:
        result = await batch_svc.calculate_all_features_for_race(race_id)
        return {
            "success": True,
            "data":    result,
            "message": f"경주 {race_id}번 피처 계산 완료 ({result['processed']}마리 처리)",
        }
    except Exception as exc:
        logger.error("[ML API] 피처 계산 실패. race_id=%d, 오류=%s", race_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/features/{race_entry_id}")
async def get_features(
    race_entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """저장된 피처 벡터를 조회합니다.

    완료 기준 3: GET /ml/features/1 → 피처 조회 성공

    @param race_entry_id  조회할 출전마 레코드 ID
    """
    stmt = (
        select(MLFeatureStore)
        .where(
            and_(
                MLFeatureStore.race_entry_id == race_entry_id,
                MLFeatureStore.feature_version == FEATURE_VERSION,
            )
        )
        .order_by(MLFeatureStore.calculated_at.desc())
    )
    record = await db.scalar(stmt)

    if record is None:
        # 피처가 없으면 404를 반환하고 계산 방법을 안내합니다.
        raise HTTPException(
            status_code=404,
            detail=(
                f"race_entry_id={race_entry_id}의 피처가 없습니다. "
                f"먼저 POST /ml/features/calculate/{{race_id}} 를 실행해주세요."
            ),
        )

    features = record.features
    feature_count = len(features)

    return {
        "success": True,
        "data": {
            "raceEntryId":    record.race_entry_id,
            "raceId":         record.race_id,
            "featureVersion": record.feature_version,
            "featureCount":   feature_count,
            "calculatedAt":   record.calculated_at.isoformat(),
            "features":       features,
        },
        "message": f"피처 {feature_count}개 조회 성공",
    }


@router.post("/features/calculate-entry/{race_entry_id}")
async def calculate_single_entry_features(
    race_entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """출전마 1마리의 피처를 계산하고 저장합니다. (단건 테스트용)

    @param race_entry_id  피처를 계산할 출전마 레코드 ID
    """
    # 출전 레코드 존재 확인
    entry = await db.get(RaceEntry, race_entry_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"출전 정보를 찾을 수 없습니다: race_entry_id={race_entry_id}"
        )

    svc = FeatureEngineeringService(db)
    try:
        features = await svc.build_feature_vector(race_entry_id)
        record = await svc.save_to_feature_store(
            race_entry_id=race_entry_id,
            race_id=entry.race_id,
            features=features,
        )
        return {
            "success": True,
            "data": {
                "raceEntryId":  record.race_entry_id,
                "raceId":       record.race_id,
                "featureCount": len(features),
                "features":     features,
            },
            "message": f"피처 {len(features)}개 계산 완료",
        }
    except Exception as exc:
        logger.error("[ML API] 단건 피처 계산 실패. entry_id=%d, 오류=%s", race_entry_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/features/recalculate")
async def recalculate_historical_features(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
):
    """날짜 범위 내 완료된 경주의 피처를 일괄 재계산합니다.

    피처 계산 로직이 변경됐을 때 사용합니다.

    @param start_date  재계산 시작 날짜 (예: 2026-01-01)
    @param end_date    재계산 종료 날짜 (예: 2026-05-01)
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date가 end_date보다 클 수 없습니다.")

    batch_svc = FeatureBatchService(db)
    try:
        result = await batch_svc.recalculate_historical_features(start_date, end_date)
        return {
            "success": True,
            "data":    result,
            "message": f"히스토리 피처 재계산 완료 ({result['races_processed']}경주)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
