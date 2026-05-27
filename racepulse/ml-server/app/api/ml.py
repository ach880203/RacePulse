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
# BaseModel = JSON body로 들어오는 Monte Carlo 요청 값을 타입으로 검증하기 위한 Pydantic 기본 클래스입니다.
from pydantic import BaseModel

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
from app.services.monte_carlo import MonteCarloService
from app.services.predictor import PredictorService
from app.services.rival_service import RivalService
from app.services.running_style_service import RunningStyleService
from app.services.sequential_updater import SequentialUpdater

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml")


class MonteCarloSimulationRequest(BaseModel):
    """POST /ml/simulate 요청 본문입니다. Phase 3부터 Bayesian/Sequential/Copula 보정 옵션을 함께 받습니다."""

    race_id: int
    n_simulations: int = 70_000  # 4차 회의 확정: 70,000회 기본
    use_bayesian: bool = True
    use_sequential: bool = True
    use_copula: bool = True


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

    # 2. 학습/테스트 분리 (groups도 함께 분리)
    X_train, X_test, y_train, y_test, train_groups, test_groups = \
        dataset_svc.split_train_test(X, y, groups)

    # 3. 피처 전처리 (결측값 처리 + 정규화)
    X_train_s, X_test_s, scaler = dataset_svc.preprocess_features(X_train, X_test)

    # 4. 모델 학습 (CPU 집중 작업 → 별도 스레드에서 실행)
    # ── 순위 레이블 변환 ───────────────────────────────────────────────────────
    # Ranker는 "숫자가 높을수록 더 좋은 샘플"로 학습합니다.
    # 경마 착순은 1=1위(최고)이므로 그대로 넣으면 꼴찌를 1위로 예측하는 반전 발생.
    #
    # XGBoost: 음수(-rank) 허용 → -1=1위, -10=꼴찌
    # LightGBM lambdarank: 0~3 정수만 허용 (4단계 관련도 점수)
    #   rank 1    → 3 (최우수)
    #   rank 2~3  → 2 (우수)
    #   rank 4~6  → 1 (보통)
    #   rank 7이상 → 0 (하위)
    import numpy as np
    y_train_xgb = -y_train.values                         # XGBoost용: 음수 반전
    y_train_lgbm = np.where(y_train.values == 1, 3,
                   np.where(y_train.values <= 3, 2,
                   np.where(y_train.values <= 6, 1, 0))).astype(int)
    y_test_original = y_test.values                       # 평가용: 원래 순위

    try:
        if model_type.lower() == "lgbm":
            model = await asyncio.to_thread(
                trainer.train_lightgbm, X_train_s, y_train_lgbm, train_groups
            )
            model_name = "lgbm"
        else:
            model = await asyncio.to_thread(
                trainer.train_xgboost, X_train_s, y_train_xgb, train_groups
            )
            model_name = "xgboost"
    except Exception as exc:
        logger.error("[학습] 모델 학습 실패: %s", exc)
        raise HTTPException(status_code=500, detail=f"모델 학습 실패: {exc}")

    # 5. 테스트 데이터로 성능 평가 (원래 순위 레이블 사용)
    metrics = trainer.evaluate_model(
        model, X_test_s, y_test_original,
        groups=test_groups,
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


@router.post("/predict/{race_id}/ensemble")
async def predict_race_ensemble(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """XGBoost + LightGBM 앙상블 예측을 실행합니다.

    두 모델의 점수를 Min-Max 정규화 후 평균내어 더 안정적인 예측을 제공합니다.
    단일 모델보다 2·3위 예측 안정성이 높습니다.
    """
    predictor = PredictorService(db)
    try:
        results = await predictor.predict_race_ensemble(race_id)
        return {
            "success": True,
            "data": {
                "raceId":      race_id,
                "modelName":   "ensemble",
                "predictions": results,
            },
            "message": f"앙상블 예측 완료 ({len(results)}마리)",
        }
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error("[앙상블 예측] race_id=%d 실패: %s", race_id, exc)
        raise HTTPException(status_code=500, detail=str(exc))


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


@router.post("/simulate/{race_id}")
async def run_monte_carlo_simulation(
    race_id: int,
    n_simulations: int = 70_000,  # 4차 회의 확정: 70,000회 기본
    use_bayesian: bool = True,
    use_sequential: bool = True,
    use_copula: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """예측 확률을 여러 번 추첨해 각 말의 순위별 확률 분포를 계산합니다."""
    service = MonteCarloService(db)
    try:
        result = await service.run_simulation(
            race_id,
            n_simulations,
            use_bayesian=use_bayesian,
            use_sequential=use_sequential,
            use_copula=use_copula,
        )
        return {
            "success": True,
            "data": result,
            "message": "몬테카를로 시뮬레이션 완료",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/simulate")
async def run_monte_carlo_simulation_from_body(
    request: MonteCarloSimulationRequest,
    db: AsyncSession = Depends(get_db),
):
    """JSON body로 Monte Carlo 시뮬레이션을 실행합니다. prompt-30의 use_bayesian 옵션을 지원합니다."""
    service = MonteCarloService(db)
    try:
        result = await service.run_simulation(
            request.race_id,
            request.n_simulations,
            use_bayesian=request.use_bayesian,
            use_sequential=request.use_sequential,
            use_copula=request.use_copula,
        )
        return {
            "success": True,
            "data": result,
            "message": "Bayesian·Sequential·Copula Monte Carlo 시뮬레이션 완료",
        }
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/sequential/update")
async def update_sequential(
    rc_date: str,
    completed_race_no: int,
    db: AsyncSession = Depends(get_db),
):
    """경주 결과 수집 후 Redis에 당일 Sequential 정보를 저장하고 다음 경주 시뮬레이션을 갱신합니다.

    @param rc_date            경주 날짜 (예: 2026-06-07)
    @param completed_race_no  방금 끝난 경주 번호
    """
    updater = SequentialUpdater(db_session=db)
    result_data = await updater.load_completed_race_result(rc_date, completed_race_no)
    if result_data is None:
        raise HTTPException(status_code=404, detail="저장할 경주 결과를 찾을 수 없습니다.")

    await updater.store_race_result_async(rc_date, completed_race_no, result_data)
    next_race_id = await updater.find_next_race_id(rc_date, completed_race_no)
    simulation_result = None

    if next_race_id is not None:
        try:
            # 다음 경주 예측은 Bayesian prior 위에 Sequential prior를 한 번 더 적용합니다.
            # 예측 데이터가 아직 없으면 업데이트 API 자체가 실패하지 않도록 결과만 생략합니다.
            simulation_result = await MonteCarloService(db).run_simulation(
                next_race_id,
                use_bayesian=True,
                use_sequential=True,
                use_copula=True,
            )
        except ValueError:
            simulation_result = None

    return {
        "success": True,
        "data": {
            "rc_date": rc_date,
            "completed_race_no": completed_race_no,
            "next_race_id": next_race_id,
            "next_race_updated": simulation_result is not None,
            "simulation": simulation_result,
        },
        "message": "Sequential 업데이트 완료",
    }


@router.get("/sequential/status/{rc_date}")
async def get_sequential_status(rc_date: str):
    """오늘 Sequential 업데이트 현황을 조회합니다."""
    updater = SequentialUpdater()
    status = await updater.get_status_async(rc_date)
    return {
        "success": True,
        "data": status,
        "message": "Sequential 업데이트 현황 조회 성공",
    }


@router.get("/simulate/{race_id}/result")
async def get_monte_carlo_simulation_result(
    race_id: int,
    db: AsyncSession = Depends(get_db),
):
    """저장된 몬테카를로 시뮬레이션 결과를 조회합니다."""
    service = MonteCarloService(db)
    result = await service.get_simulation_result(race_id)
    if result is None:
        raise HTTPException(status_code=404, detail="저장된 시뮬레이션 결과가 없습니다.")
    return {
        "success": True,
        "data": result,
        "message": "몬테카를로 시뮬레이션 결과 조회 성공",
    }


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


# =============================================================================
# 라이벌 직접 대결 + 주행 스타일 엔드포인트
# =============================================================================

@router.post("/rivals/calculate")
async def calculate_rivals(db: AsyncSession = Depends(get_db)):
    """race_results 데이터 전체에서 말 간 직접 대결 이력을 배치 계산합니다.

    rival_records 테이블을 채웁니다.
    데이터가 많을수록 시간이 걸리므로 처음 1회만 실행하면 됩니다.
    이후 새 경주 결과 수집 후 주기적으로 실행하면 갱신됩니다.
    """
    svc = RivalService(db)
    try:
        result = await svc.calculate_all_rivals()
        return {"success": True, "data": result, "message": f"라이벌 대결 이력 {result['rival_pairs_saved']}쌍 저장 완료"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/running-style/calculate")
async def calculate_running_styles(db: AsyncSession = Depends(get_db)):
    """race_results + race_entries 데이터에서 말별 주행 스타일을 배치 분류합니다.

    horse_running_style 테이블을 채웁니다.
    게이트 번호와 착순의 상관관계로 LEADER/STALKER/CLOSER를 분류합니다.
    """
    svc = RunningStyleService(db)
    try:
        result = await svc.calculate_all_styles()
        return {"success": True, "data": result, "message": f"주행 스타일 {result['horses_classified']}마리 분류 완료"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/running-style/{race_id}")
async def get_race_running_styles(race_id: int, db: AsyncSession = Depends(get_db)):
    """특정 경주 출전마들의 주행 스타일을 조회합니다. FE 경주 분석 카드에서 사용합니다."""
    svc = RunningStyleService(db)
    result = await svc.get_race_style_summary(race_id)
    return {"success": True, "data": result, "message": f"{len(result)}마리 스타일 조회 성공"}


@router.get("/rivals/{horse_id_a}/{horse_id_b}")
async def get_head_to_head(horse_id_a: int, horse_id_b: int, db: AsyncSession = Depends(get_db)):
    """두 말의 직접 대결 통계를 조회합니다. FE 라이벌 대결 섹션에서 사용합니다."""
    svc = RivalService(db)
    result = await svc.get_h2h_stats(horse_id_a, horse_id_b)
    if not result:
        raise HTTPException(status_code=404, detail="직접 대결 이력이 없습니다.")
    return {"success": True, "data": result, "message": "직접 대결 통계 조회 성공"}


# =============================================================================
# Phase 3 — 변경사항 감지 API (prompt-33)
# =============================================================================

@router.post("/changes/detect")
async def trigger_change_detection(
    rc_date: str,
    race_no: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    변경사항 감지를 수동으로 트리거합니다.

    APScheduler가 30분마다 자동 실행하지만,
    관리자 또는 테스트 시 즉시 실행할 때 이 엔드포인트를 사용합니다.

    @param rc_date   경주 날짜 (YYYYMMDD 형식, 예: '20260607')
    @param race_no   특정 경주만 검사할 경우 지정 (없으면 전체 경주)
    """
    from app.services.change_detector import ChangeDetector
    from app.services.kra_api import KRAApiService

    kra = KRAApiService()
    try:
        detector = ChangeDetector(db, kra)
        changes = await detector.detect_all(rc_date=rc_date, race_no=race_no)

        return {
            "success": True,
            "data": {
                "rc_date": rc_date,
                "race_no": race_no,
                "total_changes": len(changes),
                # ChangeEvent를 dict로 변환해서 반환합니다.
                "changes": [
                    {
                        "type": c.type,
                        "badge": c.badge,
                        "impact": c.impact,
                        "race_id": c.race_id,
                        "horse_id": c.horse_id,
                        "old_value": c.old_value,
                        "new_value": c.new_value,
                        "detected_at": c.detected_at.isoformat(),
                    }
                    for c in changes
                ],
            },
            "message": f"변경감지 완료: {len(changes)}건",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        await kra.close()


@router.get("/changes/status/{rc_date}")
async def get_change_detection_status(rc_date: str):
    """
    오늘 변경감지 현황을 조회합니다.

    마지막 실행 시각과 감지 건수를 확인할 수 있습니다.
    관리자 패널 및 FE 상태 표시줄에서 사용합니다.
    """
    from app.core.redis_client import get_redis_client

    redis = get_redis_client()
    # 체크포인트 키에서 마지막 실행 시각을 조회합니다.
    last_run = await redis.get("kra:checkpoint:change_detection")

    return {
        "success": True,
        "data": {
            "rc_date": rc_date,
            "last_run": last_run,
            "schedule": "30분마다 (토/일/월 09:00~17:00)",
        },
        "message": "변경감지 현황 조회 성공",
    }
