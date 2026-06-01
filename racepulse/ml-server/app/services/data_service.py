# -*- coding: utf-8 -*-
# =============================================================================
# data_service.py — KRA 응답 데이터를 PostgreSQL 테이블에 저장하는 서비스
# =============================================================================
# 이 파일의 핵심 역할:
# 1) 외부 API 응답을 우리 DB 스키마에 맞게 변환합니다.
# 2) 중복이면 update, 없으면 insert 하는 upsert 흐름을 처리합니다.
# 3) collection_logs 테이블에 수집 결과를 기록합니다.
# =============================================================================

# dataclass = 여러 수집 결과 숫자를 한 덩어리로 다루기 쉽게 만드는 표준 도구입니다.
from dataclasses import dataclass
# date/datetime/time = 경주일, 수집시각, 발주시간을 다루기 위한 타입입니다.
from datetime import date, datetime, time
# Decimal = 부담중량/배당/품질점수 같은 소수값을 안전하게 다루기 위한 타입입니다.
from decimal import Decimal
# Any/Literal = 다양한 응답 JSON, 상태 문자열 타입 힌트에 사용합니다.
from typing import Any, Literal

# insert = PostgreSQL 전용 ON CONFLICT upsert 문법을 SQLAlchemy로 쓰게 해주는 함수입니다.
from sqlalchemy.dialects.postgresql import insert
# func/select = 집계 함수와 조회 쿼리를 구성할 때 사용하는 SQLAlchemy 도구입니다.
from sqlalchemy import func, select
# AsyncSession = 비동기 DB 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# Horse/Jockey/Trainer/Racecourse = 기준정보 테이블 ORM 모델입니다.
from app.models.master import Horse, Jockey, Trainer, Racecourse
# Race/RaceEntry/RaceResult/CollectionLog 등 = 경주와 수집로그 관련 ORM 모델입니다.
from app.models.race import (
    ClassChangeEnum,
    CollectionLog,
    CollectStatusEnum,
    DataStatusEnum,
    DistanceChangeEnum,
    QualityStatusEnum,
    Race,
    RaceEntry,
    RaceGradeEnum,
    RaceResult,
    RaceStatusEnum,
    TrackConditionEnum,
)
# KRAApiService = 실제 외부 API 호출을 담당하는 서비스입니다.
from app.services.kra_api import KRAApiError, KRAApiService, KRARateLimitExceededError


@dataclass
class CollectionSummary:
    # api_name = 어떤 API 수집이었는지 식별하는 이름입니다.
    api_name: str
    status: str
    records_collected: int
    daily_call_count: int
    null_count: int
    anomaly_count: int
    quality_score: Decimal | None
    quality_status: str | None
    meet_code: str | None = None
    rc_date: date | None = None
    message: str | None = None


class DataService:
    def __init__(self, db: AsyncSession, kra_api_service: KRAApiService) -> None:
        self.db = db
        self.kra_api_service = kra_api_service

    async def collect_master_jockeys(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """기수 기본정보 전체를 KRA API에서 수집해 DB에 upsert합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                all_items.extend(
                    await self.kra_api_service.fetch_jockey_list(
                        meet=self._meet_code_to_api_value(meet_code),
                    )
                )

            records_collected, null_count, anomaly_count = await self._save_master_jockey_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="master_jockeys",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                message=None if records_collected > 0 else "수집된 기수 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_jockeys",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_jockeys",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_master_trainers(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """조교사 기본정보 전체를 KRA API에서 수집해 DB에 upsert합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                all_items.extend(
                    await self.kra_api_service.fetch_trainer_list(
                        meet=self._meet_code_to_api_value(meet_code),
                    )
                )

            records_collected, null_count, anomaly_count = await self._save_master_trainer_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="master_trainers",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                message=None if records_collected > 0 else "수집된 조교사 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_trainers",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_trainers",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_master_horses(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """마필 기본정보 전체를 KRA API에서 수집해 DB에 upsert합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                items = await self.kra_api_service.fetch_horse_list(
                    meet=self._meet_code_to_api_value(meet_code),
                )
                # 경마장 코드를 각 아이템에 주입합니다 (API 응답에 meet_code가 없는 경우 대비).
                for item in items:
                    item["_meet_code"] = meet_code
                all_items.extend(items)

            records_collected, null_count, anomaly_count = await self._save_master_horse_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="master_horses",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                message=None if records_collected > 0 else "수집된 마필 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_horses",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="master_horses",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_horse_results(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """경주마 통산/최근1년 승률·복승률을 KRA API(raceHorseResult_2)에서 수집해 DB에 업데이트합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                items = await self.kra_api_service.fetch_horse_result_list(
                    meet=self._meet_code_to_api_value(meet_code),
                )
                for item in items:
                    item["_meet_code"] = meet_code
                all_items.extend(items)

            records_collected, null_count, anomaly_count = await self._save_horse_result_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="horse_results",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                message=None if records_collected > 0 else "수집된 경주마 성적 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_results",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_results",
                status=CollectStatusEnum.FAILED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_horse_details(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """경주마 상세정보(모마명·생년월일 등)를 KRA API(raceHorseInfo_2)에서 수집해 DB에 업데이트합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                items = await self.kra_api_service.fetch_horse_detail_list(
                    meet=self._meet_code_to_api_value(meet_code),
                )
                for item in items:
                    item["_meet_code"] = meet_code
                all_items.extend(items)

            records_collected, null_count, anomaly_count = await self._save_horse_detail_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="horse_details",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_details",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_details",
                status=CollectStatusEnum.FAILED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_jockey_results(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """기수 성적 정보(승률 직접 제공)를 KRA API(jockeyResult_1)에서 수집해 DB에 업데이트합니다."""
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                all_items.extend(
                    await self.kra_api_service.fetch_jockey_result_list(
                        meet=self._meet_code_to_api_value(meet_code),
                    )
                )

            records_collected, null_count, anomaly_count = await self._save_jockey_result_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="jockey_results",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="jockey_results",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="jockey_results",
                status=CollectStatusEnum.FAILED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_horse_total_info(
        self,
        meet_codes: list[str],
    ) -> CollectionSummary:
        """마필종합 상세정보(부마명·모색·영문마명)를 KRA API(totalHorseInfo_1)에서 수집해 DB에 업데이트합니다.

        raceHorseInfo_2에서 제공하지 않는 father_name(부마명)·color(모색)를 보완합니다.
        주간 마스터 동기화(매주 월요일)에서 호출합니다.
        """
        all_items: list[dict[str, Any]] = []

        try:
            for meet_code in meet_codes:
                items = await self.kra_api_service.fetch_total_horse_info_list(
                    meet=self._meet_code_to_api_value(meet_code),
                )
                # 경마장 코드를 각 아이템에 주입합니다 (API 응답의 meet 필드가 없는 경우 대비).
                for item in items:
                    item["_meet_code"] = meet_code
                all_items.extend(items)

            records_collected, null_count, anomaly_count = await self._save_horse_total_items(all_items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="horse_total_info",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                message=None if records_collected > 0 else "수집된 마필종합 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_total_info",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="horse_total_info",
                status=CollectStatusEnum.FAILED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_track_conditions(
        self,
        meet_code: str,
        rc_date: date,
    ) -> CollectionSummary:
        """경주로 상태(함수율·날씨·주로상태)를 KRA API(Track_1)에서 수집해 경주 레코드를 업데이트합니다."""
        try:
            items = await self.kra_api_service.fetch_track_conditions(
                meet=self._meet_code_to_api_value(meet_code),
                rc_date=rc_date.strftime("%Y%m%d"),
            )
            for item in items:
                item["_meet_code"] = meet_code
                item["_rc_date"] = rc_date

            records_collected, null_count, anomaly_count = await self._save_track_condition_items(items)
            await self.db.commit()

            summary = await self._build_summary(
                api_name="track_conditions",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                meet_code=meet_code,
                rc_date=rc_date,
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="track_conditions",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="track_conditions",
                status=CollectStatusEnum.FAILED,
                records_collected=0, null_count=0, anomaly_count=0,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_race_schedule(
        self,
        meet_codes: list[str],
        rc_year: int,
        rc_month: str,
    ) -> CollectionSummary:
        all_items: list[dict[str, Any]] = []
        total_anomaly_count = 0

        try:
            for meet_code in meet_codes:
                all_items.extend(
                    await self.kra_api_service.fetch_race_schedule(
                        meet=self._meet_code_to_api_value(meet_code),
                        rc_year=rc_year,
                        rc_month=rc_month,
                    )
                )

            records_collected, null_count, anomaly_count = await self._save_race_schedule_items(all_items)
            total_anomaly_count += anomaly_count
            await self.db.commit()

            summary = await self._build_summary(
                api_name="race_schedule",
                status=CollectStatusEnum.SUCCESS,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=total_anomaly_count,
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="race_schedule",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="race_schedule",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=total_anomaly_count,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_entry_info(
        self,
        meet_code: str,
        rc_date: date,
        rc_no: int | None = None,
    ) -> CollectionSummary:
        try:
            await self._ensure_schedule_exists_for_month(meet_code, rc_date)
            items = await self.kra_api_service.fetch_entry_info(
                meet=self._meet_code_to_api_value(meet_code),
                rc_date=rc_date.strftime("%Y%m%d"),
                rc_no=rc_no,
            )
            records_collected, null_count, anomaly_count = await self._save_entry_items(
                items=items,
                requested_meet_code=meet_code,
                requested_date=rc_date,
                requested_race_no=rc_no,
            )
            await self.db.commit()

            summary = await self._build_summary(
                api_name="entry_info",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                meet_code=meet_code,
                rc_date=rc_date,
                message=None if records_collected > 0 else "조건에 맞는 출전표 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="entry_info",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                meet_code=meet_code,
                rc_date=rc_date,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="entry_info",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                meet_code=meet_code,
                rc_date=rc_date,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def collect_race_results(
        self,
        meet_code: str,
        rc_date: date,
        rc_no: int | None = None,
    ) -> CollectionSummary:
        try:
            await self._ensure_schedule_exists_for_month(meet_code, rc_date)
            items = await self.kra_api_service.fetch_race_results(
                meet=self._meet_code_to_api_value(meet_code),
                rc_date=rc_date.strftime("%Y%m%d"),
                rc_no=rc_no,
            )
            records_collected, null_count, anomaly_count = await self._save_result_items(
                items=items,
                requested_meet_code=meet_code,
                requested_date=rc_date,
                requested_race_no=rc_no,
            )
            await self.db.commit()

            summary = await self._build_summary(
                api_name="race_results",
                status=CollectStatusEnum.SUCCESS if records_collected > 0 else CollectStatusEnum.PARTIAL,
                records_collected=records_collected,
                null_count=null_count,
                anomaly_count=anomaly_count,
                meet_code=meet_code,
                rc_date=rc_date,
                message=None if records_collected > 0 else "조건에 맞는 경주 결과 데이터가 없습니다.",
            )
        except KRARateLimitExceededError as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="race_results",
                status=CollectStatusEnum.SKIPPED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                meet_code=meet_code,
                rc_date=rc_date,
                message=str(error),
            )
        except Exception as error:
            await self.db.rollback()
            summary = await self._build_summary(
                api_name="race_results",
                status=CollectStatusEnum.FAILED,
                records_collected=0,
                null_count=0,
                anomaly_count=0,
                meet_code=meet_code,
                rc_date=rc_date,
                message=str(error),
            )

        await self._insert_collection_log(summary)
        await self.db.commit()
        return summary

    async def get_today_collection_status(self) -> dict[str, Any]:
        # 오늘 수집 현황 조회는 "요약 숫자 + 최근 로그 목록" 두 층으로 나누면
        # 운영자가 전체 상태와 세부 이력을 함께 보기 쉽습니다.
        today = date.today()
        today_start = datetime.combine(today, time.min)

        result = await self.db.execute(
            select(CollectionLog).where(CollectionLog.collected_at >= today_start).order_by(CollectionLog.collected_at.desc())
        )
        logs = result.scalars().all()

        return {
            "today": today.isoformat(),
            "daily_call_count": await self.kra_api_service.get_daily_call_count(today),
            "total_logs": len(logs),
            "success_count": sum(1 for log in logs if log.status == CollectStatusEnum.SUCCESS),
            "failed_count": sum(1 for log in logs if log.status == CollectStatusEnum.FAILED),
            "skipped_count": sum(1 for log in logs if log.status == CollectStatusEnum.SKIPPED),
            "recent_logs": [
                {
                    "apiName": log.api_name,
                    "meetCode": log.meet_code,
                    "rcDate": log.rc_date.isoformat() if log.rc_date else None,
                    "status": log.status.value,
                    "recordsCollected": log.records_collected,
                    "dailyCallCount": log.daily_call_count,
                    "qualityStatus": log.quality_status.value if log.quality_status else None,
                    "collectedAt": log.collected_at.isoformat(),
                    "errorMessage": log.error_message,
                }
                for log in logs[:20]
            ],
        }

    async def _save_master_jockey_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: currentjockeyInfo/getcurrentjockeyinfo (data.go.kr 15086329)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            license_no = self._safe_text(item.get("jkNo"))
            name = self._safe_text(item.get("jkName"))
            meet_code = self._normalize_meet_code(item.get("meet"))

            if not name or not license_no or not meet_code:
                anomaly_count += 1
                continue

            # 승률: ord1CntT/rcCntT (API 직접 제공값 없음, 횟수에서 계산)
            win_rate_total = self._calc_rate(item.get("ord1CntT"), item.get("rcCntT"))
            win_rate_recent = self._calc_rate(item.get("ord1CntY"), item.get("rcCntY"))
            # 연대율 = (1착+2착+3착) / 총출주 (직접 계산)
            place_rate_total = self._calc_place_rate(
                item.get("ord1CntT"), item.get("ord2CntT"), item.get("ord3CntT"), item.get("rcCntT")
            )

            # birthday, debut 모두 YYYYMMDD 형식 (앞 4자리가 연도)
            birth_year = self._parse_year_from_date8(item.get("birthday"))
            debut_year = self._parse_year_from_date8(item.get("debut"))

            payload = {
                "name": name,
                "eng_name": None,  # 현직기수정보 API에는 영문명 필드 없음
                "meet_code": meet_code,
                "license_no": license_no,
                "birth_year": birth_year,
                "debut_year": debut_year,
                "affiliation": self._safe_text(item.get("part")),
                "photo_url": None,
                "win_rate_total": self._safe_decimal(win_rate_total),
                "win_rate_recent": self._safe_decimal(win_rate_recent),
                "place_rate_total": self._safe_decimal(place_rate_total),
                "is_active": True,
                "updated_at": datetime.now(),
            }

            null_count += self._count_null_values(
                payload, ignore_keys={"updated_at", "is_active", "eng_name", "photo_url"}
            )

            await self.db.execute(
                insert(Jockey)
                .values(name=name, created_at=datetime.now(), **payload)
                .on_conflict_do_update(
                    index_elements=["license_no", "meet_code"],
                    set_={k: v for k, v in payload.items() if k not in ("name", "meet_code", "license_no")},
                )
            )
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_master_trainer_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API308/trainerInfo (data.go.kr 15130588 — 조교사정보_영문추가)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            license_no = self._safe_text(item.get("trNo"))
            name = self._safe_text(item.get("trName"))
            meet_code = self._normalize_meet_code(item.get("meet"))

            if not name or not license_no or not meet_code:
                anomaly_count += 1
                continue

            # winRateT/winRateY 는 % 단위로 제공됩니다 (예: 15.30 = 15.30%)
            # DB는 0~1 소수 형식이므로 100으로 나눕니다.
            win_rate_total = self._pct_to_decimal(item.get("winRateT"))
            win_rate_recent = self._pct_to_decimal(item.get("winRateY"))

            # stDate: 데뷔일자 (YYYYMMDD 또는 YYYY 형식 모두 처리)
            debut_year = self._parse_year_from_date8(item.get("stDate"))
            # birthday: 생년월일 (trainerInfo_1 에서 제공, YYYYMMDD)
            birth_year = self._parse_year_from_date8(item.get("birthday"))

            payload = {
                "name": name,
                "eng_name": self._safe_text(item.get("trNameEn")),
                "meet_code": meet_code,
                "license_no": license_no,
                "birth_year": birth_year,
                "debut_year": debut_year,
                "affiliation": self._safe_text(item.get("part")),
                "photo_url": None,
                "win_rate_total": win_rate_total,
                "win_rate_recent": win_rate_recent,
                "is_active": True,
                "updated_at": datetime.now(),
            }

            null_count += self._count_null_values(
                payload, ignore_keys={"updated_at", "is_active", "photo_url"}
            )

            await self.db.execute(
                insert(Trainer)
                .values(name=name, created_at=datetime.now(), **payload)
                .on_conflict_do_update(
                    index_elements=["license_no", "meet_code"],
                    set_={k: v for k, v in payload.items() if k not in ("name", "meet_code", "license_no")},
                )
            )
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_master_horse_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: racehorselist/getracehorselist (data.go.kr 15089503 — 경주마명단)
        # 주의: 부마명/모마명은 이 API에서 제공되지 않습니다.
        # 주의: nameSp = 소속조(예: "40조"), 영문마명이 아닙니다.
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            name = self._safe_text(item.get("hrName"))
            # 경마장 코드: API 응답의 meet 필드 우선, 없으면 주입된 _meet_code 사용합니다.
            meet_code = self._normalize_meet_code(item.get("meet")) or item.get("_meet_code")

            if not name or not meet_code:
                anomaly_count += 1
                continue

            updates = {
                # nameSp 는 소속조 이름이므로 eng_name에 쓰지 않습니다.
                # 영문마명은 경주성적·경주기록 API(hrNameEn)에서 별도 수집됩니다.
                "sex": self._safe_text(item.get("sex")),
                "origin": self._safe_text(item.get("prdCty")),    # 생산국
                "meet_code": meet_code,
                "rating_1": self._safe_decimal(item.get("rating1")),
                "rating_2": self._safe_decimal(item.get("rating2")),
                "rating_3": self._safe_decimal(item.get("rating3")),
                "rating_4": self._safe_decimal(item.get("rating4")),
                "is_active": True,
            }

            null_count += self._count_null_values(
                updates, ignore_keys={"is_active"}
            )

            # horses 테이블에는 (name) 단독 유니크 제약이 없어 get-then-update 패턴을 사용합니다.
            horse = await self.db.scalar(
                select(Horse).where(Horse.name == name).order_by((Horse.meet_code == meet_code).desc())
            )

            if horse is None:
                horse = Horse(name=name, created_at=datetime.now(), updated_at=datetime.now(), **updates)
                self.db.add(horse)
            else:
                for key, value in updates.items():
                    if value is not None:
                        setattr(horse, key, value)
                horse.updated_at = datetime.now()

            await self.db.flush()
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_horse_result_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API15_2/raceHorseResult_2 — 경주마 성적 정보 (통산/최근1년 승률·복승률)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            name = self._safe_text(item.get("hrName"))
            meet_code = self._normalize_meet_code(item.get("meet")) or item.get("_meet_code")

            if not name or not meet_code:
                anomaly_count += 1
                continue

            # winRateT/winRateY/plcRateT 모두 % 단위 → 0~1 소수로 변환
            updates = {
                "win_rate_total": self._pct_to_decimal(item.get("winRateT")),
                "win_rate_recent": self._pct_to_decimal(item.get("winRateY")),
                "place_rate_total": self._pct_to_decimal(item.get("plcRateT")),
                "debut_year": self._parse_year_from_date8(item.get("debut")),
                "meet_code": meet_code,
                "is_active": True,
            }

            null_count += self._count_null_values(updates, ignore_keys={"is_active", "meet_code"})

            horse = await self.db.scalar(
                select(Horse).where(Horse.name == name).order_by((Horse.meet_code == meet_code).desc())
            )
            if horse is None:
                horse = Horse(name=name, created_at=datetime.now(), updated_at=datetime.now(), **updates)
                self.db.add(horse)
            else:
                for key, value in updates.items():
                    if value is not None:
                        setattr(horse, key, value)
                horse.updated_at = datetime.now()

            await self.db.flush()
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_horse_detail_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API8_2/raceHorseInfo_2 — 경주마 상세정보 (모마명·생년월일 포함)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            name = self._safe_text(item.get("hrName"))
            meet_code = self._normalize_meet_code(item.get("meet")) or item.get("_meet_code")

            if not name or not meet_code:
                anomaly_count += 1
                continue

            # 모마명 필드명: API 버전에 따라 motherName 또는 mName으로 다를 수 있음
            mother_name = (
                self._safe_text(item.get("motherName"))
                or self._safe_text(item.get("mName"))
            )

            updates = {
                "sex": self._safe_text(item.get("sex")),
                "origin": self._safe_text(item.get("prdCty")),
                "birth_year": self._parse_year_from_date8(item.get("birthday")),
                "mother_name": mother_name,
                "meet_code": meet_code,
                "is_active": True,
            }

            null_count += self._count_null_values(updates, ignore_keys={"is_active", "meet_code"})

            horse = await self.db.scalar(
                select(Horse).where(Horse.name == name).order_by((Horse.meet_code == meet_code).desc())
            )
            if horse is None:
                horse = Horse(name=name, created_at=datetime.now(), updated_at=datetime.now(), **updates)
                self.db.add(horse)
            else:
                for key, value in updates.items():
                    if value is not None:
                        setattr(horse, key, value)
                horse.updated_at = datetime.now()

            await self.db.flush()
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_jockey_result_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API11_1/jockeyResult_1 — 기수 성적 정보 (승률 직접 제공, % 단위)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            license_no = self._safe_text(item.get("jkNo"))
            name = self._safe_text(item.get("jkName"))
            meet_code = self._normalize_meet_code(item.get("meet"))

            if not name or not license_no or not meet_code:
                anomaly_count += 1
                continue

            payload = {
                "win_rate_total": self._pct_to_decimal(item.get("winRateT")),
                "win_rate_recent": self._pct_to_decimal(item.get("winRateY")),
                "place_rate_total": self._pct_to_decimal(item.get("plcRateT")),
                "updated_at": datetime.now(),
            }

            null_count += self._count_null_values(payload, ignore_keys={"updated_at"})

            await self.db.execute(
                insert(Jockey)
                .values(
                    name=name,
                    meet_code=meet_code,
                    license_no=license_no,
                    created_at=datetime.now(),
                    **payload,
                )
                .on_conflict_do_update(
                    index_elements=["license_no", "meet_code"],
                    set_={k: v for k, v in payload.items()},
                )
            )
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_horse_total_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API42/totalHorseInfo_1 — 마필종합 상세정보
        # raceHorseInfo_2에 없는 father_name(부마명)·color(모색)·eng_name 보완 전용입니다.
        # 이미 DB에 있는 말의 부가 정보만 채우고, 새 말을 추가하지 않습니다.
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            name = self._safe_text(item.get("hrName"))
            meet_code = self._normalize_meet_code(item.get("meet")) or item.get("_meet_code")

            if not name or not meet_code:
                anomaly_count += 1
                continue

            # None이 아닌 필드만 setattr로 업데이트해 기존 값을 덮어쓰지 않습니다.
            updates = {
                "eng_name":    self._safe_text(item.get("hrEngName")),
                "father_name": self._safe_text(item.get("faName")),
                "mother_name": self._safe_text(item.get("moName")),
                "color":       self._safe_text(item.get("color")),
            }

            null_count += self._count_null_values(updates)

            horse = await self.db.scalar(
                select(Horse).where(Horse.name == name).order_by((Horse.meet_code == meet_code).desc())
            )
            if horse is None:
                # 마필종합 API에만 있고 명단에 없는 말은 새로 추가하지 않습니다.
                # 이 함수의 목적은 기존 말의 혈통 정보 보완이므로 anomaly로만 기록합니다.
                anomaly_count += 1
                continue

            for key, value in updates.items():
                if value is not None:
                    setattr(horse, key, value)
            horse.updated_at = datetime.now()
            await self.db.flush()
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_track_condition_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        # API: API189_1/Track_1 — 경주로 정보 (함수율·날씨·경주로상태)
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            meet_code = self._normalize_meet_code(item.get("meet")) or item.get("_meet_code")
            rc_date = self._parse_compact_date(item.get("rcDate")) or item.get("_rc_date")
            race_no = self._safe_int(item.get("rcNo"))

            if not meet_code or rc_date is None or race_no is None:
                anomaly_count += 1
                continue

            race = await self._get_race(meet_code, rc_date, race_no)
            if race is None:
                anomaly_count += 1
                continue

            moisture = self._safe_decimal(item.get("moistContent"))
            weather = self._safe_text(item.get("weather"))
            track_cond = self._parse_track_condition(item.get("budrCondition"))

            null_count += sum(1 for v in (moisture, weather, track_cond) if v is None)

            if moisture is not None:
                race.moisture_level = moisture
            if weather is not None:
                race.weather = weather
            if track_cond is not None:
                race.track_condition = track_cond
            race.updated_at = datetime.now()
            await self.db.flush()
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_race_schedule_items(self, items: list[dict[str, Any]]) -> tuple[int, int, int]:
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            meet_code = self._normalize_meet_code(item.get("meet"))
            rc_date = self._parse_compact_date(item.get("rcDate"))
            race_no = self._safe_int(item.get("rcNo"))

            if meet_code is None or rc_date is None or race_no is None:
                anomaly_count += 1
                continue

            payload = {
                "meet_code": meet_code,
                "rc_date": rc_date,
                "race_no": race_no,
                "race_name": self._safe_text(item.get("rcName")),
                "distance": self._safe_int(item.get("rcDist")),
                "prize_money": self._safe_int(item.get("chaksun1")),
                "start_time": self._parse_compact_time(item.get("schStTime")),
                "status": RaceStatusEnum.SCHEDULED,
                "race_class": self._safe_text(item.get("rank")),
                "race_grade": self._parse_race_grade(item.get("rcName")),
                "updated_at": datetime.now(),
            }

            null_count += self._count_null_values(payload, ignore_keys={"updated_at", "status"})

            await self.db.execute(
                insert(Race)
                .values(**payload)
                .on_conflict_do_update(
                    index_elements=["meet_code", "rc_date", "race_no"],
                    set_={
                        "race_name": payload["race_name"],
                        "distance": payload["distance"],
                        "prize_money": payload["prize_money"],
                        "start_time": payload["start_time"],
                        "race_class": payload["race_class"],
                        "race_grade": payload["race_grade"],
                        "updated_at": payload["updated_at"],
                    },
                )
            )
            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_entry_items(
        self,
        items: list[dict[str, Any]],
        requested_meet_code: str,
        requested_date: date,
        requested_race_no: int | None,
    ) -> tuple[int, int, int]:
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            item_meet_code = self._normalize_meet_code(item.get("meet")) or requested_meet_code
            item_date = self._parse_compact_date(item.get("rcDate")) or requested_date
            item_race_no = self._safe_int(item.get("rcNo"))

            if item_meet_code != requested_meet_code or item_date != requested_date:
                continue

            if requested_race_no is not None and item_race_no != requested_race_no:
                continue

            if item_race_no is None:
                anomaly_count += 1
                continue

            race = await self._get_race(item_meet_code, item_date, item_race_no)
            if race is None:
                anomaly_count += 1
                continue

            horse = await self._get_or_create_horse_from_entry(item, item_meet_code)
            jockey = await self._get_or_create_jockey_from_entry(item, item_meet_code)
            trainer = await self._get_or_create_trainer_from_entry(item, item_meet_code)

            gate_no = self._safe_int(item.get("chulNo"))
            total_run_count = self._safe_int(item.get("rcCntT"))
            rest_days = self._safe_int(item.get("ilsu"))
            is_comeback = rest_days is not None and rest_days >= 120

            payload = {
                "race_id": race.id,
                "horse_id": horse.id,
                "jockey_id": jockey.id if jockey else None,
                "trainer_id": trainer.id if trainer else None,
                "gate_no": gate_no,
                "burden_weight": self._safe_decimal(item.get("wgBudam")),
                "rating": self._safe_decimal(item.get("rating")),
                "data_status": DataStatusEnum.COLLECTED,
                "last_updated": datetime.now(),
                "is_debut": total_run_count == 0 if total_run_count is not None else False,
                "is_comeback": is_comeback,
                "rest_days": rest_days,
                "class_change": ClassChangeEnum.SAME,
                "distance_change": DistanceChangeEnum.SAME,
            }

            null_count += self._count_null_values(payload, ignore_keys={"data_status", "last_updated", "class_change", "distance_change", "is_debut", "is_comeback"})

            existing_entry = await self.db.scalar(
                select(RaceEntry).where(
                    RaceEntry.race_id == race.id,
                    RaceEntry.horse_id == horse.id,
                )
            )

            if existing_entry is None:
                existing_entry = RaceEntry(
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    **payload,
                )
                self.db.add(existing_entry)
            else:
                for key, value in payload.items():
                    setattr(existing_entry, key, value)
                existing_entry.updated_at = datetime.now()

            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _save_result_items(
        self,
        items: list[dict[str, Any]],
        requested_meet_code: str,
        requested_date: date,
        requested_race_no: int | None,
    ) -> tuple[int, int, int]:
        records_collected = 0
        null_count = 0
        anomaly_count = 0

        for item in items:
            item_meet_code = self._normalize_meet_code(item.get("meet")) or requested_meet_code
            item_date = self._parse_compact_date(item.get("rcDate")) or requested_date
            item_race_no = self._safe_int(item.get("rcNo"))

            if item_meet_code != requested_meet_code or item_date != requested_date:
                continue

            if requested_race_no is not None and item_race_no != requested_race_no:
                continue

            if item_race_no is None:
                anomaly_count += 1
                continue

            race = await self._get_race(item_meet_code, item_date, item_race_no)
            if race is None:
                anomaly_count += 1
                continue

            horse = await self._get_or_create_horse_from_result(item, item_meet_code)
            jockey = await self._get_or_create_jockey_from_result(item, item_meet_code)
            trainer = await self._get_or_create_trainer_from_result(item, item_meet_code)

            race_entry = await self._get_or_create_entry_for_result(
                race=race,
                horse=horse,
                jockey=jockey,
                trainer=trainer,
                item=item,
            )

            await self._update_race_from_result_item(race, item)

            payload = {
                "race_id": race.id,
                "horse_id": horse.id,
                "race_entry_id": race_entry.id if race_entry else None,
                "rank": self._safe_int(item.get("ord")),
                "record_time": self._safe_text(item.get("rcTime")),
                "margin": self._safe_text(item.get("diffUnit")),
                "section_1": self._safe_text(item.get("seS1fAccTime")),
                "section_2": self._safe_text(item.get("se_3cAccTime")),
                "section_3": self._safe_text(item.get("se_4cAccTime")),
                "section_4": self._safe_text(item.get("seG3fAccTime")),
                "section_5": self._safe_text(item.get("seG1fAccTime")),
                "section_6": self._safe_text(item.get("track")),
            }

            null_count += self._count_null_values(payload, ignore_keys={"race_entry_id"})

            await self.db.execute(
                insert(RaceResult)
                .values(**payload)
                .on_conflict_do_update(
                    index_elements=["race_id", "horse_id"],
                    set_={
                        "race_entry_id": payload["race_entry_id"],
                        "rank": payload["rank"],
                        "record_time": payload["record_time"],
                        "margin": payload["margin"],
                        "section_1": payload["section_1"],
                        "section_2": payload["section_2"],
                        "section_3": payload["section_3"],
                        "section_4": payload["section_4"],
                        "section_5": payload["section_5"],
                        "section_6": payload["section_6"],
                    },
                )
            )

            records_collected += 1

        return records_collected, null_count, anomaly_count

    async def _get_race(self, meet_code: str, rc_date: date, race_no: int) -> Race | None:
        return await self.db.scalar(
            select(Race).where(
                Race.meet_code == meet_code,
                Race.rc_date == rc_date,
                Race.race_no == race_no,
            )
        )

    async def _ensure_schedule_exists_for_month(self, meet_code: str, rc_date: date) -> None:
        # 출전표/결과는 race_id 외래키가 필요하므로,
        # 해당 월 경주 스케줄이 비어 있으면 먼저 schedule 수집을 실행해 기반 row를 보장합니다.
        exists = await self.db.scalar(
            select(func.count()).select_from(Race).where(
                Race.meet_code == meet_code,
                func.date_trunc("month", Race.rc_date) == rc_date.replace(day=1),
            )
        )

        if not exists:
            await self.collect_race_schedule(
                meet_codes=[meet_code],
                rc_year=rc_date.year,
                rc_month=rc_date.strftime("%Y%m"),
            )

    async def _get_or_create_horse_from_entry(self, item: dict[str, Any], meet_code: str) -> Horse:
        defaults = {
            "eng_name": self._safe_text(item.get("hrNameEn")),
            "sex": self._safe_text(item.get("sex")),
            "origin": self._safe_text(item.get("prd")),
            "owner": self._safe_text(item.get("owName")),
            "meet_code": meet_code,
            "rating_1": self._safe_decimal(item.get("rating")),
            "is_active": True,
        }
        return await self._get_or_create_horse(self._safe_text(item.get("hrName")) or "이름없음", meet_code, defaults)

    async def _get_or_create_horse_from_result(self, item: dict[str, Any], meet_code: str) -> Horse:
        birthday = self._safe_int(item.get("birthday"))
        defaults = {
            "sex": self._safe_text(item.get("sex")),
            "origin": self._safe_text(item.get("name")),
            "owner": self._safe_text(item.get("owName")),
            "meet_code": meet_code,
            "rating_1": self._safe_decimal(item.get("rating")),
            "birth_year": int(str(birthday)[:4]) if birthday else None,
            "is_active": True,
        }
        return await self._get_or_create_horse(self._safe_text(item.get("hrName")) or "이름없음", meet_code, defaults)

    async def _get_or_create_horse(self, name: str, meet_code: str, defaults: dict[str, Any]) -> Horse:
        horse = await self.db.scalar(
            select(Horse).where(Horse.name == name).order_by((Horse.meet_code == meet_code).desc())
        )

        if horse is None:
            horse = Horse(name=name, created_at=datetime.now(), updated_at=datetime.now(), **defaults)
            self.db.add(horse)
            await self.db.flush()
            return horse

        for key, value in defaults.items():
            if value is not None:
                setattr(horse, key, value)
        horse.updated_at = datetime.now()
        await self.db.flush()
        return horse

    async def _get_or_create_jockey_from_entry(self, item: dict[str, Any], meet_code: str) -> Jockey | None:
        jockey_name = self._safe_text(item.get("jkName"))
        if jockey_name is None:
            return None

        defaults = {
            "eng_name": self._safe_text(item.get("jkNameEn")),
            "meet_code": meet_code,
            "license_no": self._safe_text(item.get("jkNo")),
            "is_active": True,
        }
        return await self._get_or_create_jockey(jockey_name, defaults)

    async def _get_or_create_jockey_from_result(self, item: dict[str, Any], meet_code: str) -> Jockey | None:
        jockey_name = self._safe_text(item.get("jkName"))
        if jockey_name is None:
            return None

        defaults = {
            "meet_code": meet_code,
            "license_no": self._safe_text(item.get("jkNo")),
            "is_active": True,
        }
        return await self._get_or_create_jockey(jockey_name, defaults)

    async def _get_or_create_jockey(self, name: str, defaults: dict[str, Any]) -> Jockey:
        license_no = defaults.get("license_no")
        meet_code = defaults.get("meet_code")
        statement = select(Jockey)

        # license_no + meet_code 둘 다 있으면 함께 검색합니다.
        # license_no만으로 검색하면 다른 meet_code의 동명 기수 row를 잡아 meet_code 업데이트 시
        # UNIQUE(license_no, meet_code) 제약 위반이 발생합니다.
        if license_no and meet_code:
            statement = statement.where(Jockey.license_no == license_no, Jockey.meet_code == meet_code)
        elif license_no:
            statement = statement.where(Jockey.license_no == license_no)
        else:
            statement = statement.where(Jockey.name == name)

        jockey = await self.db.scalar(statement)

        if jockey is None:
            jockey = Jockey(name=name, created_at=datetime.now(), updated_at=datetime.now(), **defaults)
            self.db.add(jockey)
            await self.db.flush()
            return jockey

        for key, value in defaults.items():
            if value is not None:
                setattr(jockey, key, value)
        jockey.updated_at = datetime.now()
        await self.db.flush()
        return jockey

    async def _get_or_create_trainer_from_entry(self, item: dict[str, Any], meet_code: str) -> Trainer | None:
        trainer_name = self._safe_text(item.get("trName"))
        if trainer_name is None:
            return None

        defaults = {
            "eng_name": self._safe_text(item.get("trNameEn")),
            "meet_code": meet_code,
            "license_no": self._safe_text(item.get("trNo")),
            "is_active": True,
        }
        return await self._get_or_create_trainer(trainer_name, defaults)

    async def _get_or_create_trainer_from_result(self, item: dict[str, Any], meet_code: str) -> Trainer | None:
        trainer_name = self._safe_text(item.get("trName"))
        if trainer_name is None:
            return None

        defaults = {
            "meet_code": meet_code,
            "license_no": self._safe_text(item.get("trNo")),
            "is_active": True,
        }
        return await self._get_or_create_trainer(trainer_name, defaults)

    async def _get_or_create_trainer(self, name: str, defaults: dict[str, Any]) -> Trainer:
        license_no = defaults.get("license_no")
        meet_code = defaults.get("meet_code")
        statement = select(Trainer)

        # Jockey와 동일한 이유로 license_no + meet_code 함께 검색합니다.
        # UNIQUE(license_no, meet_code) 제약 위반 방지.
        if license_no and meet_code:
            statement = statement.where(Trainer.license_no == license_no, Trainer.meet_code == meet_code)
        elif license_no:
            statement = statement.where(Trainer.license_no == license_no)
        else:
            statement = statement.where(Trainer.name == name)

        trainer = await self.db.scalar(statement)

        if trainer is None:
            trainer = Trainer(name=name, created_at=datetime.now(), updated_at=datetime.now(), **defaults)
            self.db.add(trainer)
            await self.db.flush()
            return trainer

        for key, value in defaults.items():
            if value is not None:
                setattr(trainer, key, value)
        trainer.updated_at = datetime.now()
        await self.db.flush()
        return trainer

    async def _get_or_create_entry_for_result(
        self,
        race: Race,
        horse: Horse,
        jockey: Jockey | None,
        trainer: Trainer | None,
        item: dict[str, Any],
    ) -> RaceEntry:
        race_entry = await self.db.scalar(
            select(RaceEntry).where(
                RaceEntry.race_id == race.id,
                RaceEntry.horse_id == horse.id,
            )
        )

        payload = {
            "race_id": race.id,
            "horse_id": horse.id,
            "jockey_id": jockey.id if jockey else None,
            "trainer_id": trainer.id if trainer else None,
            "gate_no": self._safe_int(item.get("chulNo")),
            "burden_weight": self._safe_decimal(item.get("wgBudam")),
            "horse_weight": self._parse_horse_weight(item.get("wgHr")),
            "horse_weight_diff": self._parse_horse_weight_diff(item.get("wgHr")),
            "rating": self._safe_decimal(item.get("rating")),
            "odds_win": self._safe_decimal(item.get("winOdds")),
            "odds_place": self._safe_decimal(item.get("plcOdds")),
            "data_status": DataStatusEnum.COLLECTED,
            "last_updated": datetime.now(),
            "class_change": ClassChangeEnum.SAME,
            "distance_change": DistanceChangeEnum.SAME,
            "is_debut": False,
            "is_comeback": False,
        }

        if race_entry is None:
            race_entry = RaceEntry(created_at=datetime.now(), updated_at=datetime.now(), **payload)
            self.db.add(race_entry)
            await self.db.flush()
            return race_entry

        for key, value in payload.items():
            setattr(race_entry, key, value)
        race_entry.updated_at = datetime.now()
        await self.db.flush()
        return race_entry

    async def _update_race_from_result_item(self, race: Race, item: dict[str, Any]) -> None:
        race.status = RaceStatusEnum.COMPLETED
        race.weather = self._safe_text(item.get("weather"))
        race.track_condition = self._parse_track_condition(item.get("track"))
        race.start_time = race.start_time or self._parse_start_time_text(item.get("stTime"))
        race.updated_at = datetime.now()
        await self.db.flush()

    async def _build_summary(
        self,
        api_name: str,
        status: CollectStatusEnum,
        records_collected: int,
        null_count: int,
        anomaly_count: int,
        meet_code: str | None = None,
        rc_date: date | None = None,
        message: str | None = None,
    ) -> CollectionSummary:
        daily_call_count = await self.kra_api_service.get_daily_call_count()
        quality_score = self._calculate_quality_score(records_collected, null_count, anomaly_count)
        quality_status = self._determine_quality_status(quality_score)

        return CollectionSummary(
            api_name=api_name,
            status=status.value,
            records_collected=records_collected,
            daily_call_count=daily_call_count,
            null_count=null_count,
            anomaly_count=anomaly_count,
            quality_score=quality_score,
            quality_status=quality_status.value if quality_status else None,
            meet_code=meet_code,
            rc_date=rc_date,
            message=message,
        )

    async def _insert_collection_log(self, summary: CollectionSummary) -> None:
        log = CollectionLog(
            api_name=summary.api_name,
            meet_code=summary.meet_code,
            rc_date=summary.rc_date,
            status=CollectStatusEnum(summary.status),
            records_collected=summary.records_collected,
            error_message=summary.message,
            daily_call_count=summary.daily_call_count,
            null_count=summary.null_count,
            anomaly_count=summary.anomaly_count,
            quality_score=summary.quality_score,
            quality_status=QualityStatusEnum(summary.quality_status) if summary.quality_status else None,
            collected_at=datetime.now(),
        )
        self.db.add(log)

    def _calculate_quality_score(self, records_collected: int, null_count: int, anomaly_count: int) -> Decimal:
        if records_collected <= 0:
            return Decimal("0.00")

        penalty = Decimal(null_count * 0.4 + anomaly_count * 5)
        raw_score = Decimal("100.00") - penalty
        return max(Decimal("0.00"), raw_score.quantize(Decimal("0.01")))

    def _determine_quality_status(self, quality_score: Decimal) -> QualityStatusEnum:
        if quality_score >= Decimal("85"):
            return QualityStatusEnum.GOOD
        if quality_score >= Decimal("60"):
            return QualityStatusEnum.WARNING
        return QualityStatusEnum.CRITICAL

    @staticmethod
    def _meet_code_to_api_value(meet_code: str) -> int:
        mapping = {"SC": 1, "JJ": 2, "BU": 3}
        return mapping[meet_code]

    @staticmethod
    def _normalize_meet_code(meet_value: Any) -> str | None:
        mapping = {
            1: "SC",
            2: "JJ",
            3: "BU",
            "1": "SC",
            "2": "JJ",
            "3": "BU",
            "서울": "SC",
            "제주": "JJ",
            "부산": "BU",
            "부경": "BU",
            "부산경남": "BU",
            "SC": "SC",
            "JJ": "JJ",
            "BU": "BU",
        }
        return mapping.get(meet_value)

    @staticmethod
    def _parse_compact_date(raw_value: Any) -> date | None:
        if raw_value in (None, ""):
            return None
        return datetime.strptime(str(raw_value), "%Y%m%d").date()

    @staticmethod
    def _parse_compact_time(raw_value: Any) -> time | None:
        if raw_value in (None, ""):
            return None

        raw_text = str(raw_value).zfill(4)
        return time(hour=int(raw_text[:2]), minute=int(raw_text[2:4]))

    @staticmethod
    def _parse_start_time_text(raw_value: Any) -> time | None:
        if raw_value in (None, ""):
            return None

        text_value = str(raw_value).replace("출발", "").replace(":", "").strip()
        digits = "".join(character for character in text_value if character.isdigit()).zfill(4)
        return time(hour=int(digits[:2]), minute=int(digits[2:4]))

    @staticmethod
    def _parse_track_condition(raw_value: Any) -> TrackConditionEnum | None:
        if raw_value in (None, ""):
            return None

        text_value = str(raw_value)

        if "포화" in text_value:
            return TrackConditionEnum.SATURATED
        if "다습" in text_value:
            return TrackConditionEnum.HUMID
        if "불량" in text_value:
            return TrackConditionEnum.WET
        if "양호" in text_value or "건조" in text_value:
            return TrackConditionEnum.DRY

        return None

    @staticmethod
    def _parse_race_grade(raw_value: Any) -> RaceGradeEnum | None:
        if raw_value in (None, ""):
            return None

        try:
            return RaceGradeEnum(str(raw_value))
        except ValueError:
            return None

    @staticmethod
    def _parse_horse_weight(raw_value: Any) -> int | None:
        if raw_value in (None, ""):
            return None

        text_value = str(raw_value)
        if "(" in text_value:
            text_value = text_value.split("(", maxsplit=1)[0]

        digits = "".join(character for character in text_value if character.isdigit())
        return int(digits) if digits else None

    @staticmethod
    def _parse_horse_weight_diff(raw_value: Any) -> int | None:
        if raw_value in (None, "") or "(" not in str(raw_value):
            return None

        text_value = str(raw_value)
        inside = text_value[text_value.find("(") + 1:text_value.find(")")]

        if not inside:
            return None

        try:
            return int(inside)
        except ValueError:
            return None

    @staticmethod
    def _safe_int(raw_value: Any) -> int | None:
        if raw_value in (None, "", "-"):
            return None

        try:
            return int(Decimal(str(raw_value)))
        except Exception:
            return None

    @staticmethod
    def _safe_decimal(raw_value: Any) -> Decimal | None:
        if raw_value in (None, "", "-"):
            return None

        try:
            return Decimal(str(raw_value))
        except Exception:
            return None

    @staticmethod
    def _safe_text(raw_value: Any) -> str | None:
        if raw_value is None:
            return None

        text_value = str(raw_value).strip()
        return text_value if text_value else None

    @staticmethod
    def _calc_rate(win_count: Any, total_count: Any) -> str | None:
        """승수/출전수로 승률(0~1)을 계산합니다. 유효하지 않으면 None을 반환합니다."""
        try:
            wins = int(Decimal(str(win_count)))
            total = int(Decimal(str(total_count)))
            if total <= 0:
                return None
            return str(round(wins / total, 4))
        except Exception:
            return None

    @staticmethod
    def _calc_place_rate(cnt1: Any, cnt2: Any, cnt3: Any, total: Any) -> str | None:
        """(1착+2착+3착)/총출주로 연대율(0~1)을 계산합니다."""
        try:
            placed = int(Decimal(str(cnt1 or 0))) + int(Decimal(str(cnt2 or 0))) + int(Decimal(str(cnt3 or 0)))
            total_cnt = int(Decimal(str(total)))
            if total_cnt <= 0:
                return None
            return str(round(placed / total_cnt, 4))
        except Exception:
            return None

    @staticmethod
    def _pct_to_decimal(raw_value: Any) -> Decimal | None:
        """API가 % 단위로 내려보내는 승률값을 0~1 소수로 변환합니다 (예: 15.3 → 0.1530)."""
        if raw_value in (None, "", "-"):
            return None
        try:
            pct = Decimal(str(raw_value))
            return (pct / 100).quantize(Decimal("0.0001"))
        except Exception:
            return None

    @staticmethod
    def _parse_year_from_date8(raw_value: Any) -> int | None:
        """YYYYMMDD 또는 YYYY 형식에서 연도(int)를 추출합니다."""
        if raw_value in (None, "", "-", "0", 0):
            return None
        text = str(raw_value).strip()
        if len(text) >= 4 and text[:4].isdigit():
            year = int(text[:4])
            return year if 1900 <= year <= 2100 else None
        return None

    @staticmethod
    def _count_null_values(payload: dict[str, Any], ignore_keys: set[str] | None = None) -> int:
        ignore_keys = ignore_keys or set()
        return sum(1 for key, value in payload.items() if key not in ignore_keys and value is None)
