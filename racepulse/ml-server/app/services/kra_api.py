# -*- coding: utf-8 -*-
# =============================================================================
# kra_api.py — 한국마사회 공공데이터 API 호출 전담 서비스
# =============================================================================
# 이 파일의 역할:
# 1) KRA API 주소와 파라미터를 한 곳에 모읍니다.
# 2) Redis로 오늘 호출 횟수를 세어 Rate Limit을 안전하게 지킵니다.
# 3) 재시도(지수 백오프)를 공통으로 처리해 라우터/저장 로직을 단순하게 만듭니다.
# =============================================================================

# asyncio = 재시도 대기 시간을 비동기 방식으로 기다릴 때 사용합니다.
import asyncio
# datetime/date/time/timedelta = 일일 카운트 키, 자정 만료 시각 계산에 사용합니다.
from datetime import date, datetime, time, timedelta
# Any = 다양한 응답 JSON 구조를 타입 힌트로 다룰 때 쓰는 범용 타입입니다.
from typing import Any

# httpx = 비동기 HTTP 요청을 보내는 라이브러리입니다.
import httpx
# Redis = Redis 서버와 비동기로 통신하는 클라이언트 타입입니다.
from redis.asyncio import Redis

# settings = API 키, 재시도 시간, 일일 제한 수치 같은 공통 설정값입니다.
from app.core.config import settings
# get_redis_client = Redis 연결을 재사용하기 위한 공통 함수입니다.
from app.core.redis_client import get_redis_client


class KRAApiError(Exception):
    # 외부 API 호출 실패를 서비스 계층에서 의미 있게 구분하기 위한 전용 예외입니다.
    pass


class KRARateLimitExceededError(KRAApiError):
    # "오늘 너무 많이 호출해서 더 이상 호출하면 안 된다"는 상황을 구분하는 예외입니다.
    pass


class KRAApiService:
    # 최신 공공데이터포털 공지 기준으로 실제 호출이 확인된 엔드포인트를 사용합니다.
    SCHEDULE_URL = "https://apis.data.go.kr/B551015/API72_2/racePlan_2"
    ENTRY_URL = "https://apis.data.go.kr/B551015/API26_2/entrySheet_2"
    RESULT_URL = "https://apis.data.go.kr/B551015/API214_1/RaceDetailResult_1"

    def __init__(self, redis_client: Redis | None = None) -> None:
        self.redis_client = redis_client or get_redis_client()
        # AsyncClient를 한 번 만들어 재사용하면 TCP 연결 재활용이 가능해 더 효율적입니다.
        self.http_client = httpx.AsyncClient(timeout=httpx.Timeout(30.0))

    async def close(self) -> None:
        # 앱 종료나 요청 종료 시 HTTP 연결 풀을 정리합니다.
        await self.http_client.aclose()

    def _get_daily_count_key(self, target_date: date | None = None) -> str:
        base_date = target_date or datetime.now().date()
        return f"kra:daily_count:{base_date.strftime('%Y%m%d')}"

    def _get_seconds_until_midnight(self) -> int:
        now = datetime.now()
        next_midnight = datetime.combine(now.date() + timedelta(days=1), time.min)
        return max(1, int((next_midnight - now).total_seconds()))

    async def get_daily_call_count(self, target_date: date | None = None) -> int:
        # Redis 값은 문자열로 오므로, 없으면 0으로 간주한 뒤 정수로 바꿉니다.
        raw_value = await self.redis_client.get(self._get_daily_count_key(target_date))
        return int(raw_value or 0)

    async def _ensure_rate_limit_available(self) -> None:
        current_count = await self.get_daily_call_count()

        if current_count >= settings.kra_stop_threshold:
            raise KRARateLimitExceededError(
                f"KRA 일일 호출 수가 안전 중단 기준({settings.kra_stop_threshold})에 도달했습니다."
            )

    async def _increase_daily_call_count(self) -> int:
        key = self._get_daily_count_key()
        current_count = await self.redis_client.incr(key)
        await self.redis_client.expire(key, self._get_seconds_until_midnight())
        return int(current_count)

    async def _request_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        # 공통 요청 로직을 한 함수로 빼두면
        # schedule/entry/result 세 API가 똑같은 안전장치를 재사용할 수 있습니다.
        last_error: Exception | None = None

        for attempt, delay_seconds in enumerate((0, *settings.kra_retry_delays), start=1):
            if delay_seconds > 0:
                await asyncio.sleep(delay_seconds)

            await self._ensure_rate_limit_available()
            await self._increase_daily_call_count()

            try:
                response = await self.http_client.get(url, params=params)
                response.raise_for_status()
                payload = response.json()

                result_code = (
                    payload.get("response", {})
                    .get("header", {})
                    .get("resultCode")
                )

                if result_code != "00":
                    result_message = (
                        payload.get("response", {})
                        .get("header", {})
                        .get("resultMsg", "알 수 없는 KRA API 오류")
                    )
                    raise KRAApiError(f"KRA API 응답 오류: {result_message}")

                return payload
            except (httpx.HTTPError, KRAApiError, ValueError) as error:
                last_error = error

                if attempt == len(settings.kra_retry_delays) + 1:
                    break

        raise KRAApiError(f"KRA API 호출에 실패했습니다: {last_error}") from last_error

    @staticmethod
    def _normalize_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        # 공공데이터 응답은 item이 "배열일 수도 있고 객체 하나일 수도" 있어서
        # 항상 list[dict] 형태로 통일해두면 이후 저장 로직이 훨씬 단순해집니다.
        items = payload.get("response", {}).get("body", {}).get("items", {}).get("item")

        if items is None:
            return []

        if isinstance(items, list):
            return items

        return [items]

    async def fetch_race_schedule(
        self,
        meet: int,
        rc_year: int,
        rc_month: str,
        page_no: int = 1,
        num_of_rows: int = 200,
    ) -> list[dict[str, Any]]:
        return await self._fetch_all_pages(
            url=self.SCHEDULE_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "rc_year": rc_year,
                "rc_month": rc_month,
                "_type": "json",
            },
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    async def fetch_entry_info(
        self,
        meet: int,
        rc_date: str,
        rc_no: int | None = None,
        page_no: int = 1,
        num_of_rows: int = 200,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "serviceKey": settings.kma_api_key,
            "meet": meet,
            "rc_date": rc_date,
            "_type": "json",
        }

        if rc_no is not None:
            # 실제 API가 rc_no 파라미터를 완벽히 필터링하지 않는 경우가 있어도
            # 일단 함께 전달하고, 저장 단계에서 한 번 더 race 번호를 걸러 안전하게 처리합니다.
            params["rc_no"] = rc_no

        return await self._fetch_all_pages(
            url=self.ENTRY_URL,
            base_params=params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    async def fetch_race_results(
        self,
        meet: int,
        rc_date: str,
        rc_no: int | None = None,
        page_no: int = 1,
        num_of_rows: int = 200,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "serviceKey": settings.kma_api_key,
            "meet": meet,
            "rc_date": rc_date,
            "_type": "json",
        }

        if rc_no is not None:
            params["rc_no"] = rc_no

        return await self._fetch_all_pages(
            url=self.RESULT_URL,
            base_params=params,
            page_no=page_no,
            num_of_rows=num_of_rows,
        )

    async def _fetch_all_pages(
        self,
        url: str,
        base_params: dict[str, Any],
        page_no: int,
        num_of_rows: int,
    ) -> list[dict[str, Any]]:
        # pageNo/numOfRows를 쓰는 공공데이터 API는 첫 페이지를 본 뒤 totalCount를 읽어
        # 남은 페이지를 순회하는 방식이 가장 단순하고 안정적입니다.
        all_items: list[dict[str, Any]] = []
        current_page = page_no
        total_count = None

        while True:
            payload = await self._request_json(
                url,
                {
                    **base_params,
                    "pageNo": current_page,
                    "numOfRows": num_of_rows,
                },
            )

            all_items.extend(self._normalize_items(payload))

            if total_count is None:
                total_count = int(payload.get("response", {}).get("body", {}).get("totalCount", 0))

            if current_page * num_of_rows >= total_count:
                break

            current_page += 1

        return all_items
