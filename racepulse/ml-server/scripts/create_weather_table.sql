-- =============================================================================
-- create_weather_table.sql — weather_forecasts 테이블 생성 스크립트
-- =============================================================================
-- 실행 방법: psql -U racepulse -d racepulse -f scripts/create_weather_table.sql
-- =============================================================================

CREATE TABLE IF NOT EXISTS weather_forecasts (
    -- id: 자동 증가 기본 키 (1, 2, 3 ... 순서로 DB가 자동 부여)
    id               SERIAL PRIMARY KEY,

    -- meet_code: 경마장 코드 (SC=서울/과천, BU=부산경남, JJ=제주)
    meet_code        VARCHAR(2)   NOT NULL,

    -- forecast_date: 날씨 예보 날짜
    forecast_date    DATE         NOT NULL,

    -- 기온 정보 (단위: °C, 소수 가능하므로 FLOAT 사용)
    temp_min         FLOAT,
    temp_max         FLOAT,

    -- 강수 확률 (0~100 사이 정수, %)
    precipitation_prob INTEGER,

    -- 풍속 (단위: m/s)
    wind_speed       FLOAT,

    -- 날씨 상태 (맑음/구름많음/흐림/비/눈/소나기 등 한글 텍스트)
    condition        VARCHAR(20),

    -- 데이터 출처 (short_term=단기예보, mid_term=중기예보)
    source           VARCHAR(20)  NOT NULL DEFAULT 'short_term',

    -- 생성/수정 시각 (자동 기록)
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- 인덱스: meet_code + forecast_date 조합으로 자주 조회하므로 복합 인덱스 생성
-- idx_ 접두사는 프로젝트 DB 인덱스 네이밍 규칙 (규칙 12)
CREATE INDEX IF NOT EXISTS idx_weather_forecasts_meet_code_date
    ON weather_forecasts (meet_code, forecast_date);

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE 'weather_forecasts 테이블 생성 완료';
END $$;
