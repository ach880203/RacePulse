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
    ENTRY_URL    = "https://apis.data.go.kr/B551015/API26_2/entrySheet_2"
    RESULT_URL   = "https://apis.data.go.kr/B551015/API214_1/RaceDetailResult_1"

    # 마스터 데이터 전용 API — data.go.kr B551015 공개 명세 기준 (확인된 서비스URL)
    JOCKEY_INFO_URL    = "https://apis.data.go.kr/B551015/API12_1/jockeyInfo_1"
    JOCKEY_RESULT_URL  = "https://apis.data.go.kr/B551015/API11_1/jockeyResult_1"
    JOCKEY_CHANGE_URL  = "https://apis.data.go.kr/B551015/API10_1/jockeyChangeInfo_1"
    TRAINER_INFO_URL   = "https://apis.data.go.kr/B551015/API19_1/trainerInfo_1"
    HORSE_LIST_URL     = "https://apis.data.go.kr/B551015/racehorselist/getracehorselist"
    HORSE_RESULT_URL   = "https://apis.data.go.kr/B551015/API15_2/raceHorseResult_2"
    HORSE_DETAIL_URL   = "https://apis.data.go.kr/B551015/API8_2/raceHorseInfo_2"
    HORSE_TOTAL_URL    = "https://apis.data.go.kr/B551015/API42/totalHorseInfo_1"
    TRACK_INFO_URL     = "https://apis.data.go.kr/B551015/API189_1/Track_1"
    INTEGRATED_ODD_URL = "https://apis.data.go.kr/B551015/API160_1/integratedInfo_1"
    RACE_RESULT_V3_URL = "https://apis.data.go.kr/B551015/API4_3/raceResult_3"
    HORSE_RATING_URL   = "https://apis.data.go.kr/B551015/API77/raceHorseRating"

    # 하위 호환을 위해 이전 이름도 유지합니다.
    HORSE_INFO_URL = HORSE_LIST_URL

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
        #
        # 주의: 결과가 없을 때 KRA API는 items를 {} 대신 "" (빈 문자열)로 내려보내는 경우가 있습니다.
        # 이 경우 "".get("item") 을 호출하면 AttributeError가 발생하므로
        # items_container 가 dict 인지 먼저 확인합니다.
        body = payload.get("response", {}).get("body", {})
        items_container = body.get("items")

        # items_container 가 dict 가 아니면 (None, 빈 문자열, 기타) → 데이터 없음
        if not isinstance(items_container, dict):
            return []

        items = items_container.get("item")

        if items is None:
            return []

        # 단건 응답(dict 1개) → 리스트로 감쌉니다.
        if isinstance(items, dict):
            return [items]

        # 다건 응답(list) → dict 인 항목만 추려서 반환합니다.
        if isinstance(items, list):
            return [i for i in items if isinstance(i, dict)]

        # 그 외 예상치 못한 타입 → 빈 리스트로 안전하게 처리합니다.
        return []

    async def fetch_jockey_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """현직 기수 목록을 전체 페이지 수집합니다.

        출처: data.go.kr 15056828 — 기수 상세정보 (API12_1/jockeyInfo_1)
        응답 필드:
          jkNo     — 기수번호 → license_no
          jkName   — 기수명
          part     — 소속조 → affiliation
          birthday — 생년월일 YYYYMMDD → birth_year
          debut    — 데뷔일자 YYYYMMDD → debut_year
          rcCntT   — 통산 총출주횟수
          ord1CntT — 통산 1착횟수  → win_rate_total = ord1CntT / rcCntT
          ord2CntT — 통산 2착횟수
          ord3CntT — 통산 3착횟수  → place_rate_total = (1+2+3) / rcCntT
          rcCntY   — 최근1년 총출주횟수
          ord1CntY — 최근1년 1착횟수 → win_rate_recent = ord1CntY / rcCntY
        """
        return await self._fetch_all_pages(
            url=self.JOCKEY_INFO_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_jockey_result_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """현직 기수 성적(승률 직접 제공)을 전체 페이지 수집합니다.

        출처: data.go.kr 15056591 — 기수 성적 정보 (API11_1/jockeyResult_1)
        응답 필드:
          jkNo     — 기수번호 → license_no
          jkName   — 기수명
          rcCntT   — 통산 총출주횟수
          ord1CntT — 통산 1착횟수
          ord2CntT — 통산 2착횟수
          winRateT — 통산 승률 (% 단위, e.g. 15.3 → 0.153)
          plcRateT — 통산 복승률 (% 단위)
          rcCntY   — 최근1년 총출주횟수
          ord1CntY — 최근1년 1착횟수
          winRateY — 최근1년 승률 (% 단위)
          plcRateY — 최근1년 복승률 (% 단위)
        """
        return await self._fetch_all_pages(
            url=self.JOCKEY_RESULT_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_jockey_change_list(
        self,
        meet: int,
        rc_date: str,
        num_of_rows: int = 100,
    ) -> list[dict[str, Any]]:
        """당일 기수 변경 정보를 수집합니다.

        출처: data.go.kr 15057181 — 기수변경정보 (API10_1/jockeyChangeInfo_1)
        응답 필드:
          rcDate      — 경주일자
          rcNo        — 경주번호
          chgBefore   — 변경 전 기수명
          chgAfter    — 변경 후 기수명
          wgBefore    — 변경 전 부담중량
          wgAfter     — 변경 후 부담중량
        """
        return await self._fetch_all_pages(
            url=self.JOCKEY_CHANGE_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "rc_date": rc_date,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_trainer_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """현직 조교사 목록을 전체 페이지 수집합니다.

        출처: data.go.kr 15057915 — 조교사 상세정보 (API19_1/trainerInfo_1)
        응답 필드:
          trNo      — 조교사번호 → license_no
          trName    — 조교사명
          part      — 소속조 → affiliation
          birthday  — 생년월일 YYYYMMDD → birth_year
          stDate    — 데뷔일자 → debut_year
          rcCntT    — 통산 출주횟수
          ord1CntT  — 통산 1착횟수
          ord2CntT  — 통산 2착횟수
          ord3CntT  — 통산 3착횟수
          winRateT  — 통산 승률 (% 단위, e.g. 15.3 → 0.153 으로 변환)
          plcRateT  — 통산 복승률 (% 단위)
          conRateT  — 통산 연승률 (% 단위)
          rcCntY    — 최근1년 출주횟수
          winRateY  — 최근1년 승률 (% 단위)
          plcRateY  — 최근1년 복승률 (% 단위)
        """
        return await self._fetch_all_pages(
            url=self.TRAINER_INFO_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_horse_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """경마장별 현역 경주마 명단을 전체 페이지 수집합니다.

        출처: data.go.kr 15089503 — 경주마명단 (racehorselist/getracehorselist)
        응답 필드:
          hrNo     — 마번
          hrName   — 마명
          nameSp   — 소속조 (예: "40조") — eng_name 아님
          sex      — 성별
          prdCty   — 생산국 → origin
          rating1~4 — 레이팅
        """
        return await self._fetch_all_pages(
            url=self.HORSE_LIST_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_horse_result_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """경주마 성적 정보(통산/최근1년 승률·복승률)를 전체 페이지 수집합니다.

        출처: data.go.kr 15058779 — 경주마 성적 정보 (API15_2/raceHorseResult_2)
        응답 필드:
          hrName   — 마명
          hrNo     — 마번
          prdCty   — 산지
          sex      — 성별
          age      — 나이
          debut    — 데뷔일자 YYYYMMDD → debut_year
          rcCntT   — 통산 총출주횟수
          ord1CntT — 통산 1착횟수
          ord2CntT — 통산 2착횟수
          winRateT — 통산 승률 (% 단위)
          plcRateT — 통산 복승률 (% 단위)
          rcCntY   — 최근1년 총출주횟수
          ord1CntY — 최근1년 1착횟수
          ord2CntY — 최근1년 2착횟수
          winRateY — 최근1년 승률 (% 단위)
          plcRateY — 최근1년 복승률 (% 단위)
          prizeSum — 통산 착순상금
        """
        return await self._fetch_all_pages(
            url=self.HORSE_RESULT_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_horse_detail_list(
        self,
        meet: int,
        num_of_rows: int = 500,
    ) -> list[dict[str, Any]]:
        """현역 경주마 상세정보(모마명 포함)를 전체 페이지 수집합니다.

        출처: data.go.kr 15058115 — 경주마 상세정보 (API8_2/raceHorseInfo_2)
        응답 필드:
          hrName   — 마명
          hrNo     — 마번
          prdCty   — 출생지(산지)
          sex      — 성별
          birthday — 생년월일 YYYYMMDD → birth_year
          trName   — 조교사명
          owName   — 마주명
          motherName (또는 mName) — 모마명 → mother_name
          rcCntT, ord1CntT, ord2CntT, ord3CntT — 통산 성적
          rcCntY, ord1CntY, ord2CntY, ord3CntY — 최근1년 성적
          rating   — 현재 레이팅
        """
        return await self._fetch_all_pages(
            url=self.HORSE_DETAIL_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_total_horse_info(
        self,
        hr_no: str | None = None,
        hr_name: str | None = None,
        num_of_rows: int = 10,
    ) -> list[dict[str, Any]]:
        """마필종합 상세정보(부마·모마·외조부마 혈통 포함)를 단건 조회합니다.

        출처: data.go.kr 15057985 — 마필종합 상세정보 (API42/totalHorseInfo_1)
        단건 조회이므로 hr_no 또는 hr_name 중 하나는 반드시 전달해야 합니다.
        응답 필드: 부마명(fatherName), 모마명(motherName), 외조부마명(grandfatherName), 혈통 등
        """
        params: dict[str, Any] = {
            "serviceKey": settings.kma_api_key,
            "_type": "json",
        }
        if hr_no:
            params["hr_no"] = hr_no
        if hr_name:
            params["hr_name"] = hr_name
        return await self._fetch_all_pages(
            url=self.HORSE_TOTAL_URL,
            base_params=params,
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_total_horse_info_list(
        self,
        meet: int,
        num_of_rows: int = 100,
    ) -> list[dict[str, Any]]:
        """경마장별 마필종합 상세정보(부마명·모색·영문마명)를 전체 페이지 수집합니다.

        출처: data.go.kr 15057985 — 마필종합 상세정보 (API42/totalHorseInfo_1)
        fetch_total_horse_info(단건)와 달리 meet 파라미터로 경마장 전체 목록을 수집합니다.
        주간 마스터 동기화에서 father_name·color·eng_name 일괄 보완 목적으로 사용합니다.
        응답 주요 필드:
          hrName    — 마명
          hrEngName — 영문마명 → eng_name
          faName    — 부마명   → father_name
          moName    — 모마명   → mother_name
          color     — 모색     → color
        """
        return await self._fetch_all_pages(
            url=self.HORSE_TOTAL_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_track_conditions(
        self,
        meet: int,
        rc_date: str,
        num_of_rows: int = 50,
    ) -> list[dict[str, Any]]:
        """당일 경마장 경주로 상태(함수율·날씨·주로상태)를 수집합니다.

        출처: data.go.kr 15063953 — 경주로정보 (API189_1/Track_1)
        응답 필드:
          meet          — 경마장
          rcDate        — 경주일자
          rcNo          — 경주번호
          moistContent  — 함수율 (%, e.g. 8.5)
          weather       — 날씨 (맑음/흐림/비/눈 등)
          budrCondition — 경주로상태 (건조/양호/다습/포화/불량)
        """
        return await self._fetch_all_pages(
            url=self.TRACK_INFO_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "rc_date": rc_date,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_integrated_odds(
        self,
        meet: int,
        rc_date: str,
        num_of_rows: int = 200,
    ) -> list[dict[str, Any]]:
        """당일 경주 확정배당율 통합 정보를 수집합니다.

        출처: data.go.kr 15058559 — 확정배당율 통합 정보 (API160_1/integratedInfo_1)
        응답 필드: 경주번호, 1착마 출주번호, 2착마 출주번호, 승식구분(WIN/PLC/QNL 등), 배당률
        """
        return await self._fetch_all_pages(
            url=self.INTEGRATED_ODD_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "rc_date": rc_date,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

    async def fetch_race_results_v3(
        self,
        meet: int,
        rc_date: str,
        num_of_rows: int = 200,
    ) -> list[dict[str, Any]]:
        """경주기록 정보(영문마명·영문기수명·구간기록 포함)를 수집합니다.

        출처: data.go.kr 15058305 — 경주기록 정보 (API4_3/raceResult_3)
        기존 RaceDetailResult_1 대비 영문명, 구간별 기록이 추가된 버전입니다.
        """
        return await self._fetch_all_pages(
            url=self.RACE_RESULT_V3_URL,
            base_params={
                "serviceKey": settings.kma_api_key,
                "meet": meet,
                "rc_date": rc_date,
                "_type": "json",
            },
            page_no=1,
            num_of_rows=num_of_rows,
        )

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
