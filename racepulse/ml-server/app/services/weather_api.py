# -*- coding: utf-8 -*-
# =============================================================================
# weather_api.py — 기상청 공공데이터 API 호출 서비스
# =============================================================================
# 기상청은 위경도(위도/경도) 대신 격자 좌표(nx, ny)를 씁니다.
# 이유: 기상청이 한반도 전체를 바둑판처럼 격자로 나눠서 예보를 계산하기 때문입니다.
# 예를 들어 서울(과천)은 nx=62, ny=122 로 표현됩니다.
# 우리가 아는 "위도 37.45, 경도 126.99"와 같은 좌표입니다.
# =============================================================================

# logging = 서버 로그(정보/경고/오류)를 기록하는 표준 라이브러리입니다.
import logging
# datetime/timedelta = 단기예보 기준시각(base_date, base_time) 계산에 사용합니다.
from datetime import date, datetime, timedelta
# Any/Optional = 타입 힌트에서 "어떤 타입이든 가능"하거나 "없을 수도 있음"을 표현합니다.
from typing import Any, Optional

# httpx = 파이썬에서 외부 HTTP 요청을 비동기로 보내는 라이브러리입니다.
# requests 라이브러리의 비동기 버전이라고 생각하면 됩니다.
import httpx
# AsyncSession = SQLAlchemy 비동기 DB 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession
# select = DB에서 데이터를 조회할 때 사용하는 SQL SELECT 문을 파이썬으로 작성하는 도구입니다.
from sqlalchemy import select

# settings = .env 의 WEATHER_API_KEY 를 읽어오는 공통 설정 객체입니다.
from app.core.config import settings
# WeatherForecast = weather_forecasts 테이블과 연결된 DB 모델입니다.
from app.models.weather import WeatherForecast

# 이 파일 전용 로거(log 기록기)를 만듭니다.
# 로거 이름을 파일명으로 지정하면 어느 파일에서 출력한 로그인지 구분하기 쉽습니다.
logger = logging.getLogger(__name__)

# =============================================================================
# 경마장별 기상청 격자 좌표 및 중기예보 구역 코드
# =============================================================================
# nx, ny = 기상청 격자 좌표 (위경도를 기상청 방식으로 변환한 값)
# regId = 중기예보 예보구역 코드 (기상청이 지역별로 부여한 고유 코드)
#   11B00000 = 서울/경기 권역
#   11H20000 = 부산/경남 권역
#   11G00000 = 제주 권역
# =============================================================================
RACECOURSE_COORDINATES: dict[str, dict[str, Any]] = {
    "SC": {
        "nx": 62,
        "ny": 122,
        "mid_land_reg_id": "11B00000",
        "mid_temp_reg_id": "11B10101",
    },  # 서울/과천
    "BU": {
        "nx": 98,
        "ny": 76,
        "mid_land_reg_id": "11H20000",
        "mid_temp_reg_id": "11H20201",
    },  # 부산경남
    "JJ": {
        "nx": 52,
        "ny": 38,
        "mid_land_reg_id": "11G00000",
        "mid_temp_reg_id": "11G00201",
    },  # 제주
}

# 기상청 API 기본 URL
_SHORT_TERM_BASE_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0"
_MID_TERM_BASE_URL = "https://apis.data.go.kr/1360000/MidFcstInfoService"


def get_weather_condition(pty: int, sky: int) -> str:
    """기상청 코드값을 사람이 읽을 수 있는 한글 날씨 텍스트로 변환합니다.

    pty = 강수형태 (Precipitation TYpe)
      0 = 없음, 1 = 비, 2 = 비/눈, 3 = 눈, 4 = 소나기

    sky = 하늘상태 (SKY condition)
      1 = 맑음, 3 = 구름많음, 4 = 흐림

    변환 우선순위: 강수가 있으면 강수 유형을 먼저 반환하고,
    강수가 없으면 하늘 상태로 판단합니다.
    """
    # 강수형태가 "없음(0)"이 아니면 비/눈/소나기 등을 우선 표시합니다.
    if pty == 1:
        return "비"
    if pty == 2:
        return "비/눈"
    if pty == 3:
        return "눈"
    if pty == 4:
        return "소나기"
    # 강수가 없을 때는 하늘 상태로 판단합니다.
    if sky == 1:
        return "맑음"
    if sky == 3:
        return "구름많음"
    if sky == 4:
        return "흐림"
    return "알 수 없음"


class WeatherApiService:
    """기상청 단기예보/중기예보 API를 호출하고 DB에 저장하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        # db = 이 서비스가 사용할 비동기 DB 세션입니다.
        # 세션은 외부(라우터 또는 스케줄러)에서 주입받으므로 직접 생성하지 않습니다.
        self.db = db
        # httpx.AsyncClient = 비동기 HTTP 요청을 보내는 클라이언트입니다.
        # timeout=30 = 기상청 서버가 30초 안에 응답하지 않으면 오류로 처리합니다.
        self.client = httpx.AsyncClient(timeout=30)

    async def close(self) -> None:
        """HTTP 클라이언트 연결을 닫습니다. 서비스 사용 후 반드시 호출해야 합니다."""
        await self.client.aclose()

    # =========================================================================
    # 단기예보 수집
    # =========================================================================

    async def fetch_short_term_forecast(self, meet_code: str) -> list[dict[str, Any]]:
        """단기예보 API를 호출하여 특정 경마장의 오늘~3일 후 날씨 데이터를 수집합니다.

        기상청 단기예보는 하루 8번 발표되는데, 주요 발표 시각은 02:00, 05:00, 08:00, 11:00 등입니다.
        이 함수는 가장 최근 발표된 예보를 자동으로 선택합니다.
        """
        if meet_code not in RACECOURSE_COORDINATES:
            raise ValueError(f"알 수 없는 경마장 코드입니다: {meet_code}")

        coords = RACECOURSE_COORDINATES[meet_code]

        # 단기예보 기준시각 계산
        # 기상청 발표 시각: 02, 05, 08, 11, 14, 17, 20, 23시
        # 현재 시각보다 이전에 발표된 가장 최근 시각을 사용합니다.
        base_date, base_time = self._get_short_term_base_time()

        params = {
            "serviceKey": settings.weather_api_key,  # API 인증 키
            "pageNo": 1,                              # 페이지 번호 (첫 번째 페이지)
            "numOfRows": 1000,                        # 한 번에 받을 행 수 (넉넉하게 설정)
            "dataType": "JSON",                       # 응답 형식 (XML 대신 JSON 사용)
            "base_date": base_date,                   # 예보 기준 날짜 (예: 20260507)
            "base_time": base_time,                   # 예보 기준 시각 (예: 0600)
            "nx": coords["nx"],                       # X 격자 좌표
            "ny": coords["ny"],                       # Y 격자 좌표
        }

        logger.info("[단기예보] %s 경마장 수집 시작 (base=%s %s)", meet_code, base_date, base_time)

        items = await self._request_items(
            url=f"{_SHORT_TERM_BASE_URL}/getVilageFcst",
            params=params,
            log_name=f"단기예보:{meet_code}",
        )

        # 날짜별로 데이터를 묶어서 처리합니다.
        return self._parse_short_term_items(meet_code, items)

    def _get_short_term_base_time(self) -> tuple[str, str]:
        """현재 시각 기준으로 가장 최근 단기예보 발표 시각을 계산합니다.

        단기예보 발표 시각: 02, 05, 08, 11, 14, 17, 20, 23시 (발표 후 약 10분 후 서비스 제공)
        따라서 현재 시각에서 10분을 빼고, 그보다 이전 발표 시각을 사용합니다.
        """
        # 발표 후 실제 서비스까지 10분 여유를 둡니다.
        now = datetime.now() - timedelta(minutes=10)

        # 기상청 단기예보 발표 시각 목록 (24시간 형식)
        base_times = [2, 5, 8, 11, 14, 17, 20, 23]

        # 현재 시각보다 이전에 발표된 가장 최근 발표 시각을 찾습니다.
        base_hour = 23
        for hour in reversed(base_times):
            if now.hour >= hour:
                base_hour = hour
                break
        else:
            # 아직 02시도 안 됐으면 어제 23시 예보를 사용합니다.
            now = now - timedelta(days=1)
            base_hour = 23

        base_date = now.strftime("%Y%m%d")       # 예: "20260507"
        base_time = f"{base_hour:02d}00"          # 예: "0600"
        return base_date, base_time

    def _parse_short_term_items(self, meet_code: str, items: list[dict]) -> list[dict[str, Any]]:
        """단기예보 응답 항목을 날짜별로 묶어서 정리합니다.

        기상청 단기예보는 카테고리별로 행이 쪼개져서 옵니다.
        예: 같은 날짜에 TMP(기온), PTY(강수형태), WSD(풍속) 각각 별도 행으로 옵니다.
        이 함수에서 같은 날짜의 항목을 하나로 합칩니다.
        """
        # 날짜 → 수집 데이터 딕셔너리로 묶습니다.
        daily: dict[str, dict[str, Any]] = {}

        for item in items:
            fcst_date = item.get("fcstDate", "")  # 예보 날짜 (예: "20260507")
            category = item.get("category", "")   # 항목 코드 (예: TMP, PTY, WSD)
            value = item.get("fcstValue", "")      # 예보 값

            if fcst_date not in daily:
                daily[fcst_date] = {"date": fcst_date, "meet_code": meet_code}

            # 단기예보에서 필요한 카테고리만 추출합니다.
            # TMP = 기온(°C), PTY = 강수형태, WSD = 풍속(m/s), POP = 강수확률(%)
            # TMX = 일 최고기온, TMN = 일 최저기온, SKY = 하늘상태
            if category == "TMP":
                # 시간별 기온 중 최솟값/최댓값을 누적합니다.
                try:
                    temp = float(value)
                    if "temp_min" not in daily[fcst_date]:
                        daily[fcst_date]["temp_min"] = temp
                        daily[fcst_date]["temp_max"] = temp
                    else:
                        daily[fcst_date]["temp_min"] = min(daily[fcst_date]["temp_min"], temp)
                        daily[fcst_date]["temp_max"] = max(daily[fcst_date]["temp_max"], temp)
                except (ValueError, TypeError):
                    pass
            elif category == "TMN":
                try:
                    daily[fcst_date]["temp_min"] = float(value)
                except (ValueError, TypeError):
                    pass
            elif category == "TMX":
                try:
                    daily[fcst_date]["temp_max"] = float(value)
                except (ValueError, TypeError):
                    pass
            elif category == "POP":
                # POP = 강수확률(%) — 같은 날 여러 시간대 중 최댓값 사용
                try:
                    prob = int(value)
                    current = daily[fcst_date].get("precipitation_prob", 0)
                    daily[fcst_date]["precipitation_prob"] = max(current, prob)
                except (ValueError, TypeError):
                    pass
            elif category == "WSD":
                # WSD = 풍속(m/s) — 같은 날 여러 시간대 중 최댓값 사용
                try:
                    speed = float(value)
                    current = daily[fcst_date].get("wind_speed", 0.0)
                    daily[fcst_date]["wind_speed"] = max(current, speed)
                except (ValueError, TypeError):
                    pass
            elif category == "PTY":
                # PTY = 강수형태 (비/눈/소나기 등)
                try:
                    pty = int(value)
                    # 비가 오는 경우(pty > 0)를 우선 기록합니다.
                    if pty > 0:
                        daily[fcst_date]["pty"] = pty
                    elif "pty" not in daily[fcst_date]:
                        daily[fcst_date]["pty"] = pty
                except (ValueError, TypeError):
                    pass
            elif category == "SKY":
                # SKY = 하늘상태 (맑음/구름많음/흐림)
                try:
                    sky = int(value)
                    # 가장 흐린 상태를 우선 기록합니다 (숫자가 클수록 더 흐림).
                    current = daily[fcst_date].get("sky", 1)
                    daily[fcst_date]["sky"] = max(current, sky)
                except (ValueError, TypeError):
                    pass

        # 날씨 조건 텍스트 변환 및 정리
        result = []
        for day_data in daily.values():
            pty = day_data.get("pty", 0)
            sky = day_data.get("sky", 1)
            day_data["condition"] = get_weather_condition(pty, sky)
            day_data["source"] = "short_term"
            result.append(day_data)

        return result

    # =========================================================================
    # 중기예보 수집
    # =========================================================================

    async def fetch_mid_term_forecast(self, meet_code: str) -> list[dict[str, Any]]:
        """중기예보 API를 호출하여 특정 경마장의 3~10일 후 날씨 데이터를 수집합니다.

        중기예보 발표 시각: 06:00, 18:00 두 번 발표합니다.
        """
        if meet_code not in RACECOURSE_COORDINATES:
            raise ValueError(f"알 수 없는 경마장 코드입니다: {meet_code}")

        coords = RACECOURSE_COORDINATES[meet_code]
        land_reg_id = coords["mid_land_reg_id"]
        temp_reg_id = coords["mid_temp_reg_id"]

        # 중기예보 발표시각: 오늘 06:00 또는 18:00 형식으로 전달합니다.
        # 형식: YYYYMMDDHHMM (예: 202605070600)
        tm_fc = self._get_mid_term_tm_fc()

        land_params = {
            "serviceKey": settings.weather_api_key,
            "pageNo": 1,
            "numOfRows": 10,
            "dataType": "JSON",
            "regId": land_reg_id,  # 육상예보 권역 코드 (예: 11B00000)
            "tmFc": tm_fc,         # 발표시각 (예: 202605070600)
        }

        temp_params = {
            "serviceKey": settings.weather_api_key,
            "pageNo": 1,
            "numOfRows": 10,
            "dataType": "JSON",
            "regId": temp_reg_id,  # 기온예보 상세 지역 코드 (예: 11B10101)
            "tmFc": tm_fc,
        }

        logger.info(
            "[중기예보] %s 경마장 수집 시작 (landRegId=%s, tempRegId=%s, tmFc=%s)",
            meet_code,
            land_reg_id,
            temp_reg_id,
            tm_fc,
        )

        # 실제 운영 중인 중기예보는 육상전망/기온예보가 API 두 개로 나뉘어 있습니다.
        # 프롬프트의 getMidFcst 설명만 그대로 믿으면 2026-05-11 기준 404 가 나기 때문에,
        # 공식 응답이 정상인 getMidLandFcst + getMidTa 를 조합해서 저장합니다.
        land_items = await self._request_items(
            url=f"{_MID_TERM_BASE_URL}/getMidLandFcst",
            params=land_params,
            log_name=f"중기육상예보:{meet_code}",
        )
        temp_items = await self._request_items(
            url=f"{_MID_TERM_BASE_URL}/getMidTa",
            params=temp_params,
            log_name=f"중기기온예보:{meet_code}",
        )

        return self._parse_mid_term_items(
            meet_code=meet_code,
            land_items=land_items,
            temp_items=temp_items,
            tm_fc=tm_fc,
        )

    def _get_mid_term_tm_fc(self) -> str:
        """현재 시각 기준으로 가장 최근 중기예보 발표 시각을 계산합니다.

        중기예보는 하루 두 번 발표됩니다: 오전 6시, 오후 6시.
        현재가 오전 6시 이전이면 어제 18시 예보를 사용합니다.
        """
        now = datetime.now()

        if now.hour >= 18:
            tm_fc = now.strftime("%Y%m%d") + "1800"
        elif now.hour >= 6:
            tm_fc = now.strftime("%Y%m%d") + "0600"
        else:
            # 어제 18시 예보를 사용합니다.
            yesterday = now - timedelta(days=1)
            tm_fc = yesterday.strftime("%Y%m%d") + "1800"

        return tm_fc

    def _parse_mid_term_items(
        self,
        meet_code: str,
        land_items: list[dict],
        temp_items: list[dict],
        tm_fc: str,
    ) -> list[dict[str, Any]]:
        """중기 육상예보와 중기 기온예보를 날짜 기준으로 합칩니다.

        실제 운영 API는 "날씨 전망"과 "기온"을 한 번에 주지 않습니다.
        그래서 getMidLandFcst, getMidTa 두 응답을 같은 날짜로 묶어서
        weather_forecasts 테이블의 한 행으로 만드는 작업이 필요합니다.
        """
        result: list[dict[str, Any]] = []
        base_forecast_date = datetime.strptime(tm_fc[:8], "%Y%m%d").date()

        land_item = land_items[0] if land_items else {}
        temp_item = temp_items[0] if temp_items else {}

        # 2026-05-11 실제 응답 기준으로 중기예보 필드는 4일 후부터 10일 후까지 내려옵니다.
        # 따라서 프롬프트의 "3~10일" 설명보다 실제 필드 체계를 우선해 4~10일 범위를 저장합니다.
        for day_offset in range(4, 11):
            # 중기예보의 n일 후 기준은 "현재 시각"이 아니라 "발표일(tmFc)" 기준입니다.
            # 예를 들어 2026-05-11 01:00 에는 2026-05-10 18:00 발표분을 쓰므로,
            # 4일 후 예보는 2026-05-15 가 아니라 2026-05-14 로 계산되어야 합니다.
            forecast_date = base_forecast_date + timedelta(days=day_offset)

            am_key_rn = f"rnSt{day_offset}Am"
            pm_key_rn = f"rnSt{day_offset}Pm"
            am_key_wf = f"wf{day_offset}Am"
            pm_key_wf = f"wf{day_offset}Pm"

            if day_offset >= 8:
                # 8~10일은 오전/오후 분리 키가 아니라 단일 키로 제공됩니다.
                am_key_rn = f"rnSt{day_offset}"
                pm_key_rn = f"rnSt{day_offset}"
                am_key_wf = f"wf{day_offset}"
                pm_key_wf = f"wf{day_offset}"

            try:
                am_rn = int(land_item.get(am_key_rn, 0) or 0)
                pm_rn = int(land_item.get(pm_key_rn, 0) or 0)
                precipitation_prob = max(am_rn, pm_rn)
            except (ValueError, TypeError):
                precipitation_prob = None

            wf_am = str(land_item.get(am_key_wf, "") or "").strip()
            wf_pm = str(land_item.get(pm_key_wf, "") or "").strip()
            condition = wf_pm or wf_am or "알 수 없음"

            try:
                temp_min_raw = temp_item.get(f"taMin{day_offset}")
                temp_min = float(temp_min_raw) if temp_min_raw not in (None, "", "-") else None
            except (ValueError, TypeError):
                temp_min = None

            try:
                temp_max_raw = temp_item.get(f"taMax{day_offset}")
                temp_max = float(temp_max_raw) if temp_max_raw not in (None, "", "-") else None
            except (ValueError, TypeError):
                temp_max = None

            result.append({
                "date": forecast_date.strftime("%Y%m%d"),
                "meet_code": meet_code,
                "forecast_date": forecast_date,
                "temp_min": temp_min,
                "temp_max": temp_max,
                "precipitation_prob": precipitation_prob,
                "condition": condition,
                "source": "mid_term",
            })

        return result

    async def _request_items(self, url: str, params: dict[str, Any], log_name: str) -> list[dict]:
        """기상청 OpenAPI 응답을 공통 처리해서 item 리스트로 돌려줍니다.

        기상청 응답은 item 이 list 일 때도 있고 dict 하나일 때도 있습니다.
        이 차이를 여기서 흡수해 두면 상위 파서가 훨씬 단순해집니다.
        """
        response = await self.client.get(url, params=params)
        response.raise_for_status()

        data = response.json()
        header = data.get("response", {}).get("header", {})
        result_code = header.get("resultCode")
        result_message = header.get("resultMsg", "알 수 없는 기상청 응답")

        if result_code != "00":
            raise ValueError(f"{log_name} 응답 오류: {result_message}")

        raw_items = (
            data.get("response", {})
            .get("body", {})
            .get("items", {})
            .get("item", [])
        )

        if isinstance(raw_items, list):
            return raw_items
        if isinstance(raw_items, dict):
            return [raw_items]
        return []

    # =========================================================================
    # DB 저장 (Upsert)
    # =========================================================================

    async def save_forecast(self, meet_code: str, forecast_data: list[dict[str, Any]]) -> int:
        """날씨 예보 데이터를 DB에 저장합니다.

        upsert = "있으면 업데이트(UPDATE), 없으면 삽입(INSERT)"
        같은 경마장+날짜 조합이 이미 DB에 있으면 덮어쓰고,
        없으면 새 레코드를 추가합니다.
        이렇게 하면 API를 여러 번 호출해도 중복 데이터가 쌓이지 않습니다.
        """
        saved_count = 0

        for item in forecast_data:
            # forecast_date 파싱 (문자열 "20260507" → date 객체 또는 이미 date 이면 그대로 사용)
            if isinstance(item.get("forecast_date"), date):
                forecast_date = item["forecast_date"]
            elif item.get("date"):
                try:
                    forecast_date = datetime.strptime(item["date"], "%Y%m%d").date()
                except ValueError:
                    logger.warning("날짜 파싱 실패: %s", item.get("date"))
                    continue
            else:
                continue

            # 기존 레코드 조회 (같은 경마장 + 날짜 조합)
            # 현재 DB의 유니크 키가 (meet_code, forecast_date) 이라서
            # source 까지 다르게 넣으면 short_term / mid_term 이 겹치는 날짜에서 충돌할 수 있습니다.
            # 따라서 날짜 기준으로 먼저 찾고, source 는 더 신선한 쪽 규칙으로 갱신합니다.
            stmt = select(WeatherForecast).where(
                WeatherForecast.meet_code == meet_code,
                WeatherForecast.forecast_date == forecast_date,
            )
            existing = await self.db.scalar(stmt)

            if existing:
                incoming_source = item.get("source", "short_term")

                # 단기예보는 시간 단위가 더 촘촘하므로, 같은 날짜가 겹치면 short_term 을 우선 유지합니다.
                if existing.source == "short_term" and incoming_source == "mid_term":
                    if existing.temp_min is None:
                        existing.temp_min = item.get("temp_min")
                    if existing.temp_max is None:
                        existing.temp_max = item.get("temp_max")
                    if existing.precipitation_prob is None:
                        existing.precipitation_prob = item.get("precipitation_prob")
                    if existing.wind_speed is None:
                        existing.wind_speed = item.get("wind_speed")
                    if not existing.condition:
                        existing.condition = item.get("condition")
                else:
                    # 같은 source 재수집이거나 mid_term 행을 short_term 으로 더 정밀하게 덮는 경우입니다.
                    if item.get("temp_min") is not None:
                        existing.temp_min = item.get("temp_min")
                    if item.get("temp_max") is not None:
                        existing.temp_max = item.get("temp_max")
                    if item.get("precipitation_prob") is not None:
                        existing.precipitation_prob = item.get("precipitation_prob")
                    if item.get("wind_speed") is not None:
                        existing.wind_speed = item.get("wind_speed")
                    if item.get("condition"):
                        existing.condition = item.get("condition")
                    existing.source = incoming_source
            else:
                # 기존 레코드가 없으면 새로 삽입합니다 (insert).
                new_record = WeatherForecast(
                    meet_code=meet_code,
                    forecast_date=forecast_date,
                    temp_min=item.get("temp_min"),
                    temp_max=item.get("temp_max"),
                    precipitation_prob=item.get("precipitation_prob"),
                    wind_speed=item.get("wind_speed"),
                    condition=item.get("condition"),
                    source=item.get("source", "short_term"),
                )
                self.db.add(new_record)

            saved_count += 1

        # commit = 변경 내용을 실제로 DB에 반영합니다.
        # commit 전까지는 메모리에만 있고 DB에는 저장되지 않습니다.
        await self.db.commit()
        logger.info("[날씨 저장] %s 경마장 %d 건 저장 완료", meet_code, saved_count)
        return saved_count

    # =========================================================================
    # 날씨 조회
    # =========================================================================

    async def get_weather(self, meet_code: str, target_date: date) -> Optional[WeatherForecast]:
        """특정 경마장의 특정 날짜 날씨를 DB에서 조회합니다."""
        stmt = select(WeatherForecast).where(
            WeatherForecast.meet_code == meet_code,
            WeatherForecast.forecast_date == target_date,
        ).order_by(WeatherForecast.updated_at.desc())

        return await self.db.scalar(stmt)
