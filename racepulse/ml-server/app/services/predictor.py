# -*- coding: utf-8 -*-
# =============================================================================
# predictor.py — 학습된 모델로 경주 결과를 예측하는 서비스
# =============================================================================
# 예측 흐름:
#   1. ml_feature_store에서 해당 경주 출전마의 피처 벡터를 가져옵니다.
#   2. 학습된 모델(XGBoost/LightGBM)에 피처를 입력합니다.
#   3. 모델이 각 말의 "강도 점수"를 출력합니다.
#   4. 점수가 높은 순서대로 착순을 예측합니다.
#   5. predictions 테이블에 저장합니다.
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# Any/Optional = 타입 힌트입니다.
from typing import Any, Optional
# decimal = 확률값을 DB에 안전하게 저장하기 위한 타입입니다.
from decimal import Decimal

# numpy = 수치 계산과 배열 처리를 담당합니다.
import numpy as np
# pandas = 피처 데이터를 표 형태로 다룹니다.
import pandas as pd

# SQLAlchemy 도구들
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.models.ml import MLFeatureStore, Prediction, ModelVersion
from app.models.race import RaceEntry, RaceResult
from app.services.ml_trainer import MLTrainerService
from app.services.model_manager import ModelManagerService
from app.services.ml_dataset import FEATURE_COLUMNS

logger = logging.getLogger(__name__)

# 기본 사용 모델 이름 (가장 최근 학습된 모델을 찾을 때 사용)
DEFAULT_MODEL_NAME = "xgboost"


class PredictorService:
    """학습된 ML 모델로 경주 결과를 예측하고 저장하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db      = db
        self.trainer = MLTrainerService()
        self.manager = ModelManagerService(db)

    async def predict_race(
        self,
        race_id: int,
        model_name: str = DEFAULT_MODEL_NAME,
    ) -> list[dict[str, Any]]:
        """특정 경주의 출전마 착순을 예측하고 predictions 테이블에 저장합니다.

        @param race_id     예측할 경주 ID
        @param model_name  사용할 모델 이름 (기본: "xgboost")
        @return 출전마별 예측 결과 목록
        """
        # 1. 사용할 모델 버전 결정
        active = await self.manager.get_active_model(model_name)
        version = active.version if active else "v1.0"
        model_file = active.model_path if active else f"{model_name}_v1.0"

        # 파일 이름에서 경로 추출
        import os
        model_file_name = os.path.basename(model_file).replace(".pkl", "")

        # 2. 모델과 스케일러 로드
        try:
            model, scaler = self.trainer.load_model(model_file_name)
        except FileNotFoundError as exc:
            raise RuntimeError(
                f"학습된 모델이 없습니다. POST /ml/train 으로 먼저 학습하세요. ({exc})"
            )

        # 3. 해당 경주의 출전마 피처 로드
        features_stmt = (
            select(MLFeatureStore)
            .where(MLFeatureStore.race_id == race_id)
            .order_by(MLFeatureStore.race_entry_id)
        )
        feature_records = list((await self.db.scalars(features_stmt)).all())

        if not feature_records:
            raise ValueError(
                f"race_id={race_id}의 피처가 없습니다. "
                f"먼저 POST /ml/features/calculate/{race_id} 를 실행하세요."
            )

        # 4. 피처 행렬 구성 (DataFrame → numpy array)
        rows = [
            {col: rec.features.get(col) for col in FEATURE_COLUMNS}
            for rec in feature_records
        ]
        X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
        # 결측값(None)을 0으로 채우고 스케일러로 변환합니다.
        X_filled = X.fillna(0.0)
        if scaler:
            X_scaled = scaler.transform(X_filled)
        else:
            X_scaled = X_filled.values

        # 5. 모델로 강도 점수 계산
        # predict()는 각 말의 강도 점수를 반환합니다. (높을수록 1등에 가까움)
        scores = model.predict(X_scaled)

        # 6. 점수 기반 착순 예측
        # argsort()는 오름차순 인덱스를 반환하므로 [::-1]로 내림차순으로 뒤집습니다.
        rank_order = np.argsort(scores)[::-1]
        predicted_ranks = np.empty(len(scores), dtype=int)
        for rank_pos, idx in enumerate(rank_order, start=1):
            predicted_ranks[idx] = rank_pos

        # 7. predictions 테이블에 저장 (기존 예측은 삭제 후 재저장)
        await self.db.execute(
            delete(Prediction).where(Prediction.race_id == race_id)
        )

        # softmax로 확률로 변환합니다.
        # softmax = 점수를 합이 1인 확률 분포로 변환하는 함수입니다.
        probs = _softmax(scores)
        results = []

        for i, rec in enumerate(feature_records):
            pred_rank  = int(predicted_ranks[i])
            win_prob   = float(probs[i])
            # place_prob = 이 말이 상위 3마리 안에 들 확률 합계
            top3_mask  = (predicted_ranks <= 3)
            place_prob = float(probs[top3_mask].sum()) if top3_mask[i] else float(probs[i])

            prediction = Prediction(
                race_id       = race_id,
                race_entry_id = rec.race_entry_id,
                model_name    = model_name,
                predicted_rank = pred_rank,
                win_prob      = Decimal(str(round(win_prob, 5))),
                place_prob    = Decimal(str(round(min(place_prob, 1.0), 5))),
                raw_score     = Decimal(str(round(float(scores[i]), 6))),
                model_version = version,
            )
            self.db.add(prediction)
            results.append({
                "race_entry_id":  rec.race_entry_id,
                "predicted_rank": pred_rank,
                "win_prob":       round(win_prob * 100, 2),
                "raw_score":      round(float(scores[i]), 4),
            })

        await self.db.commit()
        logger.info(
            "[예측] race_id=%d 완료. %d마리 예측, 모델=%s %s",
            race_id, len(results), model_name, version
        )
        return results

    async def predict_race_ensemble(self, race_id: int) -> list[dict[str, Any]]:
        """XGBoost + LightGBM 앙상블 예측을 수행합니다.

        두 모델의 점수를 각각 0~1로 정규화한 뒤 평균을 내어
        단일 모델보다 안정적인 예측을 제공합니다.

        앙상블(Ensemble)이란?
          여러 모델의 예측을 합쳐 더 정확하고 안정적인 결과를 내는 기법입니다.
          한 모델이 틀려도 다른 모델이 보정해주는 효과가 있습니다.
        """
        import os

        # 1. 피처 로드 (두 모델 공통으로 사용)
        features_stmt = (
            select(MLFeatureStore)
            .where(MLFeatureStore.race_id == race_id)
            .order_by(MLFeatureStore.race_entry_id)
        )
        feature_records = list((await self.db.scalars(features_stmt)).all())
        if not feature_records:
            raise ValueError(f"race_id={race_id}의 피처가 없습니다.")

        rows = [{col: rec.features.get(col) for col in FEATURE_COLUMNS} for rec in feature_records]
        X = pd.DataFrame(rows, columns=FEATURE_COLUMNS).fillna(0.0)

        all_scores = []

        # 2. 각 모델 점수 계산
        for name in ("xgboost", "lgbm"):
            active = await self.manager.get_active_model(name)
            model_file = active.model_path if active else f"{name}_v1.0"
            model_file_name = os.path.basename(model_file).replace(".pkl", "")
            try:
                model, scaler = self.trainer.load_model(model_file_name)
            except FileNotFoundError:
                logger.warning("[앙상블] %s 모델 없음 — 건너뜀", name)
                continue

            X_scaled = scaler.transform(X) if scaler else X.values
            raw_scores = model.predict(X_scaled).astype(float)

            # Min-Max 정규화: 두 모델의 점수 척도가 달라 그대로 더하면 안 됩니다.
            # 0~1 범위로 맞춘 뒤 평균해야 공정한 앙상블이 됩니다.
            score_min = raw_scores.min()
            score_max = raw_scores.max()
            if score_max > score_min:
                normalized = (raw_scores - score_min) / (score_max - score_min)
            else:
                normalized = np.ones_like(raw_scores) / len(raw_scores)

            all_scores.append(normalized)

        if not all_scores:
            raise RuntimeError("앙상블할 모델이 없습니다. POST /ml/train 으로 먼저 학습하세요.")

        # 3. 정규화된 점수 평균
        ensemble_scores = np.mean(all_scores, axis=0)

        # 4. 착순 예측 및 저장
        rank_order = np.argsort(ensemble_scores)[::-1]
        predicted_ranks = np.empty(len(ensemble_scores), dtype=int)
        for rank_pos, idx in enumerate(rank_order, start=1):
            predicted_ranks[idx] = rank_pos

        await self.db.execute(
            delete(Prediction).where(Prediction.race_id == race_id)
        )

        probs = _softmax(ensemble_scores)
        results = []

        for i, rec in enumerate(feature_records):
            pred_rank = int(predicted_ranks[i])
            win_prob  = float(probs[i])
            top3_mask = (predicted_ranks <= 3)
            place_prob = float(probs[top3_mask].sum()) if top3_mask[i] else float(probs[i])

            self.db.add(Prediction(
                race_id        = race_id,
                race_entry_id  = rec.race_entry_id,
                model_name     = "ensemble",
                predicted_rank = pred_rank,
                win_prob       = Decimal(str(round(win_prob, 5))),
                place_prob     = Decimal(str(round(min(place_prob, 1.0), 5))),
                raw_score      = Decimal(str(round(float(ensemble_scores[i]), 6))),
                model_version  = "v1.0",
            ))
            results.append({
                "race_entry_id":  rec.race_entry_id,
                "predicted_rank": pred_rank,
                "win_prob":       round(win_prob * 100, 2),
                "raw_score":      round(float(ensemble_scores[i]), 4),
            })

        await self.db.commit()
        logger.info("[앙상블 예측] race_id=%d 완료. %d마리 예측", race_id, len(results))
        return results

    async def get_prediction_result(self, race_id: int) -> list[dict[str, Any]]:
        """race_id의 예측 결과를 조회합니다."""
        stmt = (
            select(Prediction)
            .where(Prediction.race_id == race_id)
            .order_by(Prediction.predicted_rank)
        )
        preds = list((await self.db.scalars(stmt)).all())

        return [
            {
                "race_entry_id":  p.race_entry_id,
                "predicted_rank": p.predicted_rank,
                "win_prob":       float(p.win_prob) * 100 if p.win_prob else None,
                "place_prob":     float(p.place_prob) * 100 if p.place_prob else None,
                "model_name":     p.model_name,
                "model_version":  p.model_version,
            }
            for p in preds
        ]

    async def get_accuracy_stats(self) -> dict[str, Any]:
        """전체 예측 정확도를 계산하여 반환합니다.

        predictions 테이블과 race_results 테이블을 JOIN하여 계산합니다.
        """
        # 예측과 실제 결과가 모두 있는 건수 조회
        from sqlalchemy import func

        joined = (
            select(
                Prediction.predicted_rank,
                RaceResult.rank.label("actual_rank"),
            )
            .join(RaceResult, Prediction.race_entry_id == RaceResult.race_entry_id)
            .where(Prediction.predicted_rank == 1)  # 1위로 예측한 것만
        )
        rows = list((await self.db.execute(joined)).all())

        if not rows:
            return {
                "totalPredictions": 0,
                "top1Accuracy":     0.0,
                "top3Accuracy":     0.0,
                "message":          "예측 결과가 없습니다.",
            }

        total     = len(rows)
        top1_hits = sum(1 for r in rows if r.actual_rank == 1)
        top3_hits = sum(1 for r in rows if r.actual_rank <= 3)

        return {
            "totalPredictions": total,
            "top1Accuracy":     round(top1_hits / total * 100, 2),
            "top3Accuracy":     round(top3_hits / total * 100, 2),
            "top1Hits":         top1_hits,
            "top3Hits":         top3_hits,
        }


# =============================================================================
# 유틸리티
# =============================================================================

def _softmax(x: np.ndarray) -> np.ndarray:
    """점수 배열을 확률 분포로 변환합니다.

    softmax 공식: e^xi / Σ(e^xj)
    입력 값이 크면 확률이 높아지고, 모든 확률의 합은 1이 됩니다.
    """
    # 수치 안정성을 위해 최대값을 빼줍니다 (overflow 방지)
    shifted = x - np.max(x)
    exp_x = np.exp(shifted)
    return exp_x / exp_x.sum()
