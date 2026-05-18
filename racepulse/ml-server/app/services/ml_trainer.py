# -*- coding: utf-8 -*-
# =============================================================================
# ml_trainer.py — XGBoost / LightGBM 모델 학습 서비스
# =============================================================================
# XGBoost(eXtreme Gradient Boosting)란?
#   여러 개의 약한 결정 트리(Decision Tree)를 순서대로 학습하여
#   앞 모델의 오류를 다음 모델이 보정하는 방식입니다.
#   경마 순위 예측처럼 "이 말이 다른 말보다 더 잘 달릴 확률"을 계산할 때 강점이 있습니다.
#
# LightGBM(Light Gradient Boosting Machine)이란?
#   XGBoost와 같은 원리이지만 학습 속도가 매우 빠릅니다.
#   대용량 데이터(수만 건 이상)에서 XGBoost보다 3~10배 빠릅니다.
#   경마 데이터처럼 연속적으로 쌓이는 데이터에 적합합니다.
#
# XGBoost vs LightGBM 주요 차이:
#   XGBoost: 트리를 레벨(depth) 단위로 확장 → 안정적, 과적합 저항성
#   LightGBM: 트리를 잎(leaf) 단위로 확장 → 빠름, 정확도 높음, 과적합 위험 있음
#
# joblib으로 모델을 저장/로드하는 이유:
#   모델 학습에 수 분~수 시간이 걸리므로 학습 결과를 파일로 저장해둡니다.
#   서버 재시작 시 저장된 파일을 불러와 바로 예측에 활용합니다.
#   마치 "공부한 노트"를 파일로 저장해두는 것과 같습니다.
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# os = 파일/디렉토리 경로 관련 작업에 사용합니다.
import os
# time = 학습 소요 시간 측정에 사용합니다.
import time
# datetime = 모델 버전 이름 생성에 사용합니다.
from datetime import datetime, date
# Any = 타입 힌트입니다.
from typing import Any, Optional

# numpy = 수치 계산을 위한 라이브러리입니다.
import numpy as np
# pandas = 데이터 처리 라이브러리입니다.
import pandas as pd
# joblib = 파이썬 객체(모델)를 파일로 저장/로드하는 라이브러리입니다.
import joblib
# XGBoost = 경사 부스팅 기반 고성능 ML 라이브러리입니다.
import xgboost as xgb
# LightGBM = Microsoft가 개발한 빠른 경사 부스팅 라이브러리입니다.
import lightgbm as lgb
# sklearn 지표 계산 도구들
from sklearn.metrics import ndcg_score

logger = logging.getLogger(__name__)

# 모델 파일을 저장할 디렉토리
MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "models")


def _ensure_models_dir() -> None:
    """models 디렉토리가 없으면 만듭니다."""
    os.makedirs(MODELS_DIR, exist_ok=True)


class MLTrainerService:
    """XGBoost / LightGBM 모델 학습, 평가, 저장을 담당하는 서비스입니다."""

    # =========================================================================
    # XGBoost 학습
    # =========================================================================

    def train_xgboost(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        groups: Optional[list[int]] = None,
    ) -> xgb.XGBRanker:
        """XGBoost 순위 예측 모델을 학습합니다.

        objective='rank:pairwise' 란?
          "이 말이 저 말보다 높은 순위가 될 확률"을 학습하는 방식입니다.
          단순히 착순 숫자를 예측하는 것보다 경마 예측에 더 적합합니다.

        @param X_train  학습 피처 행렬
        @param y_train  실제 착순 배열
        @param groups   경주별 그룹 크기 (순위 학습용)
        @return 학습된 XGBoost 모델
        """
        logger.info("[XGBoost] 학습 시작. 샘플=%d, 피처=%d", len(X_train), X_train.shape[1])
        start = time.time()

        # XGBoost 순위 예측 모델 설정
        # rank:pairwise = 두 말을 짝지어 "어느 쪽이 더 앞설지" 학습합니다.
        model = xgb.XGBRanker(
            objective="rank:pairwise",
            max_depth=6,           # 결정 트리의 최대 깊이 (너무 깊으면 과적합)
            learning_rate=0.1,     # 한 번에 얼마나 빨리 학습할지 (너무 크면 불안정)
            n_estimators=300,      # 만들 결정 트리 수 (많을수록 정확하지만 느림)
            subsample=0.8,         # 각 트리에 사용할 데이터 비율 (과적합 방지)
            colsample_bytree=0.8,  # 각 트리에 사용할 피처 비율 (과적합 방지)
            random_state=42,       # 랜덤 시드 (재현성을 위해 고정)
            n_jobs=-1,             # 모든 CPU 코어 사용
        )

        # group = 경주별로 그룹을 나누어 학습합니다.
        # 그룹이 없으면 모든 말을 하나의 경주로 간주하므로 groups를 꼭 넣어야 합니다.
        qid = _groups_to_qid(groups, len(X_train))
        model.fit(X_train, y_train, qid=qid)

        elapsed = time.time() - start
        logger.info("[XGBoost] 학습 완료. 소요시간=%.1f초", elapsed)
        return model

    # =========================================================================
    # LightGBM 학습
    # =========================================================================

    def train_lightgbm(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        groups: Optional[list[int]] = None,
    ) -> lgb.LGBMRanker:
        """LightGBM 순위 예측 모델을 학습합니다.

        LightGBM은 XGBoost보다 빠르지만 과적합에 더 민감합니다.
        데이터가 많을수록(1만 건 이상) 더 좋은 성능을 냅니다.
        """
        logger.info("[LightGBM] 학습 시작. 샘플=%d, 피처=%d", len(X_train), X_train.shape[1])
        start = time.time()

        model = lgb.LGBMRanker(
            # LGBMRanker는 objective를 명시하지 않으면 lambdarank가 자동 적용됩니다.
            # "rank"는 유효하지 않은 값이므로 제거합니다.
            num_leaves=31,     # 결정 트리 잎 수 (많을수록 복잡한 패턴 학습)
            learning_rate=0.1,
            n_estimators=300,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            n_jobs=-1,
            verbose=-1,        # 학습 중 상세 로그 출력 끄기
        )

        # LightGBM의 group = 각 경주에 몇 마리가 출전했는지 목록입니다.
        # 예: [10, 12, 8, 9] = 4경주에 각각 10, 12, 8, 9마리 출전
        group = groups if groups else [len(y_train)]
        model.fit(X_train, y_train, group=group)

        elapsed = time.time() - start
        logger.info("[LightGBM] 학습 완료. 소요시간=%.1f초", elapsed)
        return model

    # =========================================================================
    # 모델 평가
    # =========================================================================

    def evaluate_model(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        groups: Optional[list[int]] = None,
        model_name: str = "model",
    ) -> dict[str, float]:
        """학습된 모델의 예측 정확도를 계산합니다.

        Top-1 정확도:
          모델이 가장 높은 점수를 준 말이 실제로 1위를 했는지의 비율
          계산: 각 경주에서 예측 1위 말이 실제 1위이면 적중

        Top-3 정확도:
          모델이 가장 높은 점수를 준 말이 실제로 3위 이내인지의 비율

        NDCG(Normalized Discounted Cumulative Gain):
          순위 예측의 전반적인 질을 평가하는 지표 (0~1, 높을수록 좋음)
        """
        # 모델이 출력하는 점수 (높을수록 1위에 가까움)
        scores = model.predict(X_test)

        # 경주별로 나누어 정확도를 계산합니다.
        top1_hits = 0
        top3_hits = 0
        total_races = 0

        idx = 0
        qid_groups = groups if groups else [len(y_test)]

        for g_size in qid_groups:
            if idx + g_size > len(scores):
                break

            # 이 경주의 점수와 실제 착순 추출
            race_scores = scores[idx:idx + g_size]
            race_ranks  = np.array(y_test[idx:idx + g_size])

            # 모델이 가장 높은 점수를 준 말의 인덱스
            pred_winner_idx = np.argmax(race_scores)
            actual_rank = race_ranks[pred_winner_idx]

            if actual_rank == 1:
                top1_hits += 1
            if actual_rank <= 3:
                top3_hits += 1

            total_races += 1
            idx += g_size

        top1_accuracy = (top1_hits / total_races * 100) if total_races > 0 else 0.0
        top3_accuracy = (top3_hits / total_races * 100) if total_races > 0 else 0.0

        metrics = {
            "top1_accuracy": round(top1_accuracy, 2),
            "top3_accuracy": round(top3_accuracy, 2),
            "total_races":   total_races,
            "top1_hits":     top1_hits,
            "top3_hits":     top3_hits,
        }

        logger.info(
            "[%s] 평가 결과: Top-1=%.1f%%, Top-3=%.1f%% (%d경주)",
            model_name, top1_accuracy, top3_accuracy, total_races
        )
        return metrics

    # =========================================================================
    # 모델 저장 / 로드
    # =========================================================================

    def save_model(self, model: Any, model_name: str, scaler: Any = None) -> str:
        """학습된 모델을 파일로 저장합니다.

        joblib이란?
          파이썬 객체(모델, 스케일러 등)를 바이너리 파일로 저장하는 도구입니다.
          pickle과 비슷하지만 numpy 배열이 포함된 ML 모델에 더 최적화됩니다.

        @param model       저장할 모델 객체
        @param model_name  파일 이름 (예: "xgboost_v1.0")
        @param scaler      함께 저장할 StandardScaler (예측 시 같이 필요)
        @return 저장된 파일 경로
        """
        _ensure_models_dir()
        model_path  = os.path.join(MODELS_DIR, f"{model_name}.pkl")
        scaler_path = os.path.join(MODELS_DIR, f"{model_name}_scaler.pkl")

        # 모델 저장
        joblib.dump(model, model_path)
        logger.info("[모델 저장] %s", model_path)

        # 스케일러도 함께 저장합니다.
        # 예측 시 학습에 사용한 것과 동일한 스케일러로 피처를 변환해야 합니다.
        if scaler is not None:
            joblib.dump(scaler, scaler_path)
            logger.info("[스케일러 저장] %s", scaler_path)

        return model_path

    def load_model(self, model_name: str) -> tuple[Any, Optional[Any]]:
        """저장된 모델과 스케일러를 로드합니다.

        @param model_name 로드할 모델 이름 (예: "xgboost_v1.0")
        @return (model, scaler) 튜플
        """
        model_path  = os.path.join(MODELS_DIR, f"{model_name}.pkl")
        scaler_path = os.path.join(MODELS_DIR, f"{model_name}_scaler.pkl")

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"모델 파일을 찾을 수 없습니다: {model_path}. "
                f"POST /ml/train 으로 먼저 학습하세요."
            )

        model  = joblib.load(model_path)
        scaler = joblib.load(scaler_path) if os.path.exists(scaler_path) else None

        logger.info("[모델 로드] %s", model_path)
        return model, scaler

    def list_saved_models(self) -> list[str]:
        """저장된 모델 파일 목록을 반환합니다."""
        _ensure_models_dir()
        files = [
            f.replace(".pkl", "")
            for f in os.listdir(MODELS_DIR)
            if f.endswith(".pkl") and not f.endswith("_scaler.pkl")
        ]
        return sorted(files)


# =============================================================================
# 유틸리티
# =============================================================================

def _groups_to_qid(groups: Optional[list[int]], n: int) -> np.ndarray:
    """그룹 크기 목록을 XGBoost qid 배열로 변환합니다.

    qid(Query ID) = 각 샘플이 어느 그룹(경주)에 속하는지를 나타내는 인덱스 배열
    예: groups=[3, 2] → qid=[0, 0, 0, 1, 1]
    """
    if not groups:
        return np.zeros(n, dtype=np.int32)

    qid = np.empty(n, dtype=np.int32)
    idx = 0
    for gid, size in enumerate(groups):
        qid[idx:idx + size] = gid
        idx += size
    return qid
