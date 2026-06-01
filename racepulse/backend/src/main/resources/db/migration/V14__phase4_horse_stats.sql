-- =============================================================================
-- V14__phase4_horse_stats.sql — Phase 4 경주마/경주로 통계 컬럼 추가
-- =============================================================================
-- 추가 배경:
--   raceHorseResult_2 API 수집을 통해 경주마 통산/최근1년 승률·복승률을 저장합니다.
--   Track_1 API 수집을 통해 경주별 함수율(moistContent)을 저장합니다.
--   이 수치들은 ML 예측의 핵심 feature로 사용됩니다.
-- =============================================================================

-- horses 테이블 — 경주마 성적 통계 컬럼 추가
ALTER TABLE horses
    ADD COLUMN IF NOT EXISTS win_rate_total   NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS win_rate_recent  NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS place_rate_total NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS debut_year       INTEGER;

-- races 테이블 — 함수율 컬럼 추가 (Track_1 API 제공, % 단위)
ALTER TABLE races
    ADD COLUMN IF NOT EXISTS moisture_level NUMERIC(4, 1);
