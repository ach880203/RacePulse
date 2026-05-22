"""피처 계산 0개 원인 파악"""
import asyncio
import sys
sys.path.insert(0, '.')

async def main():
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import text

    async with AsyncSessionLocal() as db:
        # 1. race_entries 존재 여부 확인
        r = await db.execute(text(
            "SELECT COUNT(*) FROM race_entries WHERE race_id = 32191"
        ))
        cnt = r.scalar()
        print(f"race_entries (race_id=32191): {cnt}건")

        # 2. ml_feature_store 존재 여부
        r2 = await db.execute(text(
            "SELECT COUNT(*) FROM ml_feature_store WHERE race_id = 32191"
        ))
        cnt2 = r2.scalar()
        print(f"ml_feature_store (race_id=32191): {cnt2}건")

        # 3. race_entries 샘플
        r3 = await db.execute(text(
            "SELECT re.id, re.horse_id, re.jockey_id, re.gate_no "
            "FROM race_entries re WHERE re.race_id = 32191 LIMIT 3"
        ))
        rows = r3.fetchall()
        print(f"\nrace_entries 샘플:")
        for row in rows:
            print(f"  entry_id={row[0]} horse={row[1]} jockey={row[2]} gate={row[3]}")

        # 4. ml_feature_store 샘플 (있다면)
        r4 = await db.execute(text(
            "SELECT race_entry_id, feature_version, features::text "
            "FROM ml_feature_store WHERE race_id = 32191 LIMIT 1"
        ))
        fs = r4.fetchone()
        if fs:
            print(f"\nml_feature_store 샘플: entry={fs[0]} v={fs[1]}")
            print(f"  features: {str(fs[2])[:200]}")
        else:
            print("\nml_feature_store: 데이터 없음")

        # 5. 예측 오류 재현 - predictor 직접 실행
        from app.services.predictor import PredictorService
        import traceback
        try:
            svc = PredictorService(db)
            results = await svc.predict_race(32191)
            print(f"\n예측 성공: {len(results)}마리")
        except Exception as e:
            print(f"\n예측 오류:\n{traceback.format_exc()}")

asyncio.run(main())
