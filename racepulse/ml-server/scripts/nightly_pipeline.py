# -*- coding: utf-8 -*-
# =============================================================================
# nightly_pipeline.py — 야간 ML 파이프라인 자동화
# =============================================================================
# 실행 시각: 매일 05:00 (데이터 수집 03:00 완료 후 2시간 여유)
#
# 실행 순서:
#   Phase 0 (순차): 최근 14일 누락 경주 결과 재수집
#   Phase 1 (병렬): 피처 재계산 + 라이벌 갱신 + 주행스타일 갱신 + FE 빌드
#   Phase 2 (순차): XGBoost 재학습 → LightGBM 재학습
#
# 전제 조건:
#   - FastAPI 서버가 localhost:8000에서 실행 중
#   - 프론트엔드: C:\Programmer\Work\horse racing\racepulse\frontend
# =============================================================================

import asyncio
import httpx
import asyncpg
import subprocess
import logging
import sys
from datetime import datetime, date
from pathlib import Path

# 로그 파일 저장 위치
LOG_FILE = Path(__file__).parent / "nightly_log.txt"
API_BASE = "http://localhost:8000"
DB_URL   = "postgresql://racepulse:racepulse_dev@localhost:5432/racepulse"
# parents[2] = racepulse/ 디렉터리, 그 아래 frontend/ 가 실제 경로입니다.
# (scripts → ml-server → racepulse → frontend)
FRONTEND = Path(__file__).parents[2] / "frontend"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# =============================================================================
# Phase 0: 누락된 경주 결과 재수집
# =============================================================================

async def collect_missing_results(client: httpx.AsyncClient) -> dict:
    """최근 14일 완료 경주 중 race_results가 비어 있는 날짜의 결과를 다시 수집합니다."""
    log.info("[결과재수집] 최근 14일 누락 결과 확인 시작")

    conn = None
    try:
        conn = await asyncpg.connect(DB_URL)
        # 새벽 수집 시점에 KRA 결과가 아직 없던 날짜를 다시 찾기 위해 DB 기준으로 누락 날짜만 조회합니다.
        missing_targets = await conn.fetch("""
            SELECT DISTINCT r.meet_code, r.rc_date
            FROM races r
            WHERE r.rc_date >= CURRENT_DATE - INTERVAL '14 days'
              AND r.rc_date < CURRENT_DATE
              AND NOT EXISTS (
                SELECT 1 FROM race_results rr
                JOIN race_entries re ON rr.race_entry_id = re.id
                WHERE re.race_id = r.id
              )
            ORDER BY r.rc_date DESC
        """)
    except Exception as e:
        log.error("[결과재수집] 누락 대상 조회 실패: %s", e)
        return {"collected": 0, "skipped": 0, "error": str(e)}
    finally:
        if conn is not None:
            await conn.close()

    if not missing_targets:
        log.info("[결과재수집] 재수집할 누락 결과 없음 — 건너뜀")
        return {"collected": 0, "skipped": 0}

    collected = 0
    skipped = 0

    log.info("[결과재수집] 대상 %d건 수집 시작", len(missing_targets))

    for row in missing_targets:
        meet_code = row["meet_code"]
        rc_date = row["rc_date"]
        target_date = rc_date.isoformat() if hasattr(rc_date, "isoformat") else str(rc_date)

        try:
            # 결과 수집은 KRA 일일 한도가 있으므로 날짜별로 순차 호출해 SKIPPED 응답을 즉시 감지합니다.
            resp = await client.post(
                f"{API_BASE}/collection/test",
                json={
                    "collection_type": "results",
                    "meet_code": meet_code,
                    "target_date": target_date,
                },
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            status = data.get("status")
            records_collected = int(data.get("recordsCollected") or 0)

            if status == "SKIPPED":
                skipped += 1
                log.warning(
                    "[결과재수집] KRA API 한도 초과로 중단 — %s %s",
                    meet_code,
                    target_date,
                )
                break

            if status == "SUCCESS":
                collected += records_collected
                log.info(
                    "[결과재수집] 완료 — %s %s, %d건",
                    meet_code,
                    target_date,
                    records_collected,
                )
            else:
                skipped += 1
                log.warning(
                    "[결과재수집] 건너뜀 — %s %s, status=%s",
                    meet_code,
                    target_date,
                    status,
                )
        except Exception as e:
            skipped += 1
            # 한 날짜 실패가 전체 야간 파이프라인을 막지 않도록 실패한 대상만 기록하고 다음 대상으로 넘어갑니다.
            log.error("[결과재수집] 실패 — %s %s: %s", meet_code, target_date, e)

        await asyncio.sleep(0.5)  # KRA/API 서버에 짧은 간격을 둬 불필요한 연속 부하를 줄입니다.

    log.info("[결과재수집] 완료 — 수집: %d건, 건너뜀: %d건", collected, skipped)
    return {"collected": collected, "skipped": skipped}


# =============================================================================
# 주간 마스터 데이터 동기화 (매주 월요일)
# =============================================================================

async def sync_master_data(client: httpx.AsyncClient) -> dict:
    """매주 월요일에 기수·조교사·말 마스터 데이터를 전체 동기화합니다.

    자동 파이프라인에서 호출되지 않아 null 상태인 birth_year·win_rate·
    father_name·color 등을 채우기 위해 Admin API를 통해 월 1회 전체 갱신합니다.
    KRA API 일일 한도(2,800콜) 소진 위험이 있으므로 월요일에만 실행합니다.
    """
    log.info("[마스터동기화] 주간 마스터 데이터 동기화 시작")

    MEET_CODES = ["SC", "BU", "JJ"]

    # 호출 순서: 기수 → 조교사 → 말 기본 → 말 상세 → 기수성적 → 말종합(부마명/모색)
    # collect_horse_total_info는 API 호출량이 많으므로 맨 마지막에 실행합니다.
    MASTER_JOBS = [
        "collect_master_jockeys",
        "collect_master_trainers",
        "collect_master_horses",
        "collect_horse_details",
        "collect_jockey_results",
        "collect_horse_total_info",
    ]

    results = {}

    for job_name in MASTER_JOBS:
        results[job_name] = {}
        for meet_code in MEET_CODES:
            try:
                resp = await client.post(
                    f"{API_BASE}/admin/scheduler/run/{job_name}",
                    json={"meet_code": meet_code},
                    timeout=300,
                )
                resp.raise_for_status()
                # Admin API 응답 구조: {"data": {"result": {meet_code: {...}}}}
                job_result = resp.json().get("data", {}).get("result", {}).get(meet_code, {})
                status = job_result.get("status", "UNKNOWN")
                records = int(job_result.get("recordsCollected") or 0)

                if status == "SKIPPED":
                    # KRA API 한도 초과 시 해당 경마장 이후를 건너뛰되, 다음 job은 계속 시도합니다.
                    log.warning("[마스터동기화] KRA API 한도 초과 — %s %s 건너뜀", job_name, meet_code)
                    results[job_name][meet_code] = {"status": "SKIPPED"}
                    continue

                results[job_name][meet_code] = {"status": status, "records": records}
                log.info("[마스터동기화] %s %s — %s, %d건", job_name, meet_code, status, records)

            except Exception as e:
                # 한 경마장 실패가 전체 마스터 동기화를 멈추지 않도록 실패만 기록하고 계속합니다.
                results[job_name][meet_code] = {"status": "ERROR", "error": str(e)}
                log.error("[마스터동기화] 실패 — %s %s: %s", job_name, meet_code, e)

            await asyncio.sleep(0.5)  # 연속 호출 간격 조절로 서버 부하를 줄입니다.

    log.info("[마스터동기화] 완료 — %d개 작업", len(MASTER_JOBS))
    return results


# =============================================================================
# Phase 1-A: 신규 경주 피처 재계산 (병렬 4개 동시)
# =============================================================================

async def calculate_new_features(client: httpx.AsyncClient) -> dict:
    """오늘 새로 수집된 경주의 피처를 계산합니다."""
    conn = await asyncpg.connect(DB_URL)
    try:
        # 결과는 있지만 피처가 없는 경주만 대상 (오늘 수집된 신규 데이터)
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
        log.info("[피처] 신규 계산할 경주 없음 — 건너뜀")
        return {"processed": 0, "skipped": True}

    log.info("[피처] 신규 %d경주 병렬 계산 시작", len(race_ids))

    # 4개씩 동시에 처리 (서버 부하 조절)
    ok = 0
    fail = 0
    BATCH = 4

    for i in range(0, len(race_ids), BATCH):
        batch = race_ids[i:i + BATCH]
        tasks = [
            client.post(f"{API_BASE}/ml/features/calculate/{row['id']}", timeout=120)
            for row in batch
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                fail += 1
            elif result.json().get("data", {}).get("processed", 0) > 0:
                ok += 1
            else:
                fail += 1

        await asyncio.sleep(0.5)  # 배치 간 서버 부하 조절

    log.info("[피처] 완료 — 성공: %d경주, 실패: %d경주", ok, fail)
    return {"processed": ok, "failed": fail}


# =============================================================================
# Phase 1-B: 라이벌 기록 갱신
# =============================================================================

async def update_rivals(client: httpx.AsyncClient) -> dict:
    """새로 추가된 경주 결과로 라이벌 대결 이력을 갱신합니다."""
    log.info("[라이벌] 갱신 시작")
    try:
        resp = await client.post(f"{API_BASE}/ml/rivals/calculate", timeout=300)
        data = resp.json()["data"]
        log.info("[라이벌] 완료 — %d쌍", data["rival_pairs_saved"])
        return data
    except Exception as e:
        log.error("[라이벌] 실패: %s", e)
        return {"error": str(e)}


# =============================================================================
# Phase 1-C: 주행 스타일 갱신
# =============================================================================

async def update_running_styles(client: httpx.AsyncClient) -> dict:
    """새 데이터로 주행 스타일을 재분류합니다."""
    log.info("[주행스타일] 갱신 시작")
    try:
        resp = await client.post(f"{API_BASE}/ml/running-style/calculate", timeout=300)
        data = resp.json()["data"]
        log.info("[주행스타일] 완료 — %d마리", data["horses_classified"])
        return data
    except Exception as e:
        log.error("[주행스타일] 실패: %s", e)
        return {"error": str(e)}


# =============================================================================
# Phase 1-D: FE 빌드 검증 (독립적 — 병렬 실행)
# =============================================================================

async def verify_fe_build() -> dict:
    """프론트엔드 빌드가 정상인지 확인합니다."""
    log.info("[FE빌드] npm run build 시작")
    # Task Scheduler 환경에서는 PATH가 제한되므로 npm 전체 경로를 지정합니다.
    # npm.cmd = Windows에서 npm을 실행하는 배치 파일입니다.
    npm_candidates = [
        r"C:\Program Files\nodejs\npm.cmd",
        r"C:\Program Files (x86)\nodejs\npm.cmd",
        r"C:\Users\ach88\AppData\Roaming\npm\npm.cmd",
    ]
    npm_path = next((p for p in npm_candidates if Path(p).exists()), None)
    if npm_path is None:
        log.error("[FE빌드] npm을 찾을 수 없습니다.")
        return {"success": False, "error": "npm not found"}

    try:
        proc = await asyncio.create_subprocess_exec(
            npm_path, "run", "build",
            cwd=str(FRONTEND),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

        if proc.returncode == 0:
            log.info("[FE빌드] 성공")
            return {"success": True}
        else:
            log.error("[FE빌드] 실패:\n%s", stderr.decode("utf-8", errors="replace")[-500:])
            return {"success": False, "error": stderr.decode("utf-8", errors="replace")[-200:]}
    except Exception as e:
        log.error("[FE빌드] 예외: %s", e)
        return {"success": False, "error": str(e)}


# =============================================================================
# Phase 2: 모델 재학습 (XGBoost + LightGBM 동시)
# =============================================================================

async def retrain_models(client: httpx.AsyncClient) -> dict:
    """XGBoost와 LightGBM을 동시에 재학습합니다."""
    today = date.today().strftime("%Y-%m-%d")
    log.info("[재학습] XGBoost + LightGBM 동시 학습 시작")

    async def train(model_type: str):
        try:
            resp = await client.post(
                f"{API_BASE}/ml/train",
                params={
                    "model_type":  model_type,
                    "start_date":  "2025-01-01",
                    "end_date":    today,
                    "version":     "v2.0",
                },
                timeout=1800,  # 최대 30분
            )
            data = resp.json()["data"]
            metrics = data.get("metrics", {})
            log.info(
                "[재학습] %s 완료 — Top-1: %.1f%%, Top-3: %.1f%%",
                model_type,
                metrics.get("top1_accuracy", 0),
                metrics.get("top3_accuracy", 0),
            )
            return {"model": model_type, "metrics": metrics}
        except Exception as e:
            log.error("[재학습] %s 실패: %s", model_type, e)
            return {"model": model_type, "error": str(e)}

    # XGBoost와 LightGBM 동시 학습
    results = await asyncio.gather(
        train("xgboost"),
        train("lgbm"),
    )
    return {"xgboost": results[0], "lgbm": results[1]}


# =============================================================================
# 메인
# =============================================================================

async def main():
    log.info("=" * 60)
    log.info("야간 ML 파이프라인 시작 — %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("=" * 60)

    # FastAPI 서버 확인
    async with httpx.AsyncClient() as client:
        try:
            await client.get(f"{API_BASE}/health", timeout=5)
        except Exception:
            log.error("FastAPI 서버 미실행 — 파이프라인 중단")
            return

        # ─── Phase 0: 누락 경주 결과 재수집 ───────────────────────────────
        log.info("\n[Phase 0] 최근 누락 경주 결과 재수집")
        collect_result = await collect_missing_results(client)

        # ─── 주간 마스터 동기화 (월요일만) ──────────────────────────────
        # 월요일(weekday=0)에만 실행: KRA API 호출량이 많아 매일 실행하면 한도 초과 위험이 있습니다.
        master_result = None
        if datetime.now().weekday() == 0:
            log.info("\n[주간동기화] 월요일 — 마스터 데이터 전체 동기화 실행")
            master_result = await sync_master_data(client)
        else:
            log.info("[주간동기화] 오늘은 월요일이 아님 — 건너뜀")

        # ─── Phase 1: 병렬 실행 ───────────────────────────────────────────
        log.info("\n[Phase 1] 피처재계산 + 라이벌 + 스타일 + FE빌드 병렬 실행")

        phase1_results = await asyncio.gather(
            calculate_new_features(client),   # 신규 피처 계산
            update_rivals(client),            # 라이벌 갱신
            update_running_styles(client),    # 스타일 갱신
            verify_fe_build(),                # FE 빌드 검증 (독립)
            return_exceptions=True,
        )

        feature_result, rival_result, style_result, fe_result = phase1_results

        # 피처 계산이 실패하면 재학습 의미 없음
        if isinstance(feature_result, Exception):
            log.error("피처 계산 예외 — 재학습 건너뜀: %s", feature_result)
            return

        # ─── Phase 2: 모델 재학습 ────────────────────────────────────────
        log.info("\n[Phase 2] 모델 재학습 시작")
        train_result = await retrain_models(client)

    # ─── 결과 요약 ──────────────────────────────────────────────────────
    log.info("\n" + "=" * 60)
    log.info("야간 파이프라인 완료 — %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("  결과재수집: %s", collect_result)
    if master_result is not None:
        log.info("  마스터동기화: %d개 작업 완료", len(master_result))
    log.info("  피처: %s", feature_result)
    log.info("  라이벌: %s", rival_result)
    log.info("  스타일: %s", style_result)
    log.info("  FE빌드: %s", fe_result)
    log.info("  재학습: %s", train_result)
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
