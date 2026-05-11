# 02. RacePulse Spring Boot 기본 API 구현 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

## 목표
Spring Boot 백엔드에 경마 데이터 조회를 위한 기본 API 3개를 구현합니다.
`/api/v1/racecourses`, `/api/v1/races`, `/api/v1/horses` 엔드포인트를 만듭니다.

---

## 프로젝트 환경
- Java 21
- Spring Boot 3.5.14
- Spring Data JPA + QueryDSL
- PostgreSQL 16 (Docker)
- Lombok
- MapStruct
- SpringDoc OpenAPI (Swagger)
- Flyway (마이그레이션 관리)
- 패키지 루트: `com.racepulse.backend`

---

## 현재 패키지 구조
```
src/main/java/com/racepulse/backend/
├── BackendApplication.java
├── domain/
│   ├── user/
│   ├── race/        ← 이번에 작업
│   ├── horse/       ← 이번에 작업
│   ├── prediction/
│   └── commentary/
└── global/
    ├── config/
    │   └── SecurityConfig.java  (이미 있음)
    ├── security/
    ├── exception/
    └── response/
        └── HealthController.java  (이미 있음)
```

---

## 데이터베이스 테이블 정보

### racecourses 테이블 (이미 데이터 3개 입력됨)
```sql
id, meet_code(SC/BU/JJ), name, location, track_types(JSONB), created_at
```
기본 데이터:
- SC → 서울경마공원 / 경기도 과천시
- BU → 부산경남경마공원 / 부산광역시 강서구
- JJ → 제주경마공원 / 제주특별자치도 제주시

### races 테이블
```sql
id, meet_code, rc_date, race_no, race_name, distance, track_type,
track_condition(DRY/WET/HUMID/SATURATED), prize_money, weather,
start_time, status(SCHEDULED/COMPLETED/CANCELLED),
race_class, race_grade(일반/중요/특별/국제),
front_count, pace_scenario(FAST/MODERATE/SLOW/CONTESTED),
pace_advantage(FRONT/STALKER/CLOSER), created_at, updated_at
```

### horses 테이블
```sql
id, name, eng_name, birth_year, sex, color, origin,
father_name, mother_name, owner, meet_code,
rating_1, rating_2, rating_3, rating_4,
coat_color, body_type, photo_url, thumbnail_url,
is_active, created_at, updated_at
```

---

## 구현할 API 3개

### 1. GET /api/v1/racecourses
- 경마장 전체 목록 조회
- 응답: id, meetCode, name, location, trackTypes

### 2. GET /api/v1/races
- 경주 목록 조회 (페이징)
- 쿼리 파라미터:
  - `meetCode` (선택): SC / BU / JJ 필터
  - `rcDate` (선택): 날짜 필터 (yyyy-MM-dd)
  - `status` (선택): SCHEDULED / COMPLETED / CANCELLED
  - `page` (기본값 0), `size` (기본값 20)
- 응답: id, meetCode, rcDate, raceNo, raceName, distance, status, startTime

### 3. GET /api/v1/horses
- 경주마 목록 조회 (페이징)
- 쿼리 파라미터:
  - `meetCode` (선택): 경마장 필터
  - `name` (선택): 이름 검색 (포함 검색)
  - `page` (기본값 0), `size` (기본값 20)
- 응답: id, name, engName, meetCode, sex, rating1, isActive, thumbnailUrl

---

## 구현 파일 목록

각 도메인마다 아래 파일들을 만들어주세요.

### race 도메인
```
domain/race/
├── entity/Race.java           ← DB 테이블과 연결되는 Java 클래스
├── repository/RaceRepository.java  ← DB 조회 메서드 모음
├── dto/RaceResponse.java      ← API 응답 형식 정의
├── service/RaceService.java   ← 비즈니스 로직
└── controller/RaceController.java  ← API 엔드포인트
```

### horse 도메인
```
domain/horse/
├── entity/Horse.java
├── repository/HorseRepository.java
├── dto/HorseResponse.java
├── service/HorseService.java
└── controller/HorseController.java
```

### racecourse 도메인
```
domain/race/                   ← race 도메인 안에 함께 관리
├── entity/Racecourse.java
├── repository/RacecourseRepository.java
├── dto/RacecourseResponse.java
├── service/RacecourseService.java
└── controller/RacecourseController.java
```

---

## 공통 응답 형식
모든 API는 아래 형식으로 감싸서 응답해주세요.

```json
{
  "success": true,
  "data": { ... },
  "message": "조회 성공"
}
```

`global/response/` 패키지에 `ApiResponse.java` 공통 응답 클래스를 만들어주세요.

---

## ENUM 처리
DB에 저장된 ENUM 값들 (예: SCHEDULED, DRY, SC 등)을 Java에서 처리할 수 있도록
각 Entity에 적절한 ENUM 클래스를 만들어주세요.

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 모든 어노테이션(@Entity, @Repository, @Service 등) 의미 설명
- 각 메서드가 하는 일, 파라미터, 반환값 설명
- JPA 관련 개념 (예: @Column, @GeneratedValue, findAll, Page 등) 쉽게 설명
- "이게 뭔지(WHAT)"와 "왜 이렇게 했는지(WHY)" 모두 설명
- Lombok 어노테이션(@Getter, @Builder 등)이 하는 일 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 인코딩 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 반드시 확인
- IntelliJ 기준: File → File Properties → File Encoding → UTF-8 확인

---

## 완료 기준
1. Swagger UI(`http://localhost:8080/swagger-ui.html`)에서 3개 API 확인
2. `GET /api/v1/racecourses` → 경마장 3개 (SC/BU/JJ) 응답
3. `GET /api/v1/races` → 빈 배열 응답 (아직 데이터 없음)
4. `GET /api/v1/horses` → 빈 배열 응답 (아직 데이터 없음)
5. 페이징 파라미터 (`?page=0&size=20`) 동작 확인
