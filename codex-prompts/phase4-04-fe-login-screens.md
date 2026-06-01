# Codex 프롬프트 — Phase 4-4: FE 인증 화면 구현 (로그인/회원가입/카카오)

## 작업 개요
현재 `/login`, `/register`, `/auth/kakao/callback` 3개가 Placeholder 상태입니다.
PrivateRoute가 로그인 화면으로 리다이렉트하도록 돼 있어서 로그인 화면이 없으면
인증이 필요한 모든 페이지(마이페이지/즐겨찾기/설정)에 접근할 수 없습니다.

## 기술 스택
- React 18 / TypeScript / Tailwind CSS v4
- 기존 BE API: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`, `GET /api/v1/auth/kakao`
- 기존 훅: `useMe`, `useLogout` 등 `src/hooks/useUser.ts`에 존재 (확인 후 사용)
- 디자인: 다크 네이비(`#080e1f`) + 골드(`#f5c842`) — 기존 디자인 시스템 그대로

## 파일 위치
```
racepulse/frontend/src/pages/
├── auth/
│   ├── LoginPage.tsx         ← 신규
│   ├── RegisterPage.tsx      ← 신규
│   └── KakaoCallbackPage.tsx ← 신규
```

---

## 화면 1: 로그인 (`/login`)

### 레이아웃
```
[레이스펄스 로고]

경마를 데이터로 분석하다
AI 기반 경주 예측 플랫폼

[이메일 입력]
[비밀번호 입력]
[로그인 버튼]  ← 골드 배경

─────── 또는 ───────

[카카오로 로그인]  ← 카카오 노란색 버튼

회원이 아니신가요? [회원가입]
```

### 기능 요구사항
1. 이메일/비밀번호 입력 후 `POST /api/v1/auth/login` 호출
2. 성공: 메인 페이지(`/`)로 이동
3. 실패: 이메일/비밀번호 아래 빨간 에러 메시지 표시
4. 카카오 버튼: `GET /api/v1/auth/kakao` 호출 → 카카오 OAuth 리다이렉트
5. 로딩 중 버튼 비활성화

### 코드 작성 규칙
- `react-hook-form` 사용 (기존 프로젝트에 있으면 사용, 없으면 useState로 구현)
- input 포커스 시 골드 테두리 (`focus:border-brand-gold-400`)
- 에러 메시지: 빨간색 `text-red-400` 텍스트
- 주석: 각 함수의 역할과 에러 처리 이유 설명

---

## 화면 2: 회원가입 (`/register`)

### 레이아웃
로그인 화면과 동일한 스타일로:
```
[닉네임 입력]
[이메일 입력]
[비밀번호 입력]
[비밀번호 확인 입력]
[회원가입 버튼]

이미 회원이신가요? [로그인]
```

### 기능 요구사항
1. 비밀번호 ≠ 비밀번호 확인 시 에러 메시지
2. `POST /api/v1/auth/register` 호출
3. 성공: `/login`으로 이동 + "회원가입이 완료되었습니다" Toast
4. 중복 이메일 에러 처리

---

## 화면 3: 카카오 콜백 (`/auth/kakao/callback`)

카카오 OAuth 완료 후 리다이렉트되는 화면입니다.

### 기능 요구사항
1. URL에서 `code` 파라미터 추출: `useSearchParams`
2. 로딩 스피너 표시 ("카카오 로그인 처리 중...")
3. `GET /api/v1/auth/kakao/callback?code=...` 호출
4. 성공: `/`로 이동
5. 실패: `/login`으로 이동 + 에러 Toast

### 구현
```tsx
// URL: /auth/kakao/callback?code=XXXX
// 카카오가 이 주소로 리다이렉트해줌 → code를 꺼내서 BE에 전달
const [searchParams] = useSearchParams()
const code = searchParams.get('code')
```

---

## App.tsx 라우트 등록 업데이트

```tsx
// 기존 Placeholder를 실제 컴포넌트로 교체
const LoginPage = lazy(() => import('./pages/auth/LoginPage'))
const RegisterPage = lazy(() => import('./pages/auth/RegisterPage'))
const KakaoCallbackPage = lazy(() => import('./pages/auth/KakaoCallbackPage'))

// Routes에서:
<Route path="/login"               element={<LoginPage />} />
<Route path="/register"            element={<RegisterPage />} />
<Route path="/auth/kakao/callback" element={<KakaoCallbackPage />} />
```

---

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-4] FE 인증 화면 구현 (로그인/회원가입/카카오)`

### FE 규칙
- **axios**: 기존 `axiosInstance` 사용 — 새 axios 인스턴스 생성 금지 (`src/services/axiosInstance.ts`)
  - 401 refresh 인터셉터, baseURL, 인증 헤더가 이미 포함되어 있음
- **환경변수**: `http://localhost:8080` 하드코딩 절대 금지 — axiosInstance가 자동 처리
- **Toast**: 기존 `Toast` 컴포넌트 재사용 (`src/components/Toast.tsx`) — 새로 만들지 말 것
- **화면 문구**: 화면에 표시되는 모든 텍스트 한글 전용 (변수명·클래스명·enum·브랜드명 제외)
- **라우팅**: `lazy()` + `Suspense` 패턴 유지 (App.tsx 번들 최적화)
- **FE → Spring Boot만**: FastAPI(`localhost:8000`) 직접 호출 금지 — 모든 API는 Spring Boot 경유
- **주석**: 각 함수의 역할과 에러 처리 이유 한 줄 이상

## 디자인 참고
기존 컴포넌트들의 공통 패턴:
```tsx
// 카드 컨테이너
className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8"

// 입력 필드
className="rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white
           outline-none transition-colors focus:border-brand-gold-400"

// 골드 버튼
className="rounded-full bg-brand-gold-400 px-6 py-3 text-sm font-semibold
           text-brand-navy-950 transition-transform hover:-translate-y-0.5"

// 보조 텍스트 링크
className="text-sm text-brand-gold-400 hover:underline"
```

## 완료 기준
- `/login` 접근 시 실제 로그인 폼 표시
- `/register` 접근 시 회원가입 폼 표시
- 로그인 성공 후 `/profile` 접근 가능
- 카카오 버튼 클릭 시 카카오 로그인 페이지로 이동
