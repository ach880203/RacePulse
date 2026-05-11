# -*- coding: utf-8 -*-
# =============================================================================
# master.py — 말/기수/조교사/경마장 같은 기준정보(마스터 데이터) 모델 모음
# =============================================================================
# 마스터 데이터는 경주가 반복되어도 계속 재사용되는 "기본 정보"입니다.
# 예: 경주 하나가 끝나도 말 이름, 기수 이름, 경마장 정보 자체는 계속 남습니다.
# =============================================================================

# datetime = 생성/수정 시각 컬럼을 파이썬에서 다룰 때 사용합니다.
from datetime import datetime
# Decimal = 승률 같은 소수 값을 float보다 더 안전하게 저장할 때 쓰는 타입입니다.
from decimal import Decimal
# List = relationship 컬렉션 타입 힌트에 사용합니다.
from typing import List, Optional

# Mapped/mapped_column = SQLAlchemy 2.0 방식으로 "이 필드가 DB 컬럼이다"를 선언하는 도구입니다.
from sqlalchemy.orm import Mapped, mapped_column, relationship
# String/Numeric/Boolean/DateTime/JSON = 컬럼 타입을 지정하는 SQLAlchemy 기본 타입들입니다.
from sqlalchemy import String, Numeric, Boolean, DateTime
from sqlalchemy.dialects.postgresql import JSONB

# Base = 모든 ORM 모델이 공통으로 상속받는 부모 클래스입니다.
from app.core.database import Base


class Horse(Base):
    # __tablename__ = 이 파이썬 클래스가 어떤 DB 테이블과 연결되는지 지정합니다.
    __tablename__ = "horses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    eng_name: Mapped[Optional[str]] = mapped_column(String(100))
    birth_year: Mapped[Optional[int]]
    sex: Mapped[Optional[str]] = mapped_column(String(10))
    color: Mapped[Optional[str]] = mapped_column(String(50))
    origin: Mapped[Optional[str]] = mapped_column(String(100))
    father_name: Mapped[Optional[str]] = mapped_column(String(100))
    mother_name: Mapped[Optional[str]] = mapped_column(String(100))
    owner: Mapped[Optional[str]] = mapped_column(String(100))
    meet_code: Mapped[Optional[str]] = mapped_column(String(2))
    rating_1: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    rating_2: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    rating_3: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    rating_4: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    coat_color: Mapped[Optional[str]] = mapped_column(String(50))
    body_type: Mapped[Optional[str]] = mapped_column(String(50))
    photo_url: Mapped[Optional[str]]
    thumbnail_url: Mapped[Optional[str]]
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # relationship = 다른 테이블과의 연결을 객체처럼 따라가게 해주는 ORM 기능입니다.
    # 말 한 마리는 여러 출전표/성적과 연결될 수 있으므로 리스트 관계로 둡니다.
    race_entries: Mapped[List["RaceEntry"]] = relationship(back_populates="horse")
    race_results: Mapped[List["RaceResult"]] = relationship(back_populates="horse")


class Jockey(Base):
    __tablename__ = "jockeys"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    eng_name: Mapped[Optional[str]] = mapped_column(String(100))
    meet_code: Mapped[Optional[str]] = mapped_column(String(2))
    license_no: Mapped[Optional[str]] = mapped_column(String(20))
    win_rate_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    win_rate_recent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    place_rate_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    race_entries: Mapped[List["RaceEntry"]] = relationship(back_populates="jockey")


class Trainer(Base):
    __tablename__ = "trainers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    eng_name: Mapped[Optional[str]] = mapped_column(String(100))
    meet_code: Mapped[Optional[str]] = mapped_column(String(2))
    license_no: Mapped[Optional[str]] = mapped_column(String(20))
    win_rate_total: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    win_rate_recent: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 4))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    race_entries: Mapped[List["RaceEntry"]] = relationship(back_populates="trainer")


class Racecourse(Base):
    __tablename__ = "racecourses"

    id: Mapped[int] = mapped_column(primary_key=True)
    meet_code: Mapped[str] = mapped_column(String(2), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    track_types: Mapped[list] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
