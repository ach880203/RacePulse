-- =============================================================================
-- V10: race_results 컬럼 타입 수정 + UNIQUE 제약 추가
-- =============================================================================
-- V9에서 time_behind(NUMERIC) → margin 으로 이름만 변경했고
-- 타입을 VARCHAR로 바꾸지 않아 INSERT 시 DatatypeMismatchError 발생.
-- data_service.py 가 margin에 '-', '건조 (5%)' 같은 문자열을 저장하므로
-- VARCHAR(30) 으로 변환합니다.
-- ON CONFLICT (race_id, horse_id) 동작을 위한 UNIQUE 제약도 추가합니다.
-- =============================================================================

-- margin: NUMERIC → VARCHAR(30)
ALTER TABLE race_results
    ALTER COLUMN margin TYPE VARCHAR(30) USING margin::TEXT;

-- ON CONFLICT (race_id, horse_id) 를 위한 UNIQUE 제약 추가
ALTER TABLE race_results
    ADD CONSTRAINT race_results_race_id_horse_id_key
    UNIQUE (race_id, horse_id);
