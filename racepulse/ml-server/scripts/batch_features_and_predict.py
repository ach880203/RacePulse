"""오늘·내일 전체 경주 피처 계산 + 예측 생성 배치 스크립트"""
import asyncio
import sys
import httpx

sys.path.insert(0, '.')

# 방금 조회한 race_id 목록
RACE_IDS = [
    # 5/23 JJ (1~7경주)
    32261, 32262, 32263, 32264, 32265, 32266, 32267,
    # 5/23 SC (1~10경주)
    32191, 32192, 32193, 32194, 32195, 32196, 32197, 32198, 32199, 32200,
    # 5/24 BU (1~7경주)
    32325, 32326, 32327, 32328, 32329, 32330, 32331,
    # 5/24 SC (1~10경주)
    32181, 32182, 32183, 32184, 32185, 32186, 32187, 32188, 32189, 32190,
]

ML_URL = "http://localhost:8000"

async def main():
    success_feat = 0
    fail_feat = 0
    success_pred = 0
    fail_pred = 0

    async with httpx.AsyncClient(timeout=120.0) as client:
        for race_id in RACE_IDS:
            # 1. 피처 계산
            try:
                r = await client.post(f"{ML_URL}/ml/features/calculate/{race_id}")
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    success_feat += 1
                    print(f"[FEAT OK] race_id={race_id} | {data.get('featuresCalculated',0)}개 피처")
                else:
                    fail_feat += 1
                    print(f"[FEAT !!] race_id={race_id} | {r.status_code} {r.text[:100]}")
            except Exception as e:
                fail_feat += 1
                print(f"[FEAT ERR] race_id={race_id} | {e}")

            await asyncio.sleep(0.5)

            # 2. 예측 생성
            try:
                r = await client.post(f"{ML_URL}/ml/predict/{race_id}")
                if r.status_code == 200:
                    data = r.json().get("data", {})
                    cnt = len(data.get("predictions", []))
                    success_pred += 1
                    print(f"[PRED OK] race_id={race_id} | {cnt}마리 예측")
                else:
                    fail_pred += 1
                    print(f"[PRED !!] race_id={race_id} | {r.status_code} {r.text[:100]}")
            except Exception as e:
                fail_pred += 1
                print(f"[PRED ERR] race_id={race_id} | {e}")

            await asyncio.sleep(0.5)

    print(f"\n=== 완료 ===")
    print(f"피처: 성공 {success_feat} / 실패 {fail_feat}")
    print(f"예측: 성공 {success_pred} / 실패 {fail_pred}")

asyncio.run(main())
