# -*- coding: utf-8 -*-
# =============================================================================
# admin.py — 스케줄러 상태 조회 및 수동 실행 관리자 API
# =============================================================================
# 이 파일은 운영 담당자가 수집 상태를 확인하고 수동으로 제어하기 위한 API입니다.
# 자동 스케줄이 있어도 초기 개발이나 장애 복구 시 "지금 바로 실행"이 필요합니다.
# =============================================================================

# logging = 서버 로그를 기록하는 표준 라이브러리입니다.
import logging
# date/datetime/timedelta = 날짜 기반 카운터 키와 수집 날짜 계산에 사용합니다.
from datetime import date, datetime, timedelta

# APIRouter = 관련 API들을 하나의 라우터 묶음으로 관리합니다.
from fastapi import APIRouter, HTTPException

# redis_client 모듈 — Rate Limit 카운터와 체크포인트를 조회합니다.
import app.core.redis_client as redis_svc
# settings = 일일 한도, 중단 기준 같은 설정값을 읽습니다.
from app.core.config import settings
# AsyncSessionLocal = DB 세션 팩토리입니다.
from app.core.database import AsyncSessionLocal
# DataService = KRA API 수집 서비스입니다.
from app.services.data_service import DataService
# KRAApiService = 마사회 API HTTP 클라이언트입니다.
from app.services.kra_api import KRAApiService
# WeatherApiService = 기상청 API 서비스입니다.
from app.services.weather_api import WeatherApiService
# CollectionScheduler = 스케줄러 인스턴스에 접근하기 위한 클래스입니다.
from app.scheduler.scheduler import CollectionScheduler, ALL_MEET_CODES

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin")

# =============================================================================
# 스케줄러 싱글턴
# =============================================================================
# 관리자 API에서 스케줄러 상태를 조회하기 위해 전역 인스턴스를 참조합니다.
# 실제 스케줄러 인스턴스는 main.py lifespan에서 생성됩니다.
# 여기서는 상태 조회 전용으로 별도 인스턴스를 만들어 사용합니다.
_scheduler_instance: CollectionScheduler | None = None


def get_scheduler() -> CollectionScheduler:
    """전역 스케줄러 인스턴스를 반환합니다. 없으면 새로 만듭니다."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = CollectionScheduler()
    return _scheduler_instance


# =============================================================================
# 수동 실행 가능한 작업 목록
# =============================================================================
# 프롬프트에서 job_name 으로 수동 실행을 요청하므로,
# 허용된 작업 이름을 딕셔너리로 관리합니다.
# 외부에서 임의의 함수를 실행하는 보안 취약점을 방지합니다.
RUNNABLE_JOBS: dict[str, str] = {
    "collect_weekend_results":         "주말 경주 결과 수집",
    "collect_monday_results":          "월요일 경주 결과 수집",
    "collect_initial_weekend_entries": "주말 출전표 초안 수집",
    "collect_updated_weekend_entries": "출전표 업데이트 수집",
    "collect_friday_final_entries":    "출전표 확정본 수집",
    "collect_daily_info":              "당일 출전 정보 수집",
    "collect_weekly":                  "주간 마스터 데이터 수집",
    "collect_monthly":                 "월간 마스터 데이터 수집",
    "collect_weather_short":           "단기예보 수집",
    "collect_weather_mid":             "중기예보 수집",
    "reset_daily_counter":             "일일 카운터 리셋",
}


# =============================================================================
# API 엔드포인트
# =============================================================================

@router.get("/scheduler/status")
async def get_scheduler_status():
    """현재 등록된 스케줄 목록과 각 작업의 다음 실행 시각을 반환합니다.

    완료 기준 1: GET /admin/scheduler/status → 전체 스케줄 목록 확인
    """
    scheduler = get_scheduler()

    # 스케줄러가 실행 중인지 확인
    is_running = scheduler.scheduler.running

    jobs_info = []
    if is_running:
        jobs_info = scheduler.get_jobs_info()
    else:
        # 스케줄러가 꺼져 있으면 등록된 작업 목록 정보를 정적으로 반환합니다.
        jobs_info = [
            {"id": job_id, "name": desc, "next_run": None}
            for job_id, desc in RUNNABLE_JOBS.items()
        ]

    return {
        "success": True,
        "data": {
            "schedulerRunning": is_running,
            "timezone": settings.scheduler_timezone,
            "totalJobs": len(jobs_info),
            "jobs": jobs_info,
        },
        "message": "스케줄러 상태 조회 성공",
    }


@router.get("/rate-limit/status")
async def get_rate_limit_status():
    """오늘 마사회 API 사용량과 남은 한도를 반환합니다.

    완료 기준 2: GET /admin/rate-limit/status → 오늘 API 사용량 조회
    """
    today = date.today()
    current_count = await redis_svc.get_daily_call_count(today)
    checkpoint_data = {}

    # 각 수집 작업의 마지막 완료 시각도 함께 반환합니다.
    for job_id in RUNNABLE_JOBS:
        checkpoint = await redis_svc.get_checkpoint(job_id)
        checkpoint_data[job_id] = checkpoint

    is_limited = current_count >= settings.kra_stop_threshold

    return {
        "success": True,
        "data": {
            "date": today.isoformat(),
            "callCount": current_count,
            "dailyLimit": settings.kra_daily_limit,
            "stopThreshold": settings.kra_stop_threshold,
            "remainingCalls": max(0, settings.kra_stop_threshold - current_count),
            "isLimitReached": is_limited,
            "usagePercent": round(current_count / settings.kra_stop_threshold * 100, 1),
            "lastCheckpoints": checkpoint_data,
        },
        "message": "Rate Limit 상태 조회 성공" if not is_limited else "⚠️ Rate Limit 도달 — 수집이 일시 중단됐습니다.",
    }


@router.post("/scheduler/run/{job_name}")
async def run_job_manually(job_name: str):
    """특정 수집 작업을 지금 바로 수동으로 실행합니다.

    완료 기준 3: POST /admin/scheduler/run/collect_weather_short → 수동 실행 성공

    @param job_name  실행할 작업 이름 (RUNNABLE_JOBS 목록에 있는 이름만 허용)
    """
    # 허용된 작업 목록에 없으면 400 오류를 반환합니다.
    # 이렇게 하면 임의의 함수 이름으로 악의적인 실행을 방지합니다.
    if job_name not in RUNNABLE_JOBS:
        raise HTTPException(
            status_code=400,
            detail=f"알 수 없는 작업입니다: {job_name}. 허용된 작업: {list(RUNNABLE_JOBS.keys())}",
        )

    job_desc = RUNNABLE_JOBS[job_name]
    logger.info("[수동 실행] %s (%s)", job_name, job_desc)

    # Rate Limit 초과 시 수동 실행도 차단합니다.
    if await redis_svc.is_limit_reached():
        count = await redis_svc.get_daily_call_count()
        raise HTTPException(
            status_code=429,
            detail=f"오늘 API 호출 한도({count}/{settings.kra_stop_threshold})에 도달했습니다. 자정 이후 다시 시도해주세요.",
        )

    # 작업별로 적절한 서비스를 호출합니다.
    result = await _dispatch_job(job_name)

    return {
        "success": True,
        "data": {
            "jobName": job_name,
            "jobDesc": job_desc,
            "executedAt": datetime.now().isoformat(),
            "result": result,
        },
        "message": f"'{job_desc}' 수동 실행 완료",
    }


async def _dispatch_job(job_name: str) -> dict:
    """job_name에 따라 적절한 수집 함수를 호출합니다.

    날씨 수집 작업은 WeatherApiService를 사용합니다.
    KRA 수집 작업은 DataService를 사용합니다.
    """
    # -----------------------------------------------------------------------
    # 날씨 수집
    # -----------------------------------------------------------------------
    if job_name == "collect_weather_short":
        results = {}
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                svc = WeatherApiService(session)
                try:
                    data = await svc.fetch_short_term_forecast(meet_code)
                    saved = await svc.save_forecast(meet_code, data)
                    results[meet_code] = {"status": "SUCCESS", "savedCount": saved}
                except Exception as exc:
                    results[meet_code] = {"status": "ERROR", "message": str(exc)}
                finally:
                    await svc.close()
        return results

    if job_name == "collect_weather_mid":
        results = {}
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                svc = WeatherApiService(session)
                try:
                    data = await svc.fetch_mid_term_forecast(meet_code)
                    saved = await svc.save_forecast(meet_code, data)
                    results[meet_code] = {"status": "SUCCESS", "savedCount": saved}
                except Exception as exc:
                    results[meet_code] = {"status": "ERROR", "message": str(exc)}
                finally:
                    await svc.close()
        return results

    # -----------------------------------------------------------------------
    # Rate Limit 카운터 리셋
    # -----------------------------------------------------------------------
    if job_name == "reset_daily_counter":
        await redis_svc.reset_daily_counter()
        return {"reset": True}

    # -----------------------------------------------------------------------
    # KRA 수집 작업 (날짜/경마장 코드 자동 결정)
    # -----------------------------------------------------------------------
    today = date.today()

    # 날짜 결정 로직
    if job_name == "collect_weekend_results":
        target_dates = [today - timedelta(days=2), today - timedelta(days=1)]
    elif job_name == "collect_monday_results":
        target_dates = [today - timedelta(days=1)]
    else:
        target_dates = [today]

    results = {}
    for target_date in target_dates:
        date_str = target_date.isoformat()
        results[date_str] = {}
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                kra = KRAApiService()
                try:
                    ds = DataService(session, kra)
                    if job_name in ("collect_weekend_results", "collect_monday_results"):
                        summary = await ds.collect_race_results(meet_code=meet_code, rc_date=target_date)
                    else:
                        summary = await ds.collect_entry_info(meet_code=meet_code, rc_date=target_date)
                    results[date_str][meet_code] = {
                        "status": summary.status,
                        "recordsCollected": summary.records_collected,
                    }
                except Exception as exc:
                    results[date_str][meet_code] = {"status": "ERROR", "message": str(exc)}
                finally:
                    await kra.close()

    return results
