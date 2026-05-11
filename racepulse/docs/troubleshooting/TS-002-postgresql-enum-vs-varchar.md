# TS-002 | operator does not exist: race_status = character varying

- **발생일:** 2026-05-11
- **서버:** Spring Boot 백엔드 (포트 8080)
- **엔드포인트:** `GET /api/v1/races?rcDate=...&status=SCHEDULED`

---

## 에러 메시지

```
ERROR: operator does not exist: race_status = character varying
  Hint: No operator matches the given name and argument types.
        You might need to add explicit type casts.
  Position: 362

org.postgresql.util.PSQLException: ERROR: operator does not exist: race_status = character varying
  at org.postgresql.core.v3.QueryExecutorImpl.receiveErrorResponse(...)
  ...
  at com.racepulse.backend.domain.race.service.RaceService.getRaces(RaceService.java:54)
```

---

## 원인

**FastAPI(SQLAlchemy)와 Spring Boot(Hibernate)가 같은 PostgreSQL 테이블을 공유할 때 발생하는 타입 불일치.**

### FastAPI 쪽 (원인 제공)

`V1__create_basic_race_tables.sql` 및 SQLAlchemy 모델이 `races.status`를
PostgreSQL **커스텀 ENUM 타입**(`race_status`)으로 생성했다.

```sql
-- V1__create_basic_race_tables.sql (문제가 된 부분)
CREATE TYPE race_status AS ENUM ('SCHEDULED', 'COMPLETED', 'CANCELLED');

CREATE TABLE races (
    ...
    status race_status NOT NULL,   -- ← 커스텀 ENUM 타입
    track_condition track_condition,
    pace_scenario pace_scenario,
    pace_advantage pace_advantage,
    race_grade race_grade,
    ...
);
```

```python
# ml-server/app/models/race.py (문제가 된 부분)
class Race(Base):
    status: Mapped[RaceStatusEnum] = mapped_column(
        build_db_enum(RaceStatusEnum, "race_status"),  # ← PostgreSQL ENUM 타입 참조
        nullable=False,
    )
```

### Spring Boot 쪽 (에러 발생)

Hibernate의 `@Enumerated(EnumType.STRING)`은 JDBC 파라미터를 **`character varying`(varchar)** 으로 바인딩한다.

```java
// Race.java (문제가 된 부분)
@Enumerated(EnumType.STRING)        // ← 문자열로 바인딩
@Column(nullable = false, length = 20)
private RaceStatus status;
```

PostgreSQL이 실행하는 쿼리:
```sql
-- Hibernate가 생성하는 SQL (파라미터 바인딩)
WHERE r1_0.status = ?
-- PostgreSQL 내부: race_status = character varying  → 에러!
-- PostgreSQL은 커스텀 ENUM ↔ varchar 사이 암묵적 형변환을 지원하지 않는다
```

---

## 해결 방법

### Flyway 마이그레이션 추가 (V4)

`backend/src/main/resources/db/migration/V4__fix_enum_columns_to_varchar.sql` 생성:

```sql
-- 해결 전: status 컬럼 타입 = race_status (PostgreSQL 커스텀 ENUM)
-- 해결 후: status 컬럼 타입 = varchar(20)

ALTER TABLE races
    ALTER COLUMN status TYPE varchar(20) USING status::text;

ALTER TABLE races
    ALTER COLUMN track_condition TYPE varchar(20) USING track_condition::text;

ALTER TABLE races
    ALTER COLUMN pace_scenario TYPE varchar(20) USING pace_scenario::text;

ALTER TABLE races
    ALTER COLUMN pace_advantage TYPE varchar(20) USING pace_advantage::text;

ALTER TABLE races
    ALTER COLUMN race_grade TYPE varchar(50) USING race_grade::text;
```

Spring Boot 재시작 시 Flyway가 자동으로 실행한다.

### 왜 SQLAlchemy는 영향이 없는가?

`build_db_enum()`에서 `create_type=False`로 설정했기 때문에 SQLAlchemy는
PostgreSQL ENUM 타입 이름만 참조할 뿐 타입 강제 캐스팅을 하지 않는다.
컬럼이 varchar로 바뀌어도 문자열 값 그대로 읽고 쓰므로 정상 동작한다.

```python
# ml-server/app/models/race.py
def build_db_enum(enum_class, enum_name):
    return SqlEnum(
        enum_class,
        name=enum_name,
        create_type=False,      # ← 타입 생성/강제 캐스팅 안 함 → varchar 변환 후에도 OK
        values_callable=lambda members: [m.value for m in members],
    )
```

---

## 수정 전 / 수정 후

### 수정 전 (에러)

```
races.status 컬럼 타입: race_status (PostgreSQL 커스텀 ENUM)
Hibernate 파라미터 타입: character varying
결과: operator does not exist: race_status = character varying
```

### 수정 후 (정상)

```
races.status 컬럼 타입: varchar(20)
Hibernate 파라미터 타입: character varying
결과: 정상 비교 가능 → 에러 없음
```

---

## 교훈: FastAPI + Spring Boot 혼용 시 주의사항

FastAPI(SQLAlchemy)와 Spring Boot(Hibernate)가 같은 DB를 공유할 때,
**PostgreSQL 커스텀 ENUM 타입은 반드시 피해야 한다.**

| 구분 | 권장 방식 | 이유 |
|------|-----------|------|
| SQLAlchemy 컬럼 선언 | `String(20)` 또는 `create_type=False` | Hibernate와 타입 충돌 방지 |
| Flyway 테이블 생성 | `VARCHAR(20)` | 두 프레임워크 모두 호환 |
| Hibernate 엔티티 | `@Enumerated(EnumType.STRING)` | VARCHAR 컬럼과 정상 동작 |

**앞으로 테이블을 신규 생성할 때는 Flyway SQL에서 커스텀 ENUM 대신 VARCHAR를 사용할 것.**
