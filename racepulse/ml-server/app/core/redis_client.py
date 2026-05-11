# -*- coding: utf-8 -*-
# =============================================================================
# redis_client.py — Redis 연결 및 공통 유틸리티 서비스
# =============================================================================
# Redis(Remote Dictionary Server)란?
#   메모리에 데이터를 저장하는 초고속 저장소입니다.
#   DB보다 10~100배 빠르기 때문에 "자주 바뀌고 빨리 읽어야 하는 값"을 저장합니다.
#
# 이 파일에서 Redis를 쓰는 이유:
#   1. 마사회 API 일일 호출 횟수 카운터 → 초 단위 응답 필요
#   2. 수집 락(동시에 같은 작업이 두 번 실행되지 않게 막기)
#   3. 체크포인트 저장(중단된 수집을 어디서부터 이어야 하는지)
#   4. 날씨 데이터 캐시(매번 DB 조회 대신 Redis에서 빠르게 가져오기)
# =============================================================================

# logging = 서버 로그(정보/경고/오류)를 기록하는 표준 라이브러리입니다.
import logging
# datetime = 날짜 키 계산, 자정까지 남은 시간 계산에 사용합니다.
from datetime import date, datetime, time, timedelta
# Any = 다양한 타입을 허용하는 타입 힌트입니다.
from typing import Any, Optional

# Redis = 파이썬에서 Redis 서버에 비동기로 연결하는 클라이언트 클래스입니다.
from redis.asyncio import Redis

# settings = Redis 주소, KRA 호출 한도 같은 공통 설정을 읽기 위한 객체입니다.
from app.core.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# Redis 연결 싱글턴
# 싱글턴(Singleton)이란? 앱 전체에서 하나의 인스턴스만 공유하는 패턴입니다.
# Redis 연결을 매번 새로 만들면 자원 낭비가 심해지므로 하나만 만들어 재사용합니다.
# =============================================================================
_redis_client: Redis | None = None


def get_redis_client() -> Redis:
    """전역 Redis 클라이언트를 반환합니다. 없으면 새로 만듭니다."""
    global _redis_client

    if _redis_client is None:
        # decode_responses=True = Redis에서 받은 byte 값을 자동으로 문자열로 변환합니다.
        _redis_client = Redis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


async def close_redis_client() -> None:
    """앱 종료 시 Redis 연결을 정리합니다."""
    global _redis_client

    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None


# =============================================================================
# Rate Limit 카운터
# =============================================================================

def _daily_count_key(target_date: date | None = None) -> str:
    """날짜별 API 호출 횟수를 저장하는 Redis 키를 반환합니다.
    형식: kra:daily_count:YYYYMMDD (예: kra:daily_count:20260507)
    """
    d = target_date or datetime.now().date()
    return f"kra:daily_count:{d.strftime('%Y%m%d')}"


def _seconds_until_midnight() -> int:
    """현재 시각부터 자정까지 남은 초를 계산합니다.
    Redis TTL(만료 시간)을 자정으로 맞추어 카운터가 자동으로 리셋되게 합니다.
    """
    now = datetime.now()
    next_midnight = datetime.combine(now.date() + timedelta(days=1), time.min)
    return max(1, int((next_midnight - now).total_seconds()))


async def get_daily_call_count(target_date: date | None = None) -> int:
    """오늘 마사회 API를 몇 번 호출했는지 조회합니다."""
    redis = get_redis_client()
    raw = await redis.get(_daily_count_key(target_date))
    return int(raw or 0)


async def increment_daily_count(target_date: date | None = None) -> int:
    """마사회 API 호출 횟수를 1 증가시키고, 자정에 자동 리셋되도록 TTL을 설정합니다.

    incr = Redis 내장 원자적(atomic) 증가 명령어입니다.
    원자적이란? 동시에 여러 요청이 와도 숫자가 정확하게 1씩 증가합니다.
    """
    redis = get_redis_client()
    key = _daily_count_key(target_date)
    count = await redis.incr(key)
    # 처음 생성된 키에만 TTL을 설정합니다. (자정에 자동 삭제 = 자동 리셋)
    if count == 1:
        await redis.expire(key, _seconds_until_midnight())
    return int(count)


async def is_limit_reached(target_date: date | None = None) -> bool:
    """오늘 호출 횟수가 안전 중단 기준(2,800콜)을 넘었는지 확인합니다.

    일일 한도: 3,000콜
    중단 기준: 2,800콜 (200콜 안전 마진)
    """
    count = await get_daily_call_count(target_date)
    return count >= settings.kra_stop_threshold


async def reset_daily_counter(target_date: date | None = None) -> None:
    """지정한 날짜의 API 호출 카운터를 0으로 초기화합니다."""
    redis = get_redis_client()
    await redis.delete(_daily_count_key(target_date))
    logger.info("[Rate Limit] 일일 카운터 초기화 완료.")


# =============================================================================
# 체크포인트 관리
# =============================================================================
# 체크포인트(Checkpoint)란?
#   "마지막으로 수집이 완료된 시점"을 기록해두는 것입니다.
#   서버가 중간에 꺼지거나 Rate Limit으로 수집이 중단됐을 때,
#   다음 실행 시 처음부터 다시 하지 않고 중단 지점부터 이어서 할 수 있습니다.
# =============================================================================

def _checkpoint_key(job_name: str) -> str:
    """체크포인트 Redis 키를 반환합니다.
    형식: kra:checkpoint:{job_name} (예: kra:checkpoint:collect_weekend_results)
    """
    return f"kra:checkpoint:{job_name}"


async def set_checkpoint(job_name: str, value: str) -> None:
    """수집 완료 시점 또는 마지막으로 처리한 항목을 Redis에 저장합니다."""
    redis = get_redis_client()
    # 체크포인트는 7일간 보관 후 자동 삭제합니다.
    await redis.set(_checkpoint_key(job_name), value, ex=7 * 24 * 60 * 60)
    logger.debug("[체크포인트] %s = %s", job_name, value)


async def get_checkpoint(job_name: str) -> Optional[str]:
    """마지막 수집 완료 시점을 Redis에서 조회합니다. 없으면 None 반환."""
    redis = get_redis_client()
    return await redis.get(_checkpoint_key(job_name))


# =============================================================================
# 분산 락 (Distributed Lock)
# =============================================================================
# 분산 락이란?
#   스케줄러가 동시에 같은 작업을 두 번 실행하는 것을 막기 위한 장치입니다.
#   예: 서버를 두 대 띄웠을 때 "마사회 결과 수집"이 두 곳에서 동시에 실행되면
#   DB에 중복 데이터가 쌓이거나 API를 두 배로 호출합니다.
#   → 락을 먼저 잡은 쪽만 실행하고, 나머지는 "이미 실행 중"이라고 보고 건너뜁니다.
#
# Redis SETNX(SET if Not eXists) 명령으로 원자적으로 락을 획득합니다.
# TTL을 설정해두면 서버가 갑자기 죽어도 락이 자동으로 풀립니다.
# =============================================================================

def _lock_key(job_name: str) -> str:
    """락 Redis 키를 반환합니다.
    형식: kra:lock:{job_name} (예: kra:lock:collect_weekend_results)
    """
    return f"kra:lock:{job_name}"


async def acquire_lock(job_name: str, ttl_seconds: int = 3600) -> bool:
    """분산 락을 획득합니다.

    set(..., nx=True) = 키가 없을 때만 값을 저장하는 Redis 원자적 명령입니다.
    → 두 서버가 동시에 시도해도 딱 하나만 True를 받습니다.

    @param job_name     락 이름 (작업별로 고유해야 합니다)
    @param ttl_seconds  락 자동 만료 시간(초). 서버가 죽어도 이 시간 후 자동 해제.
    @return True = 락 획득 성공(작업 실행 가능), False = 이미 다른 프로세스가 실행 중
    """
    redis = get_redis_client()
    key = _lock_key(job_name)
    # nx=True = Not eXists, 키가 없을 때만 저장합니다 (원자적).
    # ex=ttl_seconds = ttl_seconds 초 후 자동 삭제합니다 (자동 락 해제).
    acquired = await redis.set(key, "locked", nx=True, ex=ttl_seconds)
    if acquired:
        logger.debug("[락 획득] %s (TTL=%ds)", job_name, ttl_seconds)
    else:
        logger.debug("[락 스킵] %s - 이미 실행 중", job_name)
    return bool(acquired)


async def release_lock(job_name: str) -> None:
    """분산 락을 수동으로 해제합니다. 작업 완료 후 반드시 호출해야 합니다."""
    redis = get_redis_client()
    await redis.delete(_lock_key(job_name))
    logger.debug("[락 해제] %s", job_name)


# =============================================================================
# 날씨 캐시
# =============================================================================

def _weather_cache_key(meet_code: str, target_date: str) -> str:
    """날씨 캐시 Redis 키를 반환합니다.
    형식: weather:cache:{meet_code}:{date} (예: weather:cache:SC:20260507)
    """
    return f"weather:cache:{meet_code}:{target_date}"


async def set_weather_cache(meet_code: str, target_date: str, value: str, ttl_seconds: int = 3600) -> None:
    """날씨 데이터를 Redis에 캐시합니다. 기본 TTL은 1시간(3600초)입니다."""
    redis = get_redis_client()
    await redis.set(_weather_cache_key(meet_code, target_date), value, ex=ttl_seconds)


async def get_weather_cache(meet_code: str, target_date: str) -> Optional[str]:
    """Redis에서 날씨 캐시를 조회합니다. 없으면 None 반환."""
    redis = get_redis_client()
    return await redis.get(_weather_cache_key(meet_code, target_date))
