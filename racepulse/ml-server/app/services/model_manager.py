# -*- coding: utf-8 -*-
# =============================================================================
# model_manager.py — 학습된 모델의 버전 관리 서비스
# =============================================================================
# 왜 모델 버전 관리가 필요한가?
#   ML 모델은 학습할 때마다 성능이 달라집니다.
#   "v1.0보다 v1.1이 정확도가 높다"는 것을 추적하고,
#   필요할 때 이전 버전으로 롤백할 수 있어야 합니다.
#   model_versions 테이블에 각 버전의 학습 조건과 성능 지표를 저장합니다.
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# datetime/date = 학습 날짜 기록에 사용합니다.
from datetime import date
# Optional = 값이 없을 수도 있는 타입 힌트입니다.
from typing import Optional, Any

# SQLAlchemy 도구들
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모델
from app.models.ml import ModelVersion

logger = logging.getLogger(__name__)


class ModelManagerService:
    """ML 모델 버전을 DB에 등록하고 관리하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def register_model(
        self,
        model_name: str,
        version: str,
        model_path: str,
        metrics: dict[str, Any],
        train_start_date: Optional[date] = None,
        train_end_date: Optional[date]   = None,
    ) -> ModelVersion:
        """새 모델 버전을 model_versions 테이블에 등록합니다.

        @param model_name        모델 이름 (예: "xgboost", "lgbm")
        @param version           버전 문자열 (예: "v1.0", "v2.3")
        @param model_path        저장된 모델 파일 경로
        @param metrics           평가 지표 딕셔너리 {top1_accuracy, top3_accuracy, ...}
        @param train_start_date  학습 데이터 시작 날짜
        @param train_end_date    학습 데이터 종료 날짜
        """
        # 이미 같은 (model_name, version) 이 있으면 기존 레코드를 업데이트합니다.
        stmt = select(ModelVersion).where(
            and_(
                ModelVersion.model_name == model_name,
                ModelVersion.version    == version,
            )
        )
        existing = await self.db.scalar(stmt)

        if existing:
            existing.model_path        = model_path
            existing.metrics           = metrics
            existing.train_start_date  = train_start_date
            existing.train_end_date    = train_end_date
            record = existing
            logger.info("[모델 버전] 업데이트: %s %s", model_name, version)
        else:
            record = ModelVersion(
                model_name        = model_name,
                version           = version,
                model_path        = model_path,
                metrics           = metrics,
                train_start_date  = train_start_date,
                train_end_date    = train_end_date,
                is_active         = False,
            )
            self.db.add(record)
            logger.info("[모델 버전] 등록: %s %s", model_name, version)

        await self.db.commit()
        return record

    async def get_active_model(self, model_name: str) -> Optional[ModelVersion]:
        """현재 서비스에서 사용 중인(is_active=True) 모델을 조회합니다."""
        stmt = select(ModelVersion).where(
            and_(
                ModelVersion.model_name == model_name,
                ModelVersion.is_active  == True,  # noqa: E712
            )
        )
        return await self.db.scalar(stmt)

    async def switch_model(self, model_version_id: int) -> ModelVersion:
        """특정 버전을 활성 모델로 전환합니다.

        기존 활성 모델은 비활성화하고 새 버전을 활성화합니다.
        예: v1.0 → v1.1 으로 전환 시 v1.0의 is_active = False, v1.1의 is_active = True
        """
        # 전환할 모델 조회
        new_model = await self.db.get(ModelVersion, model_version_id)
        if not new_model:
            raise ValueError(f"model_version_id={model_version_id}를 찾을 수 없습니다.")

        # 같은 model_name의 기존 활성 모델을 비활성화합니다.
        old_active = await self.get_active_model(new_model.model_name)
        if old_active and old_active.id != model_version_id:
            old_active.is_active = False
            logger.info("[모델 전환] 비활성화: %s %s", old_active.model_name, old_active.version)

        # 새 모델 활성화
        new_model.is_active = True
        await self.db.commit()
        logger.info("[모델 전환] 활성화: %s %s", new_model.model_name, new_model.version)
        return new_model

    async def list_models(self) -> list[ModelVersion]:
        """등록된 모든 모델 버전 목록을 반환합니다."""
        stmt = select(ModelVersion).order_by(
            ModelVersion.model_name, ModelVersion.created_at.desc()
        )
        return list((await self.db.scalars(stmt)).all())
