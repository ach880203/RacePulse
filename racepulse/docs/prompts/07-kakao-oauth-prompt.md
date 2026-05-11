# 07. RacePulse 카카오 OAuth 연동 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
Spring Boot 백엔드에 카카오 OAuth 2.0 로그인을 구현합니다.
카카오 로그인 → JWT 발급 → 재방문 시 자동 로그인까지 구현합니다.

---

## 프로젝트 환경
- Java 21
- Spring Boot 3.5.14
- Spring Security 6.x
- Spring Data JPA
- jjwt 0.12.6
- Spring Data Redis
- PostgreSQL 16
- 패키지 루트: `com.racepulse.backend`

---

## 현재 파일 구조
```
src/main/java/com/racepulse/backend/
├── BackendApplication.java
├── domain/
│   ├── user/              ← 이번에 작업
│   ├── race/              ← 02번 프롬프트로 생성됨
│   ├── horse/             ← 02번 프롬프트로 생성됨
│   ├── prediction/
│   └── commentary/
└── global/
    ├── config/
    │   └── SecurityConfig.java   ← 수정 필요
    ├── security/          ← 이번에 작업
    ├── exception/
    └── response/
        ├── HealthController.java
        └── ApiResponse.java      ← 02번 프롬프트로 생성됨
```

---

## 카카오 앱 정보 (이미 등록 완료)
```
카카오 개발자 센터: developers.kakao.com
REST API 키: 환경변수 KAKAO_CLIENT_ID
Client Secret: 환경변수 KAKAO_CLIENT_SECRET
Redirect URI: http://localhost:8080/api/v1/auth/kakao/callback
제공 스코프: profile_nickname, account_email
```

---

## DB 테이블 (이미 생성됨)
```sql
-- users 테이블 주요 컬럼
id UUID PRIMARY KEY
email VARCHAR(255) UNIQUE
password VARCHAR(255) NULLABLE        ← 카카오 유저는 비밀번호 없음
kakao_id VARCHAR(100) UNIQUE NULLABLE ← 카카오 유저 고유 ID
auth_provider ENUM('LOCAL', 'KAKAO')
nickname VARCHAR(50)
role ENUM('USER', 'ADMIN')
tier ENUM('FREE', 'PRO')

-- refresh_tokens 테이블
id, user_id(FK), token_hash, family_id(UUID),
is_used(BOOL), expires_at, created_at
```

---

## 구현할 API 엔드포인트
```
GET  /api/v1/auth/kakao             ← 카카오 로그인 시작 (카카오 로그인 페이지로 리다이렉트)
GET  /api/v1/auth/kakao/callback    ← 카카오 OAuth 콜백 처리
POST /api/v1/auth/login             ← 이메일 로그인
POST /api/v1/auth/register          ← 이메일 회원가입
POST /api/v1/auth/logout            ← 로그아웃
POST /api/v1/auth/refresh           ← Access Token 재발급
GET  /api/v1/auth/me                ← 내 정보 조회
```

---

## 구현 파일 목록

### 1. User Entity
`domain/user/entity/User.java`
- users 테이블과 매핑되는 Entity 클래스

### 2. User Repository
`domain/user/repository/UserRepository.java`
- `findByEmail()`, `findByKakaoId()` 메서드

### 3. JWT 유틸리티
`global/security/JwtTokenProvider.java`
- Access Token 생성 (유효기간: 1시간)
- Refresh Token 생성 (유효기간: 24시간 / 로그인 유지 시 3일)
- 토큰 검증
- 토큰에서 userId, role 추출

JWT 페이로드:
```json
{ "userId": "uuid", "role": "USER", "tier": "FREE", "exp": 1234567890 }
```

### 4. JWT 필터
`global/security/JwtAuthenticationFilter.java`
- 모든 요청에서 Authorization 헤더의 JWT 검증
- 유효하면 SecurityContext에 인증 정보 저장
- 무효하면 다음 필터로 넘김 (401 처리는 SecurityConfig에서)

### 5. Refresh Token 서비스
`global/security/RefreshTokenService.java`
- Refresh Token 저장 (PostgreSQL refresh_tokens 테이블)
- Token Rotation: 사용된 토큰은 is_used=true 처리
- Token Family 탈취 감지: 이미 사용된 토큰 재사용 시 해당 family 전체 무효화
- Redis 블랙리스트 관리

### 6. 카카오 OAuth 서비스
`domain/user/service/KakaoOAuthService.java`
- 카카오 인가 코드 → 카카오 Access Token 교환
- 카카오 Access Token → 카카오 유저 정보 조회
- 신규 유저: DB에 저장 후 JWT 발급
- 기존 유저: JWT 재발급

### 7. Auth Controller
`domain/user/controller/AuthController.java`
- 위 7개 엔드포인트 구현

### 8. SecurityConfig 수정
`global/config/SecurityConfig.java`
- JWT 필터 추가 (UsernamePasswordAuthenticationFilter 앞에)
- 인증 불필요 경로 추가:
  - `/api/v1/auth/**`
  - `/api/v1/races/**`, `/api/v1/horses/**`, `/api/v1/racecourses/**`
  - `/api/v1/health`, `/swagger-ui/**`, `/api-docs/**`

---

## 보안 설정

### JWT 설정
```
Access Token  유효기간: 1시간
Refresh Token 유효기간: 24시간 (로그인 유지 선택 시 3일)
저장 위치: HttpOnly Cookie + Redis 블랙리스트
```

### Token Family 탈취 감지
```
1. 로그인 시 family_id(UUID) 생성
2. Refresh Token 사용 시 is_used = true 처리
3. 이미 used=true인 토큰으로 요청 오면
   → 해당 family_id의 모든 토큰 무효화
   → 유저 강제 로그아웃
```

### Rate Limiting
```
로그인 5회 실패 → 15분 잠금 (Redis로 카운터 관리)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- OAuth 2.0 흐름 전체를 단계별로 설명 (인가코드 → 토큰 → 유저정보)
- JWT 구조 설명 (Header.Payload.Signature)
- Token Rotation, Token Family 개념 쉽게 설명
- HttpOnly Cookie가 왜 보안에 좋은지 설명
- Spring Security Filter Chain 동작 순서 설명
- `SecurityContext`가 무엇인지 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- IntelliJ: File → File Properties → File Encoding → UTF-8
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `GET http://localhost:8080/api/v1/auth/kakao` 접속 시 카카오 로그인 페이지로 이동
2. 카카오 로그인 완료 후 JWT Access Token 발급 확인
3. `GET http://localhost:8080/api/v1/auth/me` → 로그인한 유저 정보 응답
4. `POST http://localhost:8080/api/v1/auth/refresh` → 새 Access Token 발급
5. Swagger UI에서 7개 인증 API 확인
6. DB `users` 테이블에 카카오 유저 정보 저장 확인
