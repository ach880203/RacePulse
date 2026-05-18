-- =============================================================================
-- V11: races 테이블 ENUM 컬럼 복원
-- =============================================================================
-- V4(fix_enum_columns_to_varchar)에서 races의 ENUM 컬럼을 VARCHAR로 변경했으나,
-- FastAPI ORM 모델(race.py)이 build_db_enum()으로 PostgreSQL ENUM 타입을 기대하므로
-- WHERE races.track_condition = $1::track_condition 형태의 쿼리가
-- "operator does not exist: character varying = track_condition" 에러를 냅니다.
-- races 테이블의 5개 컬럼을 원래 PostgreSQL ENUM 타입으로 복원합니다.
-- =============================================================================

-- 안전장치: ENUM에 없는 값이 들어있으면 USING 캐스트가 실패하므로 NULL로 초기화합니다.
-- (status는 NOT NULL이라 제외)

UPDATE races SET track_condition = NULL
    WHERE track_condition IS NOT NULL
      AND track_condition NOT IN ('DRY', 'WET', 'HUMID', 'SATURATED');

UPDATE races SET race_grade = NULL
    WHERE race_grade IS NOT NULL
      AND race_grade NOT IN ('일반', '중요', '특별', '국제');

UPDATE races SET pace_scenario = NULL
    WHERE pace_scenario IS NOT NULL
      AND pace_scenario NOT IN ('FAST', 'MODERATE', 'SLOW', 'CONTESTED');

UPDATE races SET pace_advantage = NULL
    WHERE pace_advantage IS NOT NULL
      AND pace_advantage NOT IN ('FRONT', 'STALKER', 'CLOSER');

-- VARCHAR → PostgreSQL ENUM 타입으로 변환
ALTER TABLE races
    ALTER COLUMN track_condition TYPE track_condition
    USING track_condition::track_condition;

ALTER TABLE races
    ALTER COLUMN status TYPE race_status
    USING status::race_status;

ALTER TABLE races
    ALTER COLUMN race_grade TYPE race_grade
    USING race_grade::race_grade;

ALTER TABLE races
    ALTER COLUMN pace_scenario TYPE pace_scenario
    USING pace_scenario::pace_scenario;

ALTER TABLE races
    ALTER COLUMN pace_advantage TYPE pace_advantage
    USING pace_advantage::pace_advantage;
