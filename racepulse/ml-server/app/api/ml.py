# -*- coding: utf-8 -*-
# =============================================================================
# ml.py — ML 피처 계산 및 조회 API 라우터
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# asyncio = 비동기 실행과 스레드 풀 실행을 위해 사용합니다.
import asyncio
# date = 날짜 파라미터 파싱에 사용합니다.
from datetime import date
# Optional = 타입 힌트입니다.
from typing import Optional

# FastAPI 도구들
from fastapi import APIRouter, Depends, HTTPException

# SQLAlchemy
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.core.database import get_db, AsyncSessionLocal
from app.models.ml import MLFeatureStore, ModelVersion
from app.models.race import RaceEntry
from app.services.feature_engineering import FeatureEngineeringService, FEATURE_VERSION
from app.services.feature_batch import FeatureBatchService
from app.services.ml_dataset import MLDatasetService
from app.services.ml_trainer import MLTrainerService
from app.services.model_manager import ModelManagerService
from app.services.predictor import PredictorService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml")


@router.post("/features/calculate/{race_id}")
async def calculate_race_features(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주에 출전한 모든 말의 ML 피처를 계산하고 저장합니다.

    완료 기준 1: POST /ml/features/calculate/1 → 피처 계산 성공

    @param race_id  피처를 계산할 경주 ID
    """
    batch_svc = FeatureBatchService(db)
    try:
        result = await batch_svc.calculate_all_features_for_race(race_id)
        return {
            "success": True,
            "data":    result,
            "message": f"경주 {race_id}번 피처 계산 완료 ({result['processed']}마리 처리)",
        }
    except Exception as exc:
        logger.error("[ML API] 피처 계산 실패. race_id=%d, 오류=%s", race_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/features/{race_entry_id}")
async def get_features(
    race_entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """저장된 피처 벡터를 조회합니다.

    완료 기준 3: GET /ml/features/1 → 피처 조회 성공

    @param race_entry_id  조회할 출전마 레코드 ID
    """
    stmt = (
        select(MLFeatureStore)
        .where(
            and_(
                MLFeatureStore.race_entry_id == race_entry_id,
                MLFeatureStore.feature_version == FEATURE_VERSION,
            )
        )
        .order_by(MLFeatureStore.calculated_at.desc())
    )
    record = await db.scalar(stmt)

    if record is None:
        # 피처가 없으면 404를 반환하고 계산 방법을 안내합니다.
        raise HTTPException(
            status_code=404,
            detail=(
                f"race_entry_id={race_entry_id}의 피처가 없습니다. "
                f"먼저 POST /ml/features/calculate/{{race_id}} 를 실행해주세요."
            ),
        )

    features = record.features
    feature_count = len(features)

    return {
        "success": True,
        "data": {
            "raceEntryId":    record.race_entry_id,
            "raceId":         record.race_id,
            "featureVersion": record.feature_version,
            "featureCount":   feature_count,
            "calculatedAt":   record.calculated_at.isoformat(),
            "features":       features,
        },
        "message": f"피처 {feature_count}개 조회 성공",
    }


@router.post("/features/calculate-entry/{race_entry_id}")
async def calculate_single_entry_features(
    race_entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """출전마 1마리의 피처를 계산하고 저장합니다. (단건 테스트용)

    @param race_entry_id  피처를 계산할 출전마 레코드 ID
    """
    # 출전 레코드 존재 확인
    entry = await db.get(RaceEntry, race_entry_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"출전 정보를 찾을 수 없습니다: race_entry_id={race_entry_id}"
        )

    svc = FeatureEngineeringService(db)
    try:
        features = await svc.build_feature_vector(race_entry_id)
        record = await svc.save_to_feature_store(
            race_entry_id=race_entry_id,
            race_id=entry.race_id,
            features=features,
        )
        return {
            "success": True,
            "data": {
                "raceEntryId":  record.race_entry_id,
                "raceId":       record.race_id,
                "featureCount": len(features),
                "features":     features,
            },
            "message": f"피처 {len(features)}개 계산 완료",
        }
    except Exception as exc:
        logger.error("[ML API] 단건 피처 계산 실패. entry_id=%d, 오류=%s", race_entry_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


# =============================================================================
# 모델 학습 API
# =============================================================================

@router.post("/train")
async def train_model(
    model_type:     str  = "xgboost",
    start_date:     date = date(2025, 1, 1),
    end_date:       date = date(2026, 12, 31),
    version:        str  = "v1.0",
    db: AsyncSession = Depends(get_db),
):
    """ML 모델을 학습하고 model_versions 테이블에 등록합니다.

    완료 기준 1: POST /ml/train → 모델 학습 성공

    @param model_type  학습할 모델 종류 ("xgboost" 또는 "lgbm")
    @param start_date  학습 데이터 시작 날짜
    @param end_date    학습 데이터 종료 날짜
    @param version     모델 버전 이름 (예: "v1.0")

    ⚠️ 모델 학습은 시간이 걸리는 CPU 집중 작업입니다.
    asyncio.to_thread()로 별도 스레드에서 실행하여 서버가 멈추지 않게 합니다.
    """
    dataset_svc = MLDatasetService(db)
    trainer     = MLTrainerService()
    manager     = ModelManagerService(db)

    # 1. 학습 데이터 로드
    try:
        X, y, groups = await dataset_svc.load_training_data(start_date, end_date)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    # 2. 학습/테스트 분리
    X_train, X_test, y_train, y_test = dataset_svc.split_train_test(X, y)

    # 3. 피처 전처리 (결측값 처리 + 정규화)
    X_train_s, X_test_s, scaler = dataset_svc.preprocess_features(X_train, X_test)

    # 4. 모델 학습 (CPU 집중 작업 → 별도 스레드에서 실행)
    # asyncio.to_thread() = CPU 집중 작업을 별도 스레드로 넘겨
    # FastAPI의 비동기 이벤트 루프가 블로킹되지 않게 합니다.
    try:
        if model_type.lower() == "lgbm":
            # LightGBM 학습
            model = await asyncio.to_thread(
                trainer.train_lightgbm, X_train_s, y_train.values, groups
            )
            model_name = "lgbm"
        else:
            # XGBoost 학습 (기본)
            model = await asyncio.to_thread(
                trainer.train_xgboost, X_train_s, y_train.values, groups
            )
            model_name = "xgboost"
    except Exception as exc:
        logger.error("[학습] 모델 학습 실패: %s", exc)
        raise HTTPException(status_code=500, detail=f"모델 학습 실패: {exc}")

    # 5. 테스트 데이터로 성능 평가
    metrics = trainer.evaluate_model(
        model, X_test_s, y_test.values,
        model_name=model_name
    )

    # 6. 모델 파일 저장
    file_name  = f"{model_name}_{version}"
    model_path = trainer.save_model(model, file_name, scaler)

    # 7. model_versions 테이블에 등록
    record = await manager.register_model(
        model_name       = model_name,
        version          = version,
        model_path       = model_path,
        metrics          = metrics,
        train_start_date = start_date,
        train_end_date   = end_date,
    )

    # 첫 번째 모델이면 자동으로 활성화합니다.
    active = await manager.get_active_model(model_name)
    if not active:
        await manager.switch_model(record.id)

    return {
        "success": True,
        "data": {
            "modelName":    model_name,
            "version":      version,
            "modelPath":    model_path,
            "trainSamples": len(X_train),
            "testSamples":  len(X_test),
            "metrics":      metrics,
        },
        "message": (
            f"{model_name} {version} 학습 완료. "
            f"Top-1={metrics['top1_accuracy']}%, Top-3={metrics['top3_accuracy']}%"
        ),
    }


@router.get("/models")
async def list_models(db: AsyncSession = Depends(get_db)):
    """학습된 모델 버전 목록을 조회합니다."""
    manager = ModelManagerService(db)
    trainer = MLTrainerService()
    models  = await manager.list_models()
    saved   = trainer.list_saved_models()

    return {
        "success": True,
        "data": {
            "registered": [
                {
                    "id":            m.id,
                    "modelName":     m.model_name,
                    "version":       m.version,
                    "isActive":      m.is_active,
                    "metrics":       m.metrics,
                    "createdAt":     m.created_at.isoformat(),
                    "trainStart":    m.train_start_date.isoformat() if m.train_start_date else None,
                    "trainEnd":      m.train_end_date.isoformat()   if m.train_end_date   else None,
                }
                for m in models
            ],
            "savedFiles": saved,
        },
        "message": f"모델 {len(models)}건 조회 성공",
    }


@router.post("/predict/{race_id}")
async def predict_race(
    race_id:    int,
    model_name: str = "xgboost",
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 착순을 예측하고 predictions 테이블에 저장합니다.

    완료 기준 3: POST /ml/predict/1 → 예측 결과 생성

    @param race_id    예측할 경주 ID
    @param model_name 사용할 모델 이름 (기본: "xgboost")
    """
    predictor = PredictorService(db)
    try:
        results = await predictor.predict_race(race_id, model_name)
        return {
            "success": True,
            "data": {
                "raceId":      race_id,
                "modelName":   model_name,
                "predictions": results,
            },
            "message": f"경주 {race_id}번 예측 완료 ({len(results)}마리)",
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("[예측] race_id=%d 실패: %s", race_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/predict/{race_id}")
async def get_race_prediction(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 경주의 저장된 예측 결과를 조회합니다."""
    predictor = PredictorService(db)
    results   = await predictor.get_prediction_result(race_id)

    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"race_id={race_id}의 예측 결과가 없습니다. POST /ml/predict/{race_id} 를 먼저 실행하세요."
        )

    return {
        "success": True,
        "data": {"raceId": race_id, "predictions": results},
        "message": f"예측 결과 {len(results)}건 조회 성공",
    }


@router.get("/accuracy")
async def get_accuracy(db: AsyncSession = Depends(get_db)):
    """전체 예측 정확도 현황을 반환합니다.

    완료 기준 5: Top-1 / Top-3 정확도 수치 출력 확인
    """
    predictor = PredictorService(db)
    stats     = await predictor.get_accuracy_stats()

    return {
        "success": True,
        "data":    stats,
        "message": "예측 정확도 조회 성공",
    }


@router.post("/models/{model_version_id}/activate")
async def activate_model(
    model_version_id: int,
    db: AsyncSession = Depends(get_db),
):
    """특정 모델 버전을 활성 모델로 전환합니다."""
    manager = ModelManagerService(db)
    try:
        record = await manager.switch_model(model_version_id)
        return {
            "success": True,
            "data": {
                "id":        record.id,
                "modelName": record.model_name,
                "version":   record.version,
                "isActive":  record.is_active,
            },
            "message": f"{record.model_name} {record.version} 활성화 완료",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/features/recalculate")
async def recalculate_historical_features(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db),
):
    """날짜 범위 내 완료된 경주의 피처를 일괄 재계산합니다.

    피처 계산 로직이 변경됐을 때 사용합니다.

    @param start_date  재계산 시작 날짜 (예: 2026-01-01)
    @param end_date    재계산 종료 날짜 (예: 2026-05-01)
    """
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date가 end_date보다 클 수 없습니다.")

    batch_svc = FeatureBatchService(db)
    try:
        result = await batch_svc.recalculate_historical_features(start_date, end_date)
        return {
            "success": True,
            "data":    result,
            "message": f"히스토리 피처 재계산 완료 ({result['races_processed']}경주)",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
