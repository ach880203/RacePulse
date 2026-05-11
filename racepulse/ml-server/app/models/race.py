# -*- coding: utf-8 -*-
# =============================================================================
# race.py — 경주/출전표/경주결과/수집로그 모델 모음
# =============================================================================
# 경주 관련 데이터는 한 번 수집한 뒤 계속 업데이트될 수 있으므로
# "기준정보(master)"와 "변동정보(race)"를 분리해 두면 데이터 흐름을 이해하기 쉽습니다.
# =============================================================================

# datetime/date/time = 경주일자, 출발시간, 수집시각 등을 표현하기 위한 기본 타입입니다.
from datetime import date, datetime, time
# Decimal = 부담중량, 배당, 품질점수처럼 소수 표현이 필요한 값을 안전하게 다루기 위한 타입입니다.
from decimal import Decimal
# Enum = 파이썬 enum 클래스의 부모입니다.
from enum import Enum
# List/Optional = 관계형 리스트와 nullable 타입 힌트에 사용합니다.
from typing import List, Optional

# Enum/Numeric/String/Integer/Date/DateTime/Boolean/Time = 각 컬럼의 DB 타입을 지정합니다.
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import Numeric, String, Integer, Date, DateTime, Boolean, Time, BigInteger
# ForeignKey = 다른 테이블 기본 키를 참조하는 외래키 선언입니다.
from sqlalchemy import ForeignKey
# Mapped/mapped_column/relationship = SQLAlchemy 2.0 ORM 선언 도구입니다.
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Base = 모든 모델의 공통 부모 클래스입니다.
from app.core.database import Base


def build_db_enum(enum_class: type[Enum], enum_name: str) -> SqlEnum:
    # PostgreSQL enum은 Python enum 이름이 아니라 DB에 저장된 실제 값으로 맞춰야
    # 한글 enum(예: 일반/중요/특별/국제)도 깨지지 않고 정확하게 저장됩니다.
    return SqlEnum(
        enum_class,
        name=enum_name,
        create_type=False,
        values_callable=lambda enum_members: [member.value for member in enum_members],
    )


class RaceStatusEnum(str, Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class TrackConditionEnum(str, Enum):
    DRY = "DRY"
    WET = "WET"
    HUMID = "HUMID"
    SATURATED = "SATURATED"


class RaceGradeEnum(str, Enum):
    NORMAL = "일반"
    IMPORTANT = "중요"
    SPECIAL = "특별"
    INTERNATIONAL = "국제"


class PaceScenarioEnum(str, Enum):
    FAST = "FAST"
    MODERATE = "MODERATE"
    SLOW = "SLOW"
    CONTESTED = "CONTESTED"


class PaceAdvantageEnum(str, Enum):
    FRONT = "FRONT"
    STALKER = "STALKER"
    CLOSER = "CLOSER"


class DataStatusEnum(str, Enum):
    READY = "READY"
    UPDATING = "UPDATING"
    COLLECTED = "COLLECTED"
    JOCKEY_CHANGED = "JOCKEY_CHANGED"


class ClassChangeEnum(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    SAME = "SAME"


class DistanceChangeEnum(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    SAME = "SAME"


class CollectStatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"
    SKIPPED = "SKIPPED"


class QualityStatusEnum(str, Enum):
    GOOD = "GOOD"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Race(Base):
    __tablename__ = "races"

    id: Mapped[int] = mapped_column(primary_key=True)
    meet_code: Mapped[str] = mapped_column(String(2), nullable=False)
    rc_date: Mapped[date] = mapped_column(Date, nullable=False)
    race_no: Mapped[int] = mapped_column(Integer, nullable=False)
    race_name: Mapped[Optional[str]] = mapped_column(String(100))
    distance: Mapped[Optional[int]] = mapped_column(Integer)
    track_type: Mapped[Optional[str]] = mapped_column(String(20))
    track_condition: Mapped[Optional[TrackConditionEnum]] = mapped_column(
        build_db_enum(TrackConditionEnum, "track_condition")
    )
    prize_money: Mapped[Optional[int]] = mapped_column(BigInteger)
    weather: Mapped[Optional[str]] = mapped_column(String(50))
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    status: Mapped[RaceStatusEnum] = mapped_column(
        build_db_enum(RaceStatusEnum, "race_status"),
        nullable=False,
        default=RaceStatusEnum.SCHEDULED,
    )
    race_class: Mapped[Optional[str]] = mapped_column(String(20))
    race_grade: Mapped[Optional[RaceGradeEnum]] = mapped_column(
        build_db_enum(RaceGradeEnum, "race_grade")
    )
    front_count: Mapped[Optional[int]]
    pace_scenario: Mapped[Optional[PaceScenarioEnum]] = mapped_column(
        build_db_enum(PaceScenarioEnum, "pace_scenario")
    )
    pace_advantage: Mapped[Optional[PaceAdvantageEnum]] = mapped_column(
        build_db_enum(PaceAdvantageEnum, "pace_advantage")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    race_entries: Mapped[List["RaceEntry"]] = relationship(back_populates="race")
    race_results: Mapped[List["RaceResult"]] = relationship(back_populates="race")


class RaceEntry(Base):
    __tablename__ = "race_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"), nullable=False)
    horse_id: Mapped[int] = mapped_column(ForeignKey("horses.id"), nullable=False)
    jockey_id: Mapped[Optional[int]] = mapped_column(ForeignKey("jockeys.id"))
    trainer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("trainers.id"))
    gate_no: Mapped[Optional[int]]
    burden_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 1))
    horse_weight: Mapped[Optional[int]]
    horse_weight_diff: Mapped[Optional[int]]
    rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    odds_win: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2))
    odds_place: Mapped[Optional[Decimal]] = mapped_column(Numeric(7, 2))
    data_status: Mapped[DataStatusEnum] = mapped_column(
        build_db_enum(DataStatusEnum, "data_status"),
        nullable=False,
        default=DataStatusEnum.READY,
    )
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_update: Mapped[Optional[datetime]] = mapped_column(DateTime)
    is_debut: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_comeback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    rest_days: Mapped[Optional[int]]
    class_change: Mapped[ClassChangeEnum] = mapped_column(
        build_db_enum(ClassChangeEnum, "class_change"),
        nullable=False,
        default=ClassChangeEnum.SAME,
    )
    distance_change: Mapped[DistanceChangeEnum] = mapped_column(
        build_db_enum(DistanceChangeEnum, "distance_change"),
        nullable=False,
        default=DistanceChangeEnum.SAME,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    race: Mapped["Race"] = relationship(back_populates="race_entries")
    horse: Mapped["Horse"] = relationship(back_populates="race_entries")
    jockey: Mapped[Optional["Jockey"]] = relationship(back_populates="race_entries")
    trainer: Mapped[Optional["Trainer"]] = relationship(back_populates="race_entries")
    race_results: Mapped[List["RaceResult"]] = relationship(back_populates="race_entry")


class RaceResult(Base):
    __tablename__ = "race_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    race_id: Mapped[int] = mapped_column(ForeignKey("races.id"), nullable=False)
    horse_id: Mapped[int] = mapped_column(ForeignKey("horses.id"), nullable=False)
    race_entry_id: Mapped[Optional[int]] = mapped_column(ForeignKey("race_entries.id"))
    rank: Mapped[Optional[int]]
    record_time: Mapped[Optional[str]] = mapped_column(String(20))
    margin: Mapped[Optional[str]] = mapped_column(String(20))
    section_1: Mapped[Optional[str]] = mapped_column(String(20))
    section_2: Mapped[Optional[str]] = mapped_column(String(20))
    section_3: Mapped[Optional[str]] = mapped_column(String(20))
    section_4: Mapped[Optional[str]] = mapped_column(String(20))
    section_5: Mapped[Optional[str]] = mapped_column(String(20))
    section_6: Mapped[Optional[str]] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    race: Mapped["Race"] = relationship(back_populates="race_results")
    horse: Mapped["Horse"] = relationship(back_populates="race_results")
    race_entry: Mapped[Optional["RaceEntry"]] = relationship(back_populates="race_results")


class CollectionLog(Base):
    __tablename__ = "collection_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    api_name: Mapped[str] = mapped_column(String(100), nullable=False)
    meet_code: Mapped[Optional[str]] = mapped_column(String(2))
    rc_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[CollectStatusEnum] = mapped_column(
        build_db_enum(CollectStatusEnum, "collect_status"),
        nullable=False,
    )
    records_collected: Mapped[Optional[int]]
    error_message: Mapped[Optional[str]]
    daily_call_count: Mapped[Optional[int]]
    null_count: Mapped[Optional[int]]
    anomaly_count: Mapped[Optional[int]]
    quality_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2))
    quality_status: Mapped[Optional[QualityStatusEnum]] = mapped_column(
        build_db_enum(QualityStatusEnum, "quality_status")
    )
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


# 순환 import 방지를 위해 파일 마지막에서만 타입 참조 import를 수행합니다.
from app.models.master import Horse, Jockey, Trainer  # noqa: E402
