# -*- coding: utf-8 -*-
# =============================================================================
# weather.py — 날씨 조회 API 라우터
# =============================================================================
# 경마장별로 저장된 날씨 예보 데이터를 조회하는 엔드포인트 모음입니다.
# ML 모델이나 프론트엔드에서 "이 날 이 경마장 날씨가 어때?"를 물어볼 때 사용합니다.
# =============================================================================

# date = URL 경로에서 날짜를 받을 때 사용합니다.
from datetime import date
# Literal = meet_code 에 허용된 값(SC/BU/JJ)만 받도록 제한하는 타입입니다.
from typing import Literal

# APIRouter = 관련 API들을 하나의 라우터 묶음으로 관리하는 FastAPI 도구입니다.
from fastapi import APIRouter, Depends, HTTPException
# AsyncSession = DB 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# get_db = 요청마다 비동기 DB 세션을 안전하게 빌려주는 의존성 함수입니다.
from app.core.database import get_db
# WeatherApiService = 날씨 데이터 조회/저장을 담당하는 서비스입니다.
from app.services.weather_api import WeatherApiService

router = APIRouter(prefix="/weather")


@router.get("/{meet_code}/{target_date}")
async def get_weather(
    meet_code: Literal["SC", "BU", "JJ"],
    target_date: date,
    db: AsyncSession = Depends(get_db),
):
    """특정 경마장의 특정 날짜 날씨를 조회합니다.

    경로 예시: GET /weather/SC/2026-05-08
      - meet_code: SC(서울/과천), BU(부산경남), JJ(제주)
      - target_date: YYYY-MM-DD 형식의 날짜
    """
    weather_service = WeatherApiService(db)
    try:
        # DB에서 해당 경마장 + 날짜의 날씨 데이터를 조회합니다.
        record = await weather_service.get_weather(meet_code, target_date)

        if record is None:
            # 데이터가 없으면 404 Not Found 응답을 반환합니다.
            raise HTTPException(
                status_code=404,
                detail=f"{meet_code} 경마장 {target_date} 날씨 데이터가 없습니다. 먼저 수집을 실행해주세요.",
            )

        return {
            "success": True,
            "data": {
                "meetCode": record.meet_code,
                "forecastDate": record.forecast_date.isoformat(),
                "tempMin": record.temp_min,
                "tempMax": record.temp_max,
                "precipitationProb": record.precipitation_prob,
                "windSpeed": record.wind_speed,
                "condition": record.condition,
                "source": record.source,
                "updatedAt": record.updated_at.isoformat(),
            },
            "message": "날씨 조회 성공",
        }
    finally:
        await weather_service.close()
