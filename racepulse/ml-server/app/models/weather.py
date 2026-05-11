# -*- coding: utf-8 -*-
# =============================================================================
# weather.py — 날씨 예보 DB 모델
# =============================================================================
# 기상청 API에서 받아온 날씨 데이터를 PostgreSQL 에 저장하기 위한 테이블 구조입니다.
# 날씨 정보는 ML 예측 모델이 "오늘 경마장 날씨가 어떤가"를 파악하는 핵심 피처입니다.
# =============================================================================

# datetime = 데이터가 언제 저장됐는지 기록하는 created_at/updated_at 에 사용합니다.
from datetime import date, datetime
# Optional = 값이 없을 수도 있는 컬럼(nullable)을 표현하는 타입 힌트입니다.
from typing import Optional

# Date/DateTime/Float/Integer/String = 각 컬럼의 DB 타입을 지정하는 SQLAlchemy 타입입니다.
from sqlalchemy import Date, DateTime, Float, Integer, String
# func = DB 서버 시간(now())을 기본값으로 쓸 때 사용합니다.
from sqlalchemy import func
# Mapped/mapped_column = SQLAlchemy 2.0 방식의 ORM 선언 도구입니다.
# Mapped = "이 속성이 어떤 타입인지" 파이썬이 알 수 있게 도와주는 타입 힌트입니다.
# mapped_column = 실제 DB 컬럼 설정(이름, 기본값, 인덱스 등)을 지정합니다.
from sqlalchemy.orm import Mapped, mapped_column

# Base = 모든 SQLAlchemy 모델이 공통으로 상속받는 부모 클래스입니다.
from app.core.database import Base


class WeatherForecast(Base):
    # __tablename__ = PostgreSQL 에 실제로 만들어지는 테이블 이름입니다.
    __tablename__ = "weather_forecasts"

    # -------------------------------------------------------------------------
    # 기본 키
    # Integer + autoincrement = DB가 자동으로 1, 2, 3 ... 번호를 붙여줍니다.
    # -------------------------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # -------------------------------------------------------------------------
    # 경마장 코드
    # SC = 서울/과천, BU = 부산경남, JJ = 제주
    # nullable=False = 반드시 값이 있어야 합니다 (비워두면 DB 오류 발생).
    # -------------------------------------------------------------------------
    meet_code: Mapped[str] = mapped_column(String(2), nullable=False, comment="경마장 코드 (SC/BU/JJ)")

    # -------------------------------------------------------------------------
    # 예보 날짜
    # 단기예보는 오늘~3일 후, 중기예보는 3~10일 후 날짜가 들어옵니다.
    # -------------------------------------------------------------------------
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False, comment="예보 날짜")

    # -------------------------------------------------------------------------
    # 기온 정보 (단위: °C)
    # Float = 소수점 있는 실수 타입 (예: 18.5°C)
    # Optional = 기상청이 해당 값을 제공하지 않을 경우 NULL 허용
    # -------------------------------------------------------------------------
    temp_min: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="최저 기온 (°C)")
    temp_max: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="최고 기온 (°C)")

    # -------------------------------------------------------------------------
    # 강수 확률 (단위: %)
    # 0 ~ 100 사이의 정수로 표현됩니다.
    # -------------------------------------------------------------------------
    precipitation_prob: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, comment="강수 확률 (%)")

    # -------------------------------------------------------------------------
    # 풍속 (단위: m/s)
    # 기상청 단기예보에서 WSD 항목으로 제공됩니다.
    # -------------------------------------------------------------------------
    wind_speed: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="풍속 (m/s)")

    # -------------------------------------------------------------------------
    # 날씨 상태 (한글 텍스트)
    # 예: "맑음", "구름많음", "흐림", "비", "눈", "소나기"
    # 기상청 pty(강수형태)와 sky(하늘상태) 코드를 변환해서 저장합니다.
    # -------------------------------------------------------------------------
    condition: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, comment="날씨 상태 (맑음/비/눈 등)")

    # -------------------------------------------------------------------------
    # 데이터 출처
    # "short_term" = 단기예보 API, "mid_term" = 중기예보 API
    # -------------------------------------------------------------------------
    source: Mapped[str] = mapped_column(String(20), nullable=False, default="short_term", comment="데이터 출처 (short_term/mid_term)")

    # -------------------------------------------------------------------------
    # 생성/수정 시각 (자동 기록)
    # server_default = 레코드 INSERT 시 DB 서버 시간이 자동으로 입력됩니다.
    # onupdate = 레코드 UPDATE 시 자동으로 현재 시각으로 갱신됩니다.
    # -------------------------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="최초 저장 시각",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 수정 시각",
    )

    def __repr__(self) -> str:
        return f"<WeatherForecast {self.meet_code} {self.forecast_date} {self.condition}>"
