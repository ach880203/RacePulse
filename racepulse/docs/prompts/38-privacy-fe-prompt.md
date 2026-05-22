# 38. RacePulse 개인정보보호법 FE + 사행성 팝업 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, FE 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개 (컬러 하드코딩 금지 등)
```

**선행 조건**: `prompt-36 (개인정보보호법 BE)` 완료 — `/api/v1/privacy`, `/api/v1/terms`, `/api/v1/user/consent` API 사용 가능

---

## 🗂️ 지금까지 한 작업 요약

### FE 현황
- **스택**: React 18 / TypeScript / Tailwind CSS v4 / Vite
- **디자인**: "Bloomberg Terminal × Premium Sports Analytics"
- **컬러 토큰**: `brand-navy-950`(배경) / `brand-gold-400`(골드) — 하드코딩 금지
- **폰트**: Playfair Display(브랜드) / Inter(본문) / JetBrains Mono(수치)
- **라우팅**: `App.tsx` — React Router v6, lazy import 패턴
- **API 호출**: `src/api/` 폴더 분리 규칙 (규칙 9)

### 14차 회의 확정사항 (사행성 팝업)
- 별도 팝업 방식 (페이지 진입 시 오버레이)
- 스크롤을 끝까지 내려야 "확인함" 버튼 활성화
- "확인함" 클릭 후 "동의하기" 버튼 클릭 2단계
- 동의 완료 → `localStorage`에 저장 + BE `/api/v1/user/consent` 저장
- 재방문 시: 이미 동의한 유저는 "동의하였음 + 날짜" + 닫기만 표시

---

## 목표

새 파일 4개 + 기존 파일 수정 2개를 작성합니다.

**신규:**
1. `src/pages/PrivacyPage.tsx` — 개인정보처리방침 페이지
2. `src/pages/TermsPage.tsx` — 이용약관 페이지
3. `src/components/TermsConsentModal.tsx` — 사행성+약관 팝업 (핵심)
4. `src/api/privacyApi.ts` — 약관/동의 API 호출

**수정:**
5. `src/App.tsx` — `/privacy`, `/terms` 라우트 추가 + `TermsConsentModal` 마운트
6. `src/components/layout/Header.tsx` — 푸터 영역 약관 링크 추가

---

## 프로젝트 환경

- **FE**: React 18 / TypeScript / Tailwind CSS v4 / Vite
- **BE API**:
  - `GET /api/v1/privacy` → `{ version, effectiveDate, content }`
  - `GET /api/v1/terms` → `{ version, effectiveDate, content }`
  - `GET /api/v1/user/consent` → `{ termsAgreed, termsAgreedAt, termsVersion, needsReConsent, marketingAgreed }`
  - `POST /api/v1/user/consent` → 동의 저장

---

## 구현 사항

### 1. `src/api/privacyApi.ts`

```typescript
// src/api/privacyApi.ts
// 개인정보처리방침 / 이용약관 / 동의 상태 관련 API 호출 함수들

export const fetchPrivacyPolicy = async () => { ... }
export const fetchTerms = async () => { ... }
export const fetchConsentStatus = async () => { ... }  // 로그인 유저만
export const updateConsent = async (params: {
  termsAgreed: boolean
  marketingAgreed: boolean
}) => { ... }
```

### 2. `src/pages/PrivacyPage.tsx` / `TermsPage.tsx`

- `GET /api/v1/privacy` (또는 `/terms`) 호출 → 내용 렌더링
- 로딩 중: `LoadingAnimation` 컴포넌트 재사용
- 스타일:
  ```
  배경: brand-navy-950
  제목: Playfair Display, brand-gold-400
  본문: Inter, white/80
  버전/날짜: JetBrains Mono, white/40
  ```
- 화면 레이아웃:
  ```
  ┌──────────────────────────────┐
  │ 🏇 RacePulse                 │
  │ 개인정보처리방침              │
  │ 버전 1.0 · 2026-06-01 시행   │
  ├──────────────────────────────┤
  │ 제1조 (목적)                  │
  │ ...                          │
  │ 제2조 (수집 항목)             │
  │ ...                          │
  └──────────────────────────────┘
  ```

### 3. `src/components/TermsConsentModal.tsx` (핵심 구현)

**동작 흐름:**
```
앱 최초 로드 시
  ↓
localStorage 확인
  ├─ 동의 기록 없음 → 팝업 표시 (미동의)
  └─ 동의 기록 있음 → 팝업 숨김 (이미 동의)

팝업 표시 시:
  ┌─────────────────────────────────────────┐
  │ 서비스 이용약관 및 사행성 안내           │
  │ ─────────────────────────────────────── │
  │ [약관 내용 스크롤 영역]                  │
  │  ...                                    │
  │  본 해설은 순수 데이터 분석 목적이며    │
  │  베팅 등 사행 행위와 무관합니다.        │  ← 스크롤 끝
  │ ─────────────────────────────────────── │
  │ [골드 스크롤 진행 바]                   │
  │                                         │
  │ [ 확인함 ✓ ] (스크롤 완료 전 비활성)   │
  │ [ 동의하기 ] (확인함 클릭 후 활성)      │
  │                                         │
  │ □ 마케팅 정보 수신 동의 (선택)          │
  └─────────────────────────────────────────┘
```

**구현 상세:**

```typescript
// localStorage 키
const CONSENT_KEY = 'racepulse_terms_agreed'
const CONSENT_DATE_KEY = 'racepulse_terms_agreed_at'
const TERMS_VERSION_KEY = 'racepulse_terms_version'
const CURRENT_VERSION = '1.0'

// 스크롤 감지 로직
const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
  const el = e.currentTarget
  // 스크롤이 끝까지 도달하면 (오차 10px 허용)
  const isBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 10
  if (isBottom) setScrolled(true)
}

// 동의 완료 처리
const handleAgree = async () => {
  // 1. localStorage 저장
  localStorage.setItem(CONSENT_KEY, 'true')
  localStorage.setItem(CONSENT_DATE_KEY, new Date().toISOString())
  localStorage.setItem(TERMS_VERSION_KEY, CURRENT_VERSION)
  
  // 2. 로그인 상태라면 BE에도 저장
  if (isLoggedIn) {
    await updateConsent({ termsAgreed: true, marketingAgreed })
  }
  
  setOpen(false)
}
```

**재방문 시 (이미 동의한 유저):**
```
┌─────────────────────────────────────────┐
│ 서비스 이용약관 및 사행성 안내           │
│ ─────────────────────────────────────── │
│ ✅ 2026-06-01에 동의하셨습니다          │
│ (버전 1.0)                              │
│ ─────────────────────────────────────── │
│             [ 닫기 ]                    │
└─────────────────────────────────────────┘
```

**약관 재동의 필요 시** (`needsReConsent: true`):
- 기존 동의가 있어도 새 버전이 있으면 팝업 재표시

**스타일:**
- 오버레이: `bg-black/70 backdrop-blur-sm`
- 모달: `bg-brand-navy-900 border border-brand-gold-600/30 rounded-2xl`
- 스크롤 진행 바: 골드 색상, 스크롤 % 에 따라 너비 변화 (동적 UI 30번)
- "확인함" 비활성: `opacity-30 cursor-not-allowed`
- "확인함" 활성: `border-brand-gold-400 text-brand-gold-400`
- "동의하기": `bg-brand-gold-400 text-brand-navy-950 font-bold`

### 4. `src/App.tsx` 수정

```tsx
// lazy import 추가
const PrivacyPage = lazy(() => import('./pages/PrivacyPage'))
const TermsPage = lazy(() => import('./pages/TermsPage'))

// Routes 안에 추가
<Route path="/privacy" element={<PrivacyPage />} />
<Route path="/terms" element={<TermsPage />} />

// BrowserRouter 안, Suspense 위에 추가
<TermsConsentModal />
```

### 5. `src/components/layout/Header.tsx` 수정

푸터 영역(또는 헤더 하단)에 약관 링크 추가:
```tsx
<Link to="/terms" className="text-white/40 hover:text-white/70 text-xs">이용약관</Link>
<span className="text-white/20">·</span>
<Link to="/privacy" className="text-white/40 hover:text-white/70 text-xs">개인정보처리방침</Link>
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `localStorage`가 무엇인지 설명 (브라우저에 영구 저장, 탭 닫아도 유지)
- `scrollHeight - scrollTop <= clientHeight` 공식 설명 (스크롤 끝 감지)
- `backdrop-blur-sm`이 무엇인지 설명 (배경을 흐리게 만드는 CSS 효과)
- `needsReConsent`가 왜 필요한지 설명 (약관 버전 업 시 재동의 유도)
- 왜 localStorage와 BE 둘 다 저장하는지 설명 (로그아웃 후에도 UX, 법적 증거용)
- `lazy(() => import(...))` 가 왜 필요한지 설명 (필요할 때만 코드 다운로드)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-fe-privacy
커밋 메시지: feat: [prompt-38] 개인정보보호법 FE — /privacy · /terms 페이지 + 사행성 약관 팝업 (스크롤 2단계 동의)
```

---

## 완료 기준

```bash
# 1. FE 빌드 성공
cd racepulse/frontend
npm run build

# 2. 개발 서버에서 확인
npm run dev

# 3. 동작 확인
# - localhost:5173/privacy → 개인정보처리방침 페이지 표시
# - localhost:5173/terms → 이용약관 페이지 표시
# - localhost:5173/ 최초 접속 → 사행성 팝업 표시
# - 팝업에서 스크롤 전 "확인함" 버튼 비활성 확인
# - 스크롤 완료 → "확인함" 활성화 → 클릭 → "동의하기" 활성화
# - 동의 후 localStorage에 racepulse_terms_agreed=true 저장 확인
# - 재접속 시 팝업 미표시 확인
```
