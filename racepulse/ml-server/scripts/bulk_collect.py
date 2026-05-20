# -*- coding: utf-8 -*-
# =============================================================================
# bulk_collect.py — 과거 데이터 일괄 수집 스크립트
# =============================================================================
# 사용법:
#   cd racepulse/ml-server
#   .\venv\Scripts\python.exe scripts/bulk_collect.py
#
# 이 스크립트가 하는 일:
#   1. 지정한 월 범위의 경주 일정(schedule)을 수집합니다.
#   2. DB에 저장된 과거 경주 날짜별로 결과(results)를 수집합니다.
#   3. 모든 완료 경주의 피처를 일괄 계산합니다.
#
# 주의:
#   - FastAPI 서버가 localhost:8000에서 실행 중이어야 합니다.
#   - KRA API 일일 한도 3,000콜을 초과하면 자동 중단됩니다.
# =============================================================================

import httpx
import asyncio
import asyncpg
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

# ── 설정 ────────────────────────────────────────────────────────────────────
API_BASE   = "http://localhost:8000"   # FastAPI 주소
DB_URL     = "postgresql://racepulse:racepulse_dev@localhost:5432/racepulse"
MEET_CODES = ["SC", "BU", "JJ"]       # 서울 / 부산경남 / 제주

# 수집할 월 범위 (이 범위의 경주 일정을 먼저 수집합니다)
START_MONTH = date(2021, 1, 1)   # 시작 월
END_MONTH   = date(2024, 12, 1)  # 종료 월 (2025년 이후는 이미 수집됨)

# API 호출 사이 대기 시간 (초) — 서버 부담 줄이기
CALL_DELAY = 1.0

# ── 유틸리티 ─────────────────────────────────────────────────────────────────

async def get_daily_call_count(client: httpx.AsyncClient) -> int:
    """오늘 이미 사용한 API 호출 수를 조회합니다."""
    resp = await client.get(f"{API_BASE}/collection/status")
    return resp.json()["data"]["daily_call_count"]


def month_range(start: date, end: date):
    """start 월부터 end 월까지 월 단위로 순회합니다."""
    cur = start.replace(day=1)
    while cur <= end.replace(day=1):
        yield cur
        cur += relativedelta(months=1)


# ── Step 1: 경주 일정 수집 ───────────────────────────────────────────────────

async def collect_schedules(client: httpx.AsyncClient):
    """지정한 월 범위의 경주 일정을 수집합니다."""
    print("\n" + "="*60)
    print("Step 1: 경주 일정 수집")
    print("="*60)

    for month in month_range(START_MONTH, END_MONTH):
        rc_month = month.strftime("%Y%m")
        print(f"\n  [{rc_month}] 수집 중...", end=" ")

        resp = await client.post(
            f"{API_BASE}/collection/test",
            json={
                "collection_type": "schedule",
                "rc_year":  month.year,
                "rc_month": rc_month,
            },
            timeout=120,
        )
        data = resp.json()["data"]
        status = data.get("status", "UNKNOWN")
        count  = data.get("recordsCollected", 0)
        calls  = data.get("dailyCallCount", 0)
        print(f"{status} | {count}건 | 오늘 호출 {calls}회")

        if status == "SKIPPED":
            print("  ⚠️  일일 한도 도달 — 내일 다시 실행하세요.")
            return False

        await asyncio.sleep(CALL_DELAY)

    return True


# ── Step 2: 경주 결과 수집 ───────────────────────────────────────────────────

async def collect_results(client: httpx.AsyncClient):
    """DB에 있는 모든 과거 날짜의 경주 결과를 수집합니다."""
    print("\n" + "="*60)
    print("Step 2: 경주 결과 수집")
    print("="*60)

    # DB에서 결과가 없는 (meet_code, rc_date) 목록 조회
    conn = await asyncpg.connect(DB_URL)
    try:
        rows = await conn.fetch("""
            SELECT DISTINCT r.meet_code, r.rc_date
            FROM races r
            WHERE r.rc_date < CURRENT_DATE
              AND NOT EXISTS (
                SELECT 1 FROM race_results rr
                JOIN race_entries re ON rr.race_entry_id = re.id
                WHERE re.race_id = r.id
              )
            ORDER BY r.rc_date DESC
        """)
    finally:
        await conn.close()

    if not rows:
        print("  ✅ 수집할 결과가 없습니다 (이미 전부 수집됨).")
        return True

    print(f"  수집 대상: {len(rows)}건 (meet_code, rc_date 조합)")

    for row in rows:
        meet_code = row["meet_code"]
        rc_date   = row["rc_date"].strftime("%Y-%m-%d")
        print(f"\n  [{meet_code} {rc_date}] 결과 수집 중...", end=" ")

        # KRA API 응답이 느린 경우를 대비해 타임아웃을 넉넉히 설정합니다.
        resp = await client.post(
            f"{API_BASE}/collection/test",
            json={
                "collection_type": "results",
                "meet_code":   meet_code,
                "target_date": rc_date,
            },
            timeout=120,
        )
        data   = resp.json()["data"]
        status = data.get("status", "UNKNOWN")
        count  = data.get("recordsCollected", 0)
        calls  = data.get("dailyCallCount", 0)
        quality = data.get("qualityStatus", "-")
        print(f"{status} | {count}건 | 품질 {quality} | 오늘 호출 {calls}회")

        if status == "SKIPPED":
            print("  ⚠️  일일 한도 도달 — 내일 다시 실행하세요.")
            return False

        await asyncio.sleep(CALL_DELAY)

    return True


# ── Step 3: 피처 일괄 계산 ───────────────────────────────────────────────────

async def calculate_features(client: httpx.AsyncClient):
    """결과가 수집된 모든 경주의 피처를 일괄 계산합니다."""
    print("\n" + "="*60)
    print("Step 3: 피처 일괄 계산 (API 호출 없음)")
    print("="*60)

    # 결과가 있는 완료 경주 ID 목록 조회
    conn = await asyncpg.connect(DB_URL)
    try:
        race_ids = await conn.fetch("""
            SELECT DISTINCT r.id, r.meet_code, r.rc_date, r.race_no
            FROM races r
            WHERE r.rc_date < CURRENT_DATE
              AND EXISTS (
                SELECT 1 FROM race_results rr
                JOIN race_entries re ON rr.race_entry_id = re.id
                WHERE re.race_id = r.id
              )
              AND NOT EXISTS (
                SELECT 1 FROM ml_feature_store fs
                JOIN race_entries re ON fs.race_entry_id = re.id
                WHERE re.race_id = r.id
              )
            ORDER BY r.rc_date DESC
        """)
    finally:
        await conn.close()

    if not race_ids:
        print("  [OK] 피처 계산할 경주가 없습니다 (이미 전부 계산됨).")
        return

    print(f"  계산 대상: {len(race_ids)}경주")

    ok = 0
    fail = 0
    for row in race_ids:
        race_id   = row["id"]
        meet_code = row["meet_code"]
        rc_date   = row["rc_date"].strftime("%Y-%m-%d")
        race_no   = row["race_no"]

        resp = await client.post(
            f"{API_BASE}/ml/features/calculate/{race_id}",
            timeout=120,
        )
        data      = resp.json()["data"]
        processed = data.get("processed", 0)
        errors    = data.get("errors", 0)

        if processed > 0:
            print(f"  [OK] [{meet_code} {rc_date} {race_no}R] {processed}마리 완료")
            ok += 1
        else:
            print(f"  [FAIL] [{meet_code} {rc_date} {race_no}R] 실패 (에러 {errors}건)")
            fail += 1

        await asyncio.sleep(0.3)

    print(f"\n  피처 계산 완료: 성공 {ok}경주 / 실패 {fail}경주")


# ── 메인 ─────────────────────────────────────────────────────────────────────

async def main():
    print("=" * 60)
    print("RacePulse 과거 데이터 일괄 수집 스크립트")
    print(f"수집 기간: {START_MONTH.strftime('%Y-%m')} ~ {END_MONTH.strftime('%Y-%m')}")
    print("=" * 60)

    async with httpx.AsyncClient() as client:
        # 현재 호출 수 확인
        calls = await get_daily_call_count(client)
        print(f"\n오늘 사용한 API 호출 수: {calls} / 2800 (안전 한도)")
        if calls >= 2800:
            print("⚠️  오늘 API 호출 한도에 도달했습니다. 내일 다시 실행하세요.")
            return

        # Step 1: 일정 수집
        ok = await collect_schedules(client)
        if not ok:
            return

        # Step 2: 결과 수집
        ok = await collect_results(client)
        if not ok:
            print("\n⚠️  한도 도달로 중단. 내일 다시 실행하면 이어서 수집됩니다.")

        # Step 3: 피처 계산 (API 호출 없으므로 항상 실행)
        await calculate_features(client)

    print("\n" + "="*60)
    print("완료!")
    print("다음 단계: POST /ml/train 으로 모델 학습을 실행하세요.")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
