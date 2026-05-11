# -*- coding: utf-8 -*-
# =============================================================================
# models 패키지 초기화 파일
# =============================================================================
# 다른 파일에서 `from app.models import Race` 처럼 더 짧게 가져올 수 있게
# 주요 ORM 모델을 한 곳에서 다시 내보냅니다.
# =============================================================================

# Race/RaceEntry/RaceResult/CollectionLog = 경주와 수집로그 관련 ORM 모델입니다.
from app.models.race import Race, RaceEntry, RaceResult, CollectionLog
# Horse/Jockey/Trainer/Racecourse = 기준정보(마스터 데이터) ORM 모델입니다.
from app.models.master import Horse, Jockey, Trainer, Racecourse
# WeatherForecast = 기상청 날씨 예보 데이터 ORM 모델입니다.
from app.models.weather import WeatherForecast
# MLFeatureStore/Prediction/ModelVersion = ML 피처 스토어 및 예측 결과 ORM 모델입니다.
from app.models.ml import MLFeatureStore, Prediction, ModelVersion, AICommentary

__all__ = [
    "Race",
    "RaceEntry",
    "RaceResult",
    "CollectionLog",
    "Horse",
    "Jockey",
    "Trainer",
    "Racecourse",
    "WeatherForecast",
    "MLFeatureStore",
    "Prediction",
    "ModelVersion",
    "AICommentary",
]
