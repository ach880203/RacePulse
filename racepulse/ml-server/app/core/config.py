# -*- coding: utf-8 -*-
# =============================================================================
# config.py — 환경변수 설정 파일
# =============================================================================
# 이 파일은 .env 파일에서 설정값을 읽어오는 역할을 합니다.
# 예: DB 주소, Redis 주소, API 키, 수집 제한값 등
# pydantic-settings 라이브러리가 .env 파일을 자동으로 읽어줍니다.
# =============================================================================

# Path = 현재 파일 기준으로 상위 폴더 경로를 계산할 때 사용하는 표준 라이브러리입니다.
from pathlib import Path

# BaseSettings = 환경변수와 .env 값을 파이썬 속성처럼 읽게 해주는 Pydantic 기반 클래스입니다.
from pydantic_settings import BaseSettings
# SettingsConfigDict = Pydantic v2에서 .env 파일 위치 같은 설정을 선언적으로 적는 도구입니다.
from pydantic_settings import SettingsConfigDict


# 현재 config.py 파일 위치를 기준으로 ml-server/.env 와 프로젝트 루트 .env 를 모두 찾습니다.
# 실제 작업 환경에서는 루트 .env 에 API 키가 들어 있으므로 둘 다 읽도록 해두는 것이 안전합니다.
ML_SERVER_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # -------------------------------------------------------------------------
    # 데이터베이스 연결 주소
    # postgresql+asyncpg = PostgreSQL을 비동기 방식으로 연결
    # 비동기(async) = DB 응답을 기다리는 동안 다른 작업도 처리할 수 있게 해주는 방식
    # -------------------------------------------------------------------------
    db_url: str = "postgresql+asyncpg://racepulse:racepulse_dev@localhost:5432/racepulse"

    # -------------------------------------------------------------------------
    # Redis 연결 정보
    # Redis = 빠른 메모리 저장소
    # 이번 작업에서는 일일 API 호출 카운터와 수집 체크포인트 저장에 사용합니다.
    # -------------------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379

    # -------------------------------------------------------------------------
    # 외부 API 키
    # 기본값을 빈 문자열로 두면 .env 가 비어 있어도 코드가 즉시 터지지 않고,
    # 실제 호출 직전에 "키가 없음"을 더 친절하게 안내할 수 있습니다.
    # -------------------------------------------------------------------------
    kma_api_key: str = ""
    weather_api_key: str = ""
    openai_api_key: str = ""

    # -------------------------------------------------------------------------
    # 앱 기본 설정
    # debug=True 이면 SQL 로그와 예외 정보를 더 자세히 볼 수 있어 개발 초기에 유용합니다.
    # -------------------------------------------------------------------------
    app_name: str = "RacePulse ML Server"
    debug: bool = True

    # -------------------------------------------------------------------------
    # KRA 수집 관련 공통 설정
    # daily_limit = 공공데이터 포털에서 허용한 1일 최대 호출 수
    # stop_threshold = 안전하게 멈추기 시작하는 기준선
    # retry_delays = 지수 백오프 대기 시간(초) 목록
    # -------------------------------------------------------------------------
    kra_daily_limit: int = 3000
    kra_stop_threshold: int = 2800
    kra_retry_delays: tuple[int, ...] = (300, 900, 1800, 3600, 10800)

    # -------------------------------------------------------------------------
    # 스케줄러 설정
    # timezone = APScheduler가 "몇 시"를 어떤 시간대로 해석할지 정하는 값입니다.
    # -------------------------------------------------------------------------
    scheduler_timezone: str = "Asia/Seoul"

    # model_config = BaseSettings가 어떤 .env 파일을 읽을지 정하는 설정입니다.
    model_config = SettingsConfigDict(
        env_file=(ML_SERVER_ROOT / ".env", PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def redis_url(self) -> str:
        # Redis 연결 문자열을 한 곳에서 조합해두면 다른 파일이 host/port를 다시 붙일 필요가 없습니다.
        return f"redis://{self.redis_host}:{self.redis_port}/0"


# -----------------------------------------------------------------------------
# settings 객체를 하나만 만들어서 앱 전체에서 공유
# 다른 파일에서 쓸 때: from app.core.config import settings
# -----------------------------------------------------------------------------
settings = Settings()
