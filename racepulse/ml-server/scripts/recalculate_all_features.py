# -*- coding: utf-8 -*-
# =============================================================================
# recalculate_all_features.py — 전체 피처 강제 재계산
# =============================================================================
# calculate_features_only.py는 피처가 없는 경주만 처리합니다.
# 이 스크립트는 피처가 이미 있어도 전부 재계산합니다.
# 라이벌 피처 / 주행 스타일 피처 추가 후 반드시 실행하세요.
# =============================================================================

import httpx
import asyncio
import asyncpg

API_BASE = "http://localhost:8000"
DB_URL   = "postgresql://racepulse:racepulse_dev@localhost:5432/racepulse"


async def main():
    conn = await asyncpg.connect(DB_URL)
    try:
        # 결과가 있는 완료 경주 전체 조회 (피처 유무 무관)
        race_ids = await conn.fetch("""
            SELECT DISTINCT r.id, r.meet_code, r.rc_date, r.race_no
            FROM races r
            WHERE r.rc_date < CURRENT_DATE
              AND EXISTS (
                SELECT 1 FROM race_results rr
                JOIN race_entries re ON rr.race_entry_id = re.id
                WHERE re.race_id = r.id
              )
            ORDER BY r.rc_date DESC
        """)
    finally:
        await conn.close()

    total = len(race_ids)
    print(f"[START] 재계산 대상: {total}경주 (라이벌 + 주행스타일 포함)")

    ok = 0
    fail = 0

    async with httpx.AsyncClient() as client:
        for i, row in enumerate(race_ids, 1):
            race_id   = row["id"]
            meet_code = row["meet_code"]
            rc_date   = row["rc_date"].strftime("%Y-%m-%d")
            race_no   = row["race_no"]

            try:
                resp = await client.post(
                    f"{API_BASE}/ml/features/calculate/{race_id}",
                    timeout=120,
                )
                data      = resp.json()["data"]
                processed = data.get("processed", 0)
                errors    = data.get("errors", 0)

                if processed > 0:
                    print(f"  [{i}/{total}] [OK] {meet_code} {rc_date} {race_no}R -- {processed}마리")
                    ok += 1
                else:
                    print(f"  [{i}/{total}] [FAIL] {meet_code} {rc_date} {race_no}R -- 에러 {errors}건")
                    fail += 1
            except Exception as e:
                print(f"  [{i}/{total}] [ERR] {meet_code} {rc_date} {race_no}R -- {e}")
                fail += 1

            await asyncio.sleep(0.2)

    print(f"\n[DONE] 성공: {ok}경주 / 실패: {fail}경주")
    print("다음: POST /ml/train 으로 v2.0 재학습 실행")


if __name__ == "__main__":
    asyncio.run(main())
