# RacePulse — 의존성 정리 문서

> 작성: WR (서기)
> 최초 작성일: 2026-05-08
> 대상: Spring Boot 백엔드 (backend/)

---

## Spring Initializr에서 추가한 의존성 (9개)

### 1. Spring Web
- **역할**: REST API 서버를 만드는 핵심 의존성
- **하는 일**: HTTP 요청/응답 처리, @RestController, @GetMapping 등 어노테이션 제공
- **쉽게 말하면**: 우리가 만들 39개 API 엔드포인트의 기반이 되는 라이브러리

---

### 2. Spring Security
- **역할**: 인증(로그인)과 인가(권한) 처리
- **하는 일**:
  - 로그인하지 않은 유저 차단
  - GUEST/USER/ADMIN 권한별 접근 제어
  - CORS 설정, CSRF 보호
- **쉽게 말하면**: "이 API는 로그인한 사람만 쓸 수 있다"를 관리하는 경비원

---

### 3. Spring Data JPA
- **역할**: 데이터베이스 연동
- **하는 일**:
  - Java 객체(Entity)를 DB 테이블과 자동으로 연결
  - SQL 없이도 데이터 저장/조회 가능 (`save()`, `findById()` 등)
  - 복잡한 쿼리는 JPQL 또는 QueryDSL로 처리
- **쉽게 말하면**: Java 코드로 DB를 조작할 수 있게 해주는 번역기

---

### 4. PostgreSQL Driver
- **역할**: Java에서 PostgreSQL DB에 실제로 접속하게 해주는 드라이버
- **하는 일**: Spring Data JPA가 PostgreSQL과 통신할 때 필요한 연결 도구
- **쉽게 말하면**: Java ↔ PostgreSQL 사이의 통역사

---

### 5. Spring Data Redis
- **역할**: Redis(인메모리 캐시) 연동
- **하는 일**:
  - Refresh Token 저장/조회/삭제
  - AI 해설 캐싱 (pre_race / post_race 캐시 키)
  - API Rate Limit 카운터 관리
- **쉽게 말하면**: 자주 쓰는 데이터를 빠르게 꺼낼 수 있는 빠른 메모장

---

### 6. Spring Boot Actuator
- **역할**: 서버 상태 모니터링
- **하는 일**:
  - `GET /api/v1/health` 헬스체크 엔드포인트 자동 제공
  - 서버 메모리, DB 연결 상태, 기타 지표 확인 가능
- **쉽게 말하면**: 서버가 지금 살아있는지 확인하는 심전도 모니터

---

### 7. Validation
- **역할**: 입력값 유효성 검사
- **하는 일**:
  - `@NotNull`, `@Email`, `@Size` 등 어노테이션으로 요청 데이터 검증
  - 잘못된 값이 오면 자동으로 400 에러 반환
- **쉽게 말하면**: "이메일 형식이 맞는지", "비밀번호가 8자 이상인지" 자동으로 확인하는 검사관

---

### 8. Flyway Migration
- **역할**: DB 스키마 버전 관리
- **하는 일**:
  - `V1__phase0.sql`, `V2__phase1.sql` 등 파일을 순서대로 자동 실행
  - 이미 실행한 파일은 다시 실행하지 않음 (체크섬으로 추적)
  - 팀원 모두 같은 DB 구조를 유지할 수 있음
- **쉽게 말하면**: DB 변경 이력을 git처럼 관리하는 도구

---

### 9. Lombok
- **역할**: 반복되는 Java 코드 자동 생성
- **하는 일**:
  - `@Getter`, `@Setter`, `@Builder`, `@RequiredArgsConstructor` 등
  - getter/setter/생성자를 직접 타이핑하지 않아도 됨
- **쉽게 말하면**: 귀찮은 반복 코드를 자동으로 써주는 비서

---

## build.gradle에 직접 추가할 의존성 (4개)

> Spring Initializr에 없어서 프로젝트 생성 후 `build.gradle`에 수동으로 추가

---

### 10. QueryDSL
- **역할**: 타입 안전한 복잡한 쿼리 작성
- **하는 일**:
  - JPA만으로 작성하기 어려운 복잡한 조건 쿼리를 Java 코드로 작성
  - 컴파일 시점에 오류 감지 (문자열 SQL보다 안전)
  - 예: "서울 경마장에서 최근 5경주 중 3회 이상 입상한 말 조회"
- **쉽게 말하면**: 복잡한 DB 검색을 SQL 대신 Java로 깔끔하게 작성하는 도구

---

### 11. jjwt (JWT)
- **역할**: JWT 토큰 생성/검증
- **하는 일**:
  - 로그인 시 Access Token, Refresh Token 생성
  - 요청이 올 때 토큰이 유효한지 검증
  - Token Family 탈취 감지 구현
- **쉽게 말하면**: 로그인 상태를 증명하는 디지털 신분증을 만들고 확인하는 도구

---

### 12. MapStruct
- **역할**: 객체 간 변환 자동화
- **하는 일**:
  - Entity(DB 객체) ↔ DTO(API 응답 객체) 자동 변환
  - 직접 변환 코드 작성 없이 어노테이션으로 처리
- **쉽게 말하면**: DB에서 꺼낸 데이터를 API 응답 형식으로 자동으로 바꿔주는 변환기

---

### 13. SpringDoc OpenAPI (Swagger)
- **역할**: API 문서 자동 생성
- **하는 일**:
  - `/swagger-ui.html` 접속하면 39개 API 목록과 테스트 UI 자동 제공
  - 코드 어노테이션 기반으로 문서 자동 업데이트
- **쉽게 말하면**: 우리가 만든 API를 브라우저에서 바로 테스트하고 문서로 볼 수 있게 해주는 도구

---

## 의존성 구조 요약

```
[클라이언트 요청]
      ↓
Spring Web          ← HTTP 요청 받기
Spring Security     ← 인증/권한 확인
Validation          ← 입력값 검사
      ↓
Spring Data JPA     ← DB 조작
QueryDSL            ← 복잡한 쿼리
PostgreSQL Driver   ← PostgreSQL 연결
Flyway              ← DB 스키마 관리
      ↓
Spring Data Redis   ← 캐시/토큰 관리
jjwt                ← JWT 토큰 처리
      ↓
Lombok              ← 코드 자동 생성 (개발 편의)
MapStruct           ← 객체 변환 자동화
Actuator            ← 서버 상태 모니터링
SpringDoc           ← API 문서 자동화
```
