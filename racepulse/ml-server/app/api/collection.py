# -*- coding: utf-8 -*-
# =============================================================================
# collection.py — 수동 수집 테스트 및 상태 조회 API
# =============================================================================
# 자동 스케줄이 있어도 초기 개발 단계에서는 "지금 바로 한 번 돌려보기"가 꼭 필요합니다.
# 그래서 POST /collection/test 로 수동 실행, GET /collection/status 로 오늘 현황 조회를 제공합니다.
# =============================================================================

# date = 수집 대상 경주일자를 받기 위한 타입입니다.
from datetime import date
# Literal = 요청 body에서 허용하는 collection_type 문자열 후보를 제한하는 타입입니다.
from typing import Literal

# APIRouter = 관련 API들을 하나의 라우터 묶음으로 관리하는 FastAPI 도구입니다.
from fastapi import APIRouter, Depends, HTTPException
# BaseModel/Field = 요청 body 형식을 문서화하고 검증하는 Pydantic 도구입니다.
from pydantic import BaseModel, Field
# AsyncSession = DB 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# get_db = 요청마다 비동기 DB 세션을 안전하게 빌려주는 의존성 함수입니다.
from app.core.database import get_db
# DataService = 수집 결과 저장과 collection_logs 기록을 담당하는 서비스입니다.
from app.services.data_service import DataService
# KRAApiError/KRAApiService = 실제 KRA API 호출과 호출 오류 관리를 담당합니다.
from app.services.kra_api import KRAApiError, KRAApiService
# WeatherApiService = 기상청 API 호출 및 날씨 데이터 저장을 담당하는 서비스입니다.
from app.services.weather_api import WeatherApiService

router = APIRouter(prefix="/collection")


class CollectionTestRequest(BaseModel):
    # collection_type = 어떤 수집을 수동 실행할지 고르는 값입니다.
    collection_type: Literal["schedule", "entry", "results"] = Field(
        default="schedule",
        description="수집 유형: schedule / entry / results",
    )
    # meet_code는 프론트/백엔드에서 공통으로 쓰는 SC/JJ/BU 형식을 사용합니다.
    meet_code: Literal["SC", "JJ", "BU"] | None = Field(
        default=None,
        description="경마장 코드: SC(서울), JJ(제주), BU(부산경남)",
    )
    target_date: date | None = Field(
        default=None,
        description="대상 경주일자. 미입력 시 오늘 날짜를 사용합니다.",
    )
    race_no: int | None = Field(
        default=None,
        ge=1,
        description="특정 경주 번호만 수집하고 싶을 때 사용합니다.",
    )
    rc_year: int | None = Field(
        default=None,
        ge=2020,
        description="경주계획표 수집 시 대상 연도",
    )
    rc_month: str | None = Field(
        default=None,
        description="경주계획표 수집 시 대상 월(예: 202605)",
    )


@router.post("/test")
async def run_collection_test(
    request: CollectionTestRequest,
    db: AsyncSession = Depends(get_db),
):
    # API 키가 비어 있으면 외부 API 호출 자체가 불가능하므로
    # 라우터에서 먼저 짧고 분명하게 막아두는 편이 디버깅에 유리합니다.
    kra_api_service = KRAApiService()
    data_service = DataService(db, kra_api_service)

    try:
        if request.collection_type == "schedule":
            target_year = request.rc_year or date.today().year
            target_month = request.rc_month or date.today().strftime("%Y%m")
            meet_codes = [request.meet_code] if request.meet_code else ["SC", "JJ", "BU"]
            summary = await data_service.collect_race_schedule(
                meet_codes=meet_codes,
                rc_year=target_year,
                rc_month=target_month,
            )
        elif request.collection_type == "entry":
            if request.meet_code is None:
                raise HTTPException(status_code=400, detail="entry 수집은 meet_code가 필요합니다.")

            summary = await data_service.collect_entry_info(
                meet_code=request.meet_code,
                rc_date=request.target_date or date.today(),
                rc_no=request.race_no,
            )
        else:
            if request.meet_code is None:
                raise HTTPException(status_code=400, detail="results 수집은 meet_code가 필요합니다.")

            summary = await data_service.collect_race_results(
                meet_code=request.meet_code,
                rc_date=request.target_date or date.today(),
                rc_no=request.race_no,
            )

        return {
            "success": summary.status in {"SUCCESS", "PARTIAL"},
            "data": {
                "apiName": summary.api_name,
                "status": summary.status,
                "recordsCollected": summary.records_collected,
                "dailyCallCount": summary.daily_call_count,
                "nullCount": summary.null_count,
                "anomalyCount": summary.anomaly_count,
                "qualityScore": str(summary.quality_score) if summary.quality_score is not None else None,
                "qualityStatus": summary.quality_status,
                "meetCode": summary.meet_code,
                "rcDate": summary.rc_date.isoformat() if summary.rc_date else None,
            },
            "message": summary.message or "수집 테스트 실행 완료",
        }
    except KRAApiError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error
    finally:
        await kra_api_service.close()


@router.post("/weather/test")
async def run_weather_test(
    db: AsyncSession = Depends(get_db),
):
    """3개 경마장(SC/BU/JJ)의 단기/중기예보를 수동으로 수집합니다.

    스케줄을 기다리지 않고 지금 바로 기상청 API를 호출해서 테스트할 때 사용합니다.
    실제 운영에서는 단기예보와 중기예보가 서로 다른 엔드포인트를 쓰므로
    이 테스트도 둘 다 실행해 두어야 구현 누락을 빨리 발견할 수 있습니다.
    """
    results = {}

    for meet_code in ("SC", "BU", "JJ"):
        weather_service = WeatherApiService(db)
        try:
            # 단기예보 수집 → DB 저장
            short_forecast_data = await weather_service.fetch_short_term_forecast(meet_code)
            short_saved_count = await weather_service.save_forecast(meet_code, short_forecast_data)

            # 중기예보 수집 → DB 저장
            mid_forecast_data = await weather_service.fetch_mid_term_forecast(meet_code)
            mid_saved_count = await weather_service.save_forecast(meet_code, mid_forecast_data)

            results[meet_code] = {
                "status": "SUCCESS",
                "shortTermSavedCount": short_saved_count,
                "midTermSavedCount": mid_saved_count,
            }
        except Exception as exc:
            # 한 경마장이 실패해도 나머지 경마장 수집은 계속 진행합니다.
            results[meet_code] = {"status": "ERROR", "message": str(exc)}
        finally:
            await weather_service.close()

    # 하나라도 성공이면 전체 success=True 로 응답합니다.
    has_success = any(v.get("status") == "SUCCESS" for v in results.values())
    return {
        "success": has_success,
        "data": results,
        "message": "날씨 수동 수집 완료",
    }


@router.get("/status")
async def get_collection_status(
    db: AsyncSession = Depends(get_db),
):
    kra_api_service = KRAApiService()
    data_service = DataService(db, kra_api_service)

    try:
        return {
            "success": True,
            "data": await data_service.get_today_collection_status(),
            "message": "오늘 수집 현황 조회 성공",
        }
    finally:
        await kra_api_service.close()
