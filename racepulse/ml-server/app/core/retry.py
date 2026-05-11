# -*- coding: utf-8 -*-
# =============================================================================
# retry.py — 지수 백오프(Exponential Backoff) 재시도 유틸리티
# =============================================================================
# 지수 백오프란?
#   API 호출이 실패했을 때 바로 재시도하지 않고, 점점 더 긴 시간을 기다렸다가 재시도합니다.
#   예: 1차 실패 → 5분 기다림 → 2차 실패 → 15분 기다림 → 3차 실패 → 30분 ...
#
#   왜 이렇게 하는가?
#   - 서버가 일시적으로 과부하 상태일 때, 즉시 재시도하면 오히려 더 나빠집니다.
#   - 기다렸다가 재시도하면 서버가 회복할 시간을 주고, 성공 가능성이 높아집니다.
#   - 마사회 API 서버가 점검 중이거나 네트워크가 불안정할 때 유용합니다.
# =============================================================================

# asyncio = 비동기 방식으로 대기 시간을 처리합니다.
import asyncio
# functools = 데코레이터를 만들 때 원래 함수의 이름/docstring을 유지하게 해줍니다.
import functools
# logging = 재시도 상태를 로그로 남기는 표준 라이브러리입니다.
import logging
# Any/Callable/TypeVar = 함수 타입 힌트에 사용합니다.
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# =============================================================================
# 재시도 간격 설정 (분 단위)
# =============================================================================
# RETRY_DELAYS = 각 재시도마다 기다릴 분 수 목록입니다.
# 5분 → 15분 → 30분 → 1시간 → 3시간 순서로 점점 길어집니다.
# 최대 5번 재시도합니다.
RETRY_DELAYS_MINUTES: list[int] = [5, 15, 30, 60, 180]

# 초 단위로 변환한 버전 (asyncio.sleep은 초 단위를 사용합니다)
RETRY_DELAYS_SECONDS: list[int] = [m * 60 for m in RETRY_DELAYS_MINUTES]

# 즉시 재시도 없이 기다리는 버전 (첫 시도는 대기 없이 바로 실행)
# (0, *RETRY_DELAYS_SECONDS) = 첫 시도 대기 0초, 이후 5분, 15분, 30분, 1시간, 3시간
RETRY_SEQUENCE: tuple[int, ...] = (0, *RETRY_DELAYS_SECONDS)

# TypeVar = 제네릭 타입 힌트 도구 (함수 반환 타입을 유연하게 표현할 때 사용)
F = TypeVar("F", bound=Callable[..., Any])


async def retry_with_backoff(
    func: Callable,
    *args: Any,
    max_attempts: int = len(RETRY_DELAYS_SECONDS) + 1,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    job_name: str = "",
    **kwargs: Any,
) -> Any:
    """지수 백오프 방식으로 비동기 함수를 재시도합니다.

    @param func         재시도할 비동기 함수
    @param args         함수 위치 인자
    @param max_attempts 최대 시도 횟수 (기본 6회: 초기 1회 + 재시도 5회)
    @param exceptions   재시도할 예외 타입 목록
    @param job_name     로그에 표시할 작업 이름
    @param kwargs       함수 키워드 인자
    @return 함수 실행 결과
    @raises 마지막 시도에서도 실패하면 예외를 그대로 전파합니다.

    사용 예시:
        result = await retry_with_backoff(
            some_api_call,
            meet_code="SC",
            job_name="결과 수집",
        )
    """
    last_error: Exception | None = None

    for attempt, delay in enumerate(RETRY_SEQUENCE[:max_attempts], start=1):
        # 첫 시도는 대기 없이 바로 실행하고, 이후 시도는 지정된 시간만큼 대기합니다.
        if delay > 0:
            delay_minutes = delay // 60
            logger.warning(
                "[%s] 재시도 %d/%d — %d분 후 재시도합니다.",
                job_name, attempt - 1, max_attempts - 1, delay_minutes
            )
            # asyncio.sleep = 지정한 초만큼 비동기로 대기합니다.
            # 일반 time.sleep과 달리 다른 작업이 계속 실행될 수 있습니다.
            await asyncio.sleep(delay)

        try:
            return await func(*args, **kwargs)
        except exceptions as error:
            last_error = error
            if attempt == max_attempts:
                # 마지막 시도에서도 실패하면 재시도를 중단하고 예외를 올립니다.
                logger.error(
                    "[%s] 최대 재시도 횟수(%d회) 초과. 마지막 오류: %s",
                    job_name, max_attempts, error
                )
                break
            logger.warning("[%s] 시도 %d 실패: %s", job_name, attempt, error)

    raise last_error  # type: ignore[misc]
