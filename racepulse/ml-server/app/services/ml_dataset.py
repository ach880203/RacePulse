# -*- coding: utf-8 -*-
# =============================================================================
# ml_dataset.py — ML 모델 학습용 데이터 준비 서비스
# =============================================================================
# 학습(Train)과 테스트(Test)를 왜 분리하는가?
#   모델이 "시험 문제를 외워서" 높은 점수를 받는 것처럼,
#   학습한 데이터로 테스트하면 실제 성능보다 좋게 나옵니다.
#   이를 과적합(Overfitting)이라고 합니다.
#
#   과적합이란?
#     모델이 학습 데이터에 너무 최적화되어
#     새로운 데이터(실제 예측)에서는 성능이 떨어지는 현상입니다.
#     마치 교과서 문제만 외운 학생이 응용 문제는 못 푸는 것과 같습니다.
#
#   해결책: 학습 데이터(80%)와 테스트 데이터(20%)를 분리합니다.
#     학습 데이터 → 모델 파라미터 조정에 사용
#     테스트 데이터 → 한 번도 보지 않은 데이터로 성능 평가
#
# pandas DataFrame이란?
#   표(스프레드시트) 형태의 데이터를 파이썬에서 다루는 자료구조입니다.
#   ml_feature_store에서 가져온 JSON 피처를 행(출전마)/열(피처명)의 표로 변환합니다.
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# date = 날짜 범위 파라미터에 사용합니다.
from datetime import date
# Any = 타입 힌트입니다.
from typing import Any, Optional

# pandas = 표 형태 데이터를 다루는 라이브러리입니다.
import pandas as pd
# numpy = 수치 계산과 배열 처리를 담당합니다.
import numpy as np
# StandardScaler = 피처 값을 평균 0, 표준편차 1로 정규화합니다.
# train_test_split = 데이터를 학습/테스트용으로 나눕니다.
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

# SQLAlchemy 도구들
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모델
from app.models.ml import MLFeatureStore
from app.models.race import RaceResult, Race, RaceEntry, RaceStatusEnum

logger = logging.getLogger(__name__)

# 모델이 학습할 피처 컬럼 이름 목록 (순서가 중요합니다!)
# 학습할 때와 예측할 때 반드시 동일한 순서여야 합니다.
FEATURE_COLUMNS = [
    "horse_win_rate_total",
    "horse_win_rate_recent",
    "horse_place_rate",
    "horse_weight",
    "horse_weight_diff",
    "days_since_last_race",
    "avg_rank_last5",
    "best_rank_last5",
    "is_debut",
    "is_comeback",
    "class_change",
    "distance_change",
    "jockey_win_rate_total",
    "jockey_win_rate_recent",
    "jockey_horse_win_rate",
    "trainer_win_rate_total",
    "trainer_horse_win_rate",
    "gate_no",
    "burden_weight",
    "odds_win",
    "course_win_rate",
    "distance_win_rate",
    "condition_win_rate",
]


class MLDatasetService:
    """ML 모델 학습에 필요한 데이터를 준비하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def load_training_data(
        self,
        start_date: date,
        end_date: date,
    ) -> tuple[pd.DataFrame, pd.Series, list[int]]:
        """학습용 데이터를 DB에서 로드합니다.

        ml_feature_store에서 피처를 가져오고,
        race_results에서 실제 착순(정답 레이블)을 가져옵니다.

        @return (X, y, race_id_groups)
          X              = 피처 행렬 (출전마 수 × 피처 수 DataFrame)
          y              = 정답 레이블 (실제 착순, Series)
          race_id_groups = 각 행이 어느 경주에 속하는지 (LightGBM 그룹 학습용)
        """
        logger.info("[데이터셋] %s ~ %s 데이터 로드 시작", start_date, end_date)

        # 완료된 경주의 race_entry_id 목록 조회
        # 완료된 경주만 사용하는 이유: 결과가 없는 경주는 정답 레이블이 없습니다.
        entries_stmt = (
            select(
                RaceEntry.id.label("entry_id"),
                RaceEntry.race_id,
            )
            .join(Race, RaceEntry.race_id == Race.id)
            .where(
                and_(
                    Race.rc_date >= start_date,
                    Race.rc_date <= end_date,
                    Race.status == RaceStatusEnum.COMPLETED,
                )
            )
            .order_by(RaceEntry.race_id, RaceEntry.gate_no)
        )
        entry_rows = list((await self.db.execute(entries_stmt)).all())

        if not entry_rows:
            raise ValueError(
                f"{start_date} ~ {end_date} 사이 완료된 경주 출전 데이터가 없습니다. "
                "피처 계산(POST /ml/features/calculate)을 먼저 실행하세요."
            )

        entry_ids = [row.entry_id for row in entry_rows]
        race_ids  = [row.race_id  for row in entry_rows]

        # ml_feature_store에서 피처 벡터 조회
        features_stmt = (
            select(MLFeatureStore)
            .where(MLFeatureStore.race_entry_id.in_(entry_ids))
            .order_by(MLFeatureStore.race_entry_id)
        )
        feature_records = list((await self.db.scalars(features_stmt)).all())

        # 피처 레코드를 entry_id → features 딕셔너리로 변환합니다.
        feature_map: dict[int, dict] = {
            rec.race_entry_id: rec.features for rec in feature_records
        }

        # 실제 착순(정답) 조회
        result_stmt = (
            select(
                RaceResult.race_entry_id,
                RaceResult.rank,
            )
            .where(RaceResult.race_entry_id.in_(entry_ids))
        )
        result_rows = list((await self.db.execute(result_stmt)).all())
        result_map: dict[int, int] = {
            row.race_entry_id: row.rank
            for row in result_rows
            if row.rank is not None
        }

        # 피처와 정답이 모두 있는 출전마만 학습에 사용합니다.
        valid_entries = [
            eid for eid in entry_ids
            if eid in feature_map and eid in result_map
        ]

        if not valid_entries:
            raise ValueError(
                "피처와 결과 데이터가 모두 있는 출전마가 없습니다. "
                "피처 계산과 결과 수집을 먼저 실행하세요."
            )

        # DataFrame 구성
        rows = []
        labels = []
        groups = []

        prev_race_id = None
        for eid in valid_entries:
            feat  = feature_map[eid]
            label = result_map[eid]
            rows.append({col: feat.get(col) for col in FEATURE_COLUMNS})
            labels.append(label)

            # race_id_groups: 같은 경주 출전마들을 하나의 그룹으로 묶습니다.
            # LightGBM 순위 학습(rank)에서 그룹 정보가 필요합니다.
            cur_race_id = feature_map[eid].get("__race_id__") or 0
            if cur_race_id != prev_race_id:
                groups.append(1)
                prev_race_id = cur_race_id
            else:
                groups[-1] += 1

        X = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
        y = pd.Series(labels, name="rank")

        logger.info(
            "[데이터셋] 로드 완료. 샘플=%d, 피처=%d",
            len(X), len(FEATURE_COLUMNS)
        )
        return X, y, groups

    def split_train_test(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """학습/테스트 데이터를 분리합니다.

        test_size=0.2 = 전체의 20%를 테스트용으로 남겨둡니다.
        shuffle=False = 시간 순서를 유지합니다.
          시간 순서를 섞으면 미래 데이터로 과거를 예측하는 데이터 누수가 발생합니다.
          예: 2026년 3월 데이터를 학습하고 2026년 1월을 테스트 → 미래를 이미 봤으므로 불공정
        """
        # shuffle=False로 시간 순서를 보존합니다.
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            shuffle=False,  # 시간 순서 유지
        )
        logger.info(
            "[데이터셋] 학습=%d, 테스트=%d", len(X_train), len(X_test)
        )
        return X_train, X_test, y_train, y_test

    def preprocess_features(
        self,
        X_train: pd.DataFrame,
        X_test: Optional[pd.DataFrame] = None,
    ) -> tuple[np.ndarray, Optional[np.ndarray], StandardScaler]:
        """결측값 처리와 피처 정규화를 수행합니다.

        결측값(None/NaN) 처리:
          피처 계산 시 데이터가 없으면 None이 들어올 수 있습니다.
          ML 모델은 None을 처리하지 못하므로 0 또는 중앙값으로 채웁니다.

        표준화(Standard Scaling):
          각 피처의 값 범위가 달라도(0~1 승률 vs 0~100 마체중)
          모델이 공평하게 학습하도록 평균=0, 표준편차=1로 맞춥니다.
        """
        # 1. 결측값을 중앙값(median)으로 채웁니다.
        #    0으로 채우는 것보다 중앙값이 더 자연스러운 대체값입니다.
        X_train_filled = X_train.fillna(X_train.median())

        # 2. StandardScaler로 정규화합니다.
        #    학습 데이터의 평균/표준편차를 기준으로 변환합니다.
        #    테스트 데이터도 같은 기준(학습 기준)으로 변환해야 합니다.
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_filled)

        X_test_scaled = None
        if X_test is not None:
            X_test_filled = X_test.fillna(X_train.median())  # 학습 데이터 중앙값 사용
            X_test_scaled = scaler.transform(X_test_filled)

        return X_train_scaled, X_test_scaled, scaler
