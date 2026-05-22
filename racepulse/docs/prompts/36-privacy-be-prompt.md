# 36. RacePulse 개인정보보호법 BE 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, Spring Boot 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (개인정보 처리)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: `prompt-29 (V13 마이그레이션)` 완료 필수
- `users` 테이블에 `marketing_agreed`, `terms_agreed_at`, `terms_version` 컬럼 추가됨

---

## 🗂️ 지금까지 한 작업 요약

### Spring Boot 현황
- `User.java` Entity: `id`, `email`, `password`, `kakaoId`, `authProvider`, `nickname`, `role`, `tier`, `createdAt`, `updatedAt`
- V13에서 추가된 컬럼: `marketing_agreed(BOOLEAN)`, `terms_agreed_at(TIMESTAMPTZ)`, `terms_version(VARCHAR(10))`
- `AuthService.register()`: 회원가입 처리 (동의 처리 없음 → 추가 필요)
- `RegisterRequest.java`: 회원가입 요청 DTO (동의 필드 없음 → 추가 필요)

### 14차 회의 확정사항
- 별도 팝업 방식 (약관 내용 스크롤 완료 → "확인함" 버튼 → "동의하기" 2단계)
- `localStorage`에 동의 날짜 저장 (FE) + DB에도 영구 저장 (BE)
- 재방문 시: 동의한 유저는 "동의하였음 + 날짜" 표시 후 닫기만 가능

---

## 목표

Spring Boot BE에 개인정보보호법 관련 기능을 추가합니다.

1. `User.java` Entity — V13 컬럼 3개 필드 추가
2. `RegisterRequest.java` — 동의 필드 추가
3. `AuthService.register()` — 동의 처리 로직 추가
4. `GET /api/v1/privacy` — 개인정보처리방침 조회 API
5. `GET /api/v1/terms` — 이용약관 조회 API
6. `POST /api/v1/user/consent` — 동의 상태 업데이트 API (USER 권한)
7. `GET /api/v1/user/consent` — 현재 동의 상태 조회 API (USER 권한)

---

## 프로젝트 환경

- **BE**: Spring Boot / Java 21 / JPA / PostgreSQL
- **기존 패키지 참고**:
  - `domain/user/` — User Entity, AuthService, AuthController
  - `global/response/ApiResponse.java` — 공통 응답 (반드시 사용)
  - `global/exception/` — BusinessException, ErrorCode (반드시 사용)

---

## 구현 사항

### 1. `User.java` — V13 컬럼 3개 추가

```java
// 마케팅 정보 수신 동의 여부 (선택 항목 — false가 기본값)
@Column(name = "marketing_agreed", nullable = false)
@Builder.Default
private boolean marketingAgreed = false;

// 이용약관 동의 시각 (가입 완료 시점에 자동 기록)
// OffsetDateTime = 타임존까지 포함한 시각 타입입니다. (KST = UTC+9)
@Column(name = "terms_agreed_at")
private OffsetDateTime termsAgreedAt;

// 동의한 약관 버전 (예: "1.0", "1.1")
// 약관이 개정되면 재동의가 필요한지 판단할 때 사용합니다.
@Column(name = "terms_version", length = 10)
private String termsVersion;
```

현재 약관 버전 상수 추가:
```java
// 현재 서비스 중인 약관 버전 — 약관 개정 시 이 값을 올립니다.
public static final String CURRENT_TERMS_VERSION = "1.0";
```

동의 처리 메서드 추가:
```java
// 이용약관 동의를 기록합니다. (Builder 패턴 외에 동의 업데이트용)
public void agreeToTerms(boolean marketingAgreed) {
    this.termsAgreedAt = OffsetDateTime.now(ZoneId.of("Asia/Seoul"));
    this.termsVersion = CURRENT_TERMS_VERSION;
    this.marketingAgreed = marketingAgreed;
}
```

### 2. `RegisterRequest.java` — 동의 필드 추가

```java
// 이용약관 동의 여부 (필수 — false이면 회원가입 거부)
@NotNull(message = "이용약관 동의는 필수입니다.")
private Boolean termsAgreed;

// 마케팅 정보 수신 동의 여부 (선택)
// null이면 false로 처리합니다.
private Boolean marketingAgreed;
```

### 3. `AuthService.register()` — 동의 처리 추가

```java
// 이용약관 동의 필수 확인
if (!request.getTermsAgreed()) {
    throw new BusinessException(ErrorCode.TERMS_NOT_AGREED);
}

// User 생성 시 동의 정보 포함
User user = User.builder()
    .email(request.getEmail())
    .password(encodedPassword)
    .nickname(request.getNickname())
    .authProvider(AuthProvider.LOCAL)
    .build();

// 동의 정보 기록
user.agreeToTerms(Boolean.TRUE.equals(request.getMarketingAgreed()));
```

`ErrorCode.java`에 추가:
```java
TERMS_NOT_AGREED(400, "TERMS_NOT_AGREED", "이용약관 동의가 필요합니다."),
```

### 4~5. 약관/처리방침 조회 API

`PrivacyController.java` 신규 생성:

```java
// GET /api/v1/privacy — 개인정보처리방침 전문 조회
// GET /api/v1/terms   — 이용약관 전문 조회
```

내용은 `.properties` 또는 DB가 아닌 **코드 내 상수**로 관리:
- 약관 내용이 코드에 있으면 버전 관리(Git)가 자동으로 됩니다.
- `CURRENT_TERMS_VERSION`이 바뀔 때 약관 내용도 함께 커밋합니다.

응답 형식:
```json
{
  "success": true,
  "data": {
    "version": "1.0",
    "effectiveDate": "2026-06-01",
    "content": "제1조 (목적)..."
  }
}
```

약관 내용 예시 (간략 버전 — 실제 법적 검토 후 교체 필요):
```
제1조 (목적)
RacePulse(이하 "서비스")는 경마 데이터 분석 목적으로만 운영됩니다.
이 서비스는 베팅, 도박, 사행 행위와 무관하며 이를 권장하지 않습니다.

제2조 (수집하는 개인정보)
이메일 주소, 닉네임, 서비스 이용 기록

제3조 (이용 목적)
서비스 제공, 공지사항 발송 (마케팅 동의 시 이벤트 안내)

제4조 (보유 기간)
회원 탈퇴 시 즉시 삭제 (관계 법령에 따른 보관 기간 예외)
```

### 6~7. 동의 상태 API (USER 권한)

```java
// POST /api/v1/user/consent — 동의 상태 업데이트 (마케팅 동의 변경 등)
// GET  /api/v1/user/consent — 현재 동의 상태 조회
```

`ConsentResponse.java` DTO:
```java
{
  "termsAgreed": true,
  "termsAgreedAt": "2026-06-01T09:00:00+09:00",
  "termsVersion": "1.0",
  "currentTermsVersion": "1.0",
  "needsReConsent": false,   // termsVersion != currentTermsVersion이면 true
  "marketingAgreed": false
}
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `OffsetDateTime`이 왜 `LocalDateTime`과 다른지 설명 (타임존 포함 여부)
- `terms_version`을 저장하는 이유 설명 (약관 개정 시 재동의 판단)
- `marketingAgreed`가 선택인 이유 설명 (개인정보보호법: 필수/선택 구분 의무)
- `needsReConsent`가 왜 필요한지 설명 (약관 버전 올라가면 재동의 유도)
- `@NotNull` 검증이 왜 DTO에 있어야 하는지 설명 (Controller 레이어 검증)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장
- 한글 약관 내용 깨짐 없이 확인

---

## Git 규칙

```
브랜치: feat/phase3-be-privacy
커밋 메시지: feat: [prompt-36] 개인정보보호법 BE — /privacy · /terms API + 회원가입 동의 처리 + consent API
```

---

## 완료 기준

```bash
# 1. BE 컴파일
cd racepulse/backend
.\gradlew compileJava

# 2. API 동작 확인
curl http://localhost:8080/api/v1/privacy
# → {"success": true, "data": {"version": "1.0", ...}}

curl http://localhost:8080/api/v1/terms
# → {"success": true, "data": {"version": "1.0", ...}}

# 3. 회원가입 동의 없이 시도 → 400 에러
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"pass","nickname":"테스트","termsAgreed":false}'
# → {"success": false, "message": "이용약관 동의가 필요합니다."}

# 4. 동의 포함 회원가입 → 200 성공
curl -X POST http://localhost:8080/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"test@test.com","password":"pass","nickname":"테스트","termsAgreed":true,"marketingAgreed":false}'
# → {"success": true, "data": {...}}
```
