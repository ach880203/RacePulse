# -*- coding: utf-8 -*-
# =============================================================================
# ml.py — ML 피처 스토어 / 예측 결과 / 모델 버전 ORM 모델
# =============================================================================
# 피처(Feature)란?
#   ML 모델이 "이 말이 1등을 할 확률"을 계산할 때 입력으로 쓰는 숫자 데이터입니다.
#   예: 최근 5경주 평균 착순, 기수 승률, 마체중 증감 ...
#   사람으로 치면 "이력서" — 다양한 정보를 수치로 표현한 것입니다.
#
# 왜 미리 계산해서 저장하는가?
#   경주 예측 요청이 올 때마다 DB에서 수십 개 테이블을 JOIN해서 계산하면
#   응답이 수 초씩 걸립니다. 미리 계산해두면 0.01초 이내로 응답할 수 있습니다.
#   (마치 시험지를 미리 풀어두고 제출만 하는 것처럼요)
# =============================================================================

# datetime/date = 날짜/시각 컬럼 타입에 사용합니다.
from datetime import date, datetime
# Decimal = 확률/점수처럼 소수가 필요한 컬럼에 씁니다.
from decimal import Decimal
# Optional = nullable 컬럼에 사용합니다.
from typing import Optional, Any

# SQLAlchemy 컬럼 타입들
from sqlalchemy import BigInteger, Boolean, Date, DateTime, Integer, Numeric, String, Text, ForeignKey
# JSONB = PostgreSQL 전용 JSON 바이너리 타입. 일반 JSON보다 조회가 빠릅니다.
from sqlalchemy.dialects.postgresql import JSONB
# Mapped/mapped_column = SQLAlchemy 2.0 방식의 ORM 컬럼 선언 도구입니다.
from sqlalchemy.orm import Mapped, mapped_column
# func = DB 서버 시각(NOW())을 기본값으로 쓸 때 사용합니다.
from sqlalchemy import func

# Base = 모든 ORM 모델의 공통 부모 클래스입니다.
from app.core.database import Base


class MLFeatureStore(Base):
    """ml_feature_store 테이블 — 출전마별 피처 벡터 저장소입니다.

    피처 벡터(Feature Vector)란?
      말 1마리의 모든 피처를 하나의 숫자 배열로 모아놓은 것입니다.
      예: [0.25, 3.2, 0.18, 56.0, -2, ...]
      ML 모델은 이 배열을 입력으로 받아서 착순 확률을 출력합니다.
    """
    __tablename__ = "ml_feature_store"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 어떤 출전마의 피처인지 (race_entries.id 참조)
    race_entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("race_entries.id", ondelete="CASCADE"), nullable=False
    )

    # 어떤 경주인지 (빠른 필터링을 위해 비정규화로 저장)
    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), nullable=False
    )

    # features = 계산된 피처 전체를 JSON으로 저장합니다.
    # 예: { "horse_win_rate_total": 0.25, "avg_rank_last5": 3.2 }
    # dict[str, float | None] 구조를 JSONB로 저장하면
    # 나중에 피처를 추가/제거해도 스키마 변경 없이 유연하게 대응할 수 있습니다.
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # 피처 계산 로직 버전 (로직이 바뀌면 "v1.1", "v2.0" 등으로 올립니다)
    feature_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="v1.0"
    )

    # 피처가 계산된 시각
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MLFeatureStore entry={self.race_entry_id} version={self.feature_version}>"


class Prediction(Base):
    """predictions 테이블 — ML 모델의 착순 예측 결과를 저장합니다."""
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), nullable=False
    )
    race_entry_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("race_entries.id", ondelete="CASCADE"), nullable=False
    )

    # 예측에 사용한 모델 이름 (예: "xgboost_v1", "lgbm_v2")
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # 예측 착순 (1 = 1위 예측)
    predicted_rank: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 1위 확률 (0.0 ~ 1.0)
    win_prob: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 5), nullable=True)

    # 3위 이내 확률
    place_prob: Mapped[Optional[Decimal]] = mapped_column(Numeric(6, 5), nullable=True)

    # 모델 원시 점수 (클수록 좋은 말)
    raw_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 6), nullable=True)

    # 예측에 사용한 모델 버전
    model_version: Mapped[str] = mapped_column(
        String(20), nullable=False, default="v1.0"
    )

    # 예측이 수행된 시각
    predicted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction entry={self.race_entry_id} "
            f"rank={self.predicted_rank} win={self.win_prob}>"
        )


class ModelVersion(Base):
    """model_versions 테이블 — 학습된 ML 모델의 메타데이터를 기록합니다.

    모델이 업그레이드될 때마다 새 행을 추가합니다.
    어떤 데이터로 학습했는지, 성능은 얼마인지 추적합니다.
    """
    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 모델 이름 (예: "xgboost", "lgbm", "ensemble")
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)

    # 버전 문자열 (예: "v1.0", "v2.3")
    version: Mapped[str] = mapped_column(String(20), nullable=False)

    # 모델 파일 저장 경로 (예: "models/xgboost_v1.0.pkl")
    model_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # 학습 결과 지표를 JSON으로 저장합니다.
    # 예: { "accuracy": 0.42, "top3_accuracy": 0.68, "ndcg": 0.75 }
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # 학습 데이터 기간
    train_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    train_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # 현재 서비스에 활성화된 모델인지 여부
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<ModelVersion {self.model_name} {self.version} active={self.is_active}>"


class AICommentary(Base):
    """ai_commentary 테이블 — GPT가 생성한 경주 해설을 저장합니다.

    사전 해설(PRE) = 경주 출전표 확정 후 금요일 08:00에 자동 생성
    결과 해설(POST) = 경주 결과 수집 후 월요일 14:00에 자동 생성

    Redis 캐시와 함께 사용하여 같은 경주는 GPT를 최대 2번만 호출합니다.
    (사전 1회 + 결과 1회 = 경주당 최대 2회 API 호출로 비용 고정)
    """
    __tablename__ = "ai_commentary"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    # 어떤 경주의 해설인지
    race_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("races.id", ondelete="CASCADE"), nullable=False
    )

    # 해설 종류: 'PRE'(사전) 또는 'POST'(결과)
    type: Mapped[str] = mapped_column(String(10), nullable=False)

    # GPT가 생성한 해설 텍스트 (600~1200자)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 사용한 GPT 모델 이름 (예: "gpt-4o-mini")
    model_used: Mapped[str] = mapped_column(
        String(50), nullable=False, default="gpt-4o-mini"
    )

    # Redis 캐시 키 (예: "pre_race:SC:20260508:1")
    cache_key: Mapped[str] = mapped_column(String(100), nullable=False)

    # GPT API 사용 토큰 수 (비용 모니터링)
    # 토큰(token)이란? GPT가 텍스트를 처리하는 단위입니다.
    # 대략 한국어 1글자 ≈ 2~3토큰, gpt-4o-mini 기준 1000토큰 ≈ $0.00015
    prompt_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completion_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # V13 품질 컬럼입니다. 해설 품질을 숫자로 남겨두면 운영자가 낮은 품질의 해설을 빠르게 찾아 재생성할 수 있습니다.
    quality_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 실제 사용한 temperature를 저장합니다. 사전 해설은 표현력이 중요하고 결과 해설은 정확성이 중요해서 서로 다른 값을 씁니다.
    temperature_used: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)

    # 금칙어가 감지되어 GPT를 다시 호출한 횟수입니다. 재시도가 많을수록 품질 점수를 낮게 보정합니다.
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # GPT 응답까지 걸린 시간(ms)입니다. 응답이 느려지면 사용자 경험에 직접 영향을 주므로 운영 지표로 저장합니다.
    generation_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<AICommentary race={self.race_id} type={self.type}>"
