# -*- coding: utf-8 -*-
# =============================================================================
# nightly_pipeline.py — 야간 ML 파이프라인 자동화
# =============================================================================
# 실행 시각: 매일 05:00 (데이터 수집 03:00 완료 후 2시간 여유)
#
# 실행 순서:
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
    log.info("  피처: %s", feature_result)
    log.info("  라이벌: %s", rival_result)
    log.info("  스타일: %s", style_result)
    log.info("  FE빌드: %s", fe_result)
    log.info("  재학습: %s", train_result)
    log.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
