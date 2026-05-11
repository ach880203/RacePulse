-- =============================================================================
-- V4: races 테이블의 PostgreSQL 커스텀 ENUM 컬럼을 varchar로 변경
-- =============================================================================
-- 문제: FastAPI(SQLAlchemy)가 race_status, track_condition 등을 PostgreSQL 커스텀
--       ENUM 타입으로 생성했지만, Hibernate는 @Enumerated(EnumType.STRING)으로
--       JDBC 파라미터를 character varying으로 바인딩합니다.
--       결과: "operator does not exist: race_status = character varying" 에러 발생
--
-- 해결: 해당 컬럼들을 varchar로 변경합니다.
--       - SQLAlchemy는 create_type=False 설정으로 타입 이름만 참조했으므로 영향 없음
--       - Hibernate @Enumerated(EnumType.STRING)은 varchar 컬럼과 정상 동작
-- =============================================================================

-- 1. status 컬럼: race_status ENUM → varchar(20)
ALTER TABLE races
    ALTER COLUMN status TYPE varchar(20) USING status::text;

-- 2. track_condition 컬럼: track_condition ENUM → varchar(20)
ALTER TABLE races
    ALTER COLUMN track_condition TYPE varchar(20) USING track_condition::text;

-- 3. pace_scenario 컬럼: pace_scenario ENUM → varchar(20)
ALTER TABLE races
    ALTER COLUMN pace_scenario TYPE varchar(20) USING pace_scenario::text;

-- 4. pace_advantage 컬럼: pace_advantage ENUM → varchar(20)
ALTER TABLE races
    ALTER COLUMN pace_advantage TYPE varchar(20) USING pace_advantage::text;

-- 5. race_grade 컬럼: race_grade ENUM → varchar(50)
--    (한글 값 "일반/중요/특별/국제" 포함, Spring Boot에서 String으로 처리)
ALTER TABLE races
    ALTER COLUMN race_grade TYPE varchar(50) USING race_grade::text;
