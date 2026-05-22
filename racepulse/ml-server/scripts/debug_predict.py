"""예측 오류 원인 파악 및 전체 배치 처리 스크립트"""
import asyncio
import sys
import traceback
sys.path.insert(0, '.')

async def main():
    from app.core.database import AsyncSessionLocal
    from app.services.predictor import PredictorService
    from app.services.feature_engineering import FeatureEngineeringService, FEATURE_COLUMNS

    # 오류 원인 파악
    async with AsyncSessionLocal() as db:
        # 피처 계산
        feat_svc = FeatureEngineeringService(db)
        feat_result = await feat_svc.calculate_features_for_race(32191)
        print(f"피처 계산 결과: {feat_result}")
        print(f"FEATURE_COLUMNS 수: {len(FEATURE_COLUMNS)}")
        print(f"FEATURE_COLUMNS: {FEATURE_COLUMNS[:5]}...")

        # 예측 시도
        try:
            predictor = PredictorService(db)
            result = await predictor.predict_race(32191)
            print(f"예측 성공: {len(result)}마리")
        except Exception as e:
            print(f"\n예측 오류:\n{traceback.format_exc()}")

asyncio.run(main())
