-- =============================================================================
-- V8: jockeys / trainers 테이블 컬럼명 정렬 + 누락 컬럼 추가
-- =============================================================================
-- FastAPI master.py 모델이 license_no / win_rate_total 등을 기대하는데
-- DB에는 jockey_code / trainer_code 로 저장돼 있어 UndefinedColumnError 발생.
-- =============================================================================


-- -----------------------------------------------------------------------------
-- 1. jockeys 테이블
-- -----------------------------------------------------------------------------

-- jockey_code → license_no 이름 변경
ALTER TABLE jockeys
    DROP CONSTRAINT IF EXISTS jockeys_jockey_code_meet_code_key;

ALTER TABLE jockeys
    RENAME COLUMN jockey_code TO license_no;

ALTER TABLE jockeys
    ADD CONSTRAINT jockeys_license_no_meet_code_key UNIQUE (license_no, meet_code);

-- FastAPI Jockey 모델에 있는 누락 컬럼 추가
ALTER TABLE jockeys
    ADD COLUMN IF NOT EXISTS win_rate_total   NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS win_rate_recent  NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS place_rate_total NUMERIC(5, 4);


-- -----------------------------------------------------------------------------
-- 2. trainers 테이블
-- -----------------------------------------------------------------------------

-- trainer_code → license_no 이름 변경
ALTER TABLE trainers
    DROP CONSTRAINT IF EXISTS trainers_trainer_code_meet_code_key;

ALTER TABLE trainers
    RENAME COLUMN trainer_code TO license_no;

ALTER TABLE trainers
    ADD CONSTRAINT trainers_license_no_meet_code_key UNIQUE (license_no, meet_code);

-- FastAPI Trainer 모델에 있는 누락 컬럼 추가
ALTER TABLE trainers
    ADD COLUMN IF NOT EXISTS win_rate_total  NUMERIC(5, 4),
    ADD COLUMN IF NOT EXISTS win_rate_recent NUMERIC(5, 4);
