# 04. RacePulse 홈 페이지 뼈대 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
RacePulse 홈 페이지(`/`)와 경주 목록 페이지(`/races`)의 기본 레이아웃을 구현합니다.
실제 데이터 연동은 아직 하지 않고, 레이아웃과 더미 데이터로 UI 뼈대를 만듭니다.

---

## 프로젝트 환경
- React 18 + TypeScript
- Vite 6.x
- Tailwind CSS v4
- React Router v6
- @tanstack/react-query (설치됨, 아직 미사용)
- 포트: 3000

---

## 디자인 스펙
```
기본 톤:     다크 모드 (배경: brand-navy-950 = #080e1f)
포인트 색상: brand-gold-400 (#f5c842)
제목 폰트:   Playfair Display (font-heading)
본문 폰트:   Inter (font-body)
레이아웃:    Mobile First (모바일 우선 반응형)
```

⚠️ 컬러는 반드시 Tailwind 토큰만 사용 (`text-brand-gold-400`, `bg-brand-navy-950` 등)
하드코딩(`#f5c842`) 절대 금지

---

## 현재 파일 구조
```
frontend/src/
├── App.tsx          ← 라우팅 설정 (이미 있음)
├── main.tsx
├── index.css        ← Tailwind + 브랜드 토큰 (이미 있음)
├── api/             ← 빈 폴더 (API 호출 파일 위치)
└── pages/           ← 없으면 새로 만들기
    ← 이 폴더에 페이지 컴포넌트 만들기
```

---

## 구현 파일 목록

### 1. 공통 레이아웃 컴포넌트
`src/components/layout/Header.tsx`
- RacePulse 로고 (텍스트 or 간단한 SVG)
- 네비게이션: 홈 / 경주 / 경주마 / 대시보드
- 우측: 로그인 버튼
- 다크 네이비 배경, 골드 포인트

`src/components/layout/Layout.tsx`
- Header + children(페이지 내용) + Footer 구조
- 모든 페이지에서 공통으로 사용할 레이아웃 래퍼

### 2. 홈 페이지
`src/pages/HomePage.tsx`

구성 섹션:
```
① 히어로 섹션
   - 큰 타이틀: "경마를 데이터로 분석하다"
   - 서브타이틀: "AI 기반 경주 예측 플랫폼"
   - 경주 목록 보기 버튼 (brand-gold 색상)
   - 배경: brand-navy-950

② 오늘의 경주 섹션
   - "오늘의 경주" 제목
   - 더미 경주 카드 3개 표시 (실제 데이터 없음)
   - 카드 내용: 경마장명 / 경주번호 / 출발시간 / 상태뱃지(준비중)
   - // TODO: [Phase 1] Spring Boot API 연동 후 실제 데이터로 교체

③ 예측 정확도 섹션
   - "누적 예측 정확도" 제목
   - 더미 수치: Top-1: 42% / Top-3: 68%
   - 원형 게이지 대신 간단한 텍스트+바로 표시
   - // TODO: [Phase 2] 실제 정확도 데이터 연동
```

### 3. 경주 목록 페이지
`src/pages/RaceListPage.tsx`

구성:
```
① 필터 바
   - 경마장 선택: 전체 / 서울 / 부산 / 제주
   - 날짜 선택 (오늘 기본)

② 경주 카드 목록
   - 더미 경주 5개 표시
   - 카드: 경주번호 / 경주명 / 거리 / 출발시간 / 상태
   - 카드 클릭 시 /races/:raceId 로 이동 (React Router Link)
   - // TODO: [Phase 1] Spring Boot /api/v1/races API 연동

③ 데이터 없을 때 표시
   - "경주 데이터를 불러오는 중입니다" 메시지
   - 준비중 뱃지 스타일로 표시
```

### 4. App.tsx 수정
기존 Placeholder 컴포넌트 대신 실제 페이지 컴포넌트로 교체
- `/` → HomePage
- `/races` → RaceListPage
- 나머지는 Placeholder 유지

---

## 더미 데이터 예시
실제 API 연동 전까지 사용할 하드코딩 더미 데이터입니다.
```ts
const dummyRaces = [
  { id: 1, meetCode: 'SC', raceName: '서울 1경주', distance: 1200, startTime: '11:00', status: 'SCHEDULED' },
  { id: 2, meetCode: 'SC', raceName: '서울 2경주', distance: 1400, startTime: '11:40', status: 'SCHEDULED' },
  { id: 3, meetCode: 'BU', raceName: '부산 1경주', distance: 1000, startTime: '11:10', status: 'SCHEDULED' },
]
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `props`, `children`, `Link`, `useNavigate` 등 개념 쉽게 설명
- Tailwind 클래스 조합이 복잡한 경우 "이 클래스가 하는 일" 설명
- Mobile First 반응형 (`sm:`, `md:`, `lg:`)이 어떻게 동작하는지 설명
- 더미 데이터 사용 이유와 나중에 교체할 위치 TODO로 표시

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 확인

---

## 완료 기준
1. `http://localhost:3000` 접속 시 홈 페이지 표시 (히어로 + 경주 카드 + 정확도)
2. `http://localhost:3000/races` 접속 시 경주 목록 표시 (필터 + 더미 카드 5개)
3. 경주 카드 클릭 시 `/races/1` 로 이동 확인
4. 모바일 화면(375px)에서 레이아웃 깨지지 않음 확인 (Chrome 개발자 도구 → 모바일 뷰)
5. 다크 네이비 배경, 골드 포인트 컬러 정상 적용 확인
