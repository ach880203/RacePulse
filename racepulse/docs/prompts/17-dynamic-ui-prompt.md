# 17. RacePulse 동적 UI 16종 구현 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
RacePulse에서 확정된 16종의 동적 UI 컴포넌트를 구현합니다.
각 컴포넌트는 독립적으로 재사용 가능해야 합니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4 (brand 토큰)
- Recharts (차트)
- CSS Animation / Framer Motion (선택)

---

## 구현할 컴포넌트 16종

모든 컴포넌트는 `src/components/dynamic/` 폴더에 생성합니다.

### 1. ConditionGauge.tsx
컨디션 게이지 애니메이션 (최하~최상 차오르는 효과)
- props: `grade: '최하' | '하' | '중' | '상' | '최상'`
- 세로 또는 가로 바가 위에서 아래로(또는 왼쪽→오른쪽) 채워지는 애니메이션
- 색상: 최하(빨강) → 최상(초록)

### 2. WinProbabilityBar.tsx
예측 승률 바 차트 스윕 애니메이션
- props: `probability: number` (0~100)
- 0%에서 실제 값까지 애니메이션으로 채워짐
- brand-gold-400 색상

### 3. HorseCardHover.tsx
말 카드 호버 시 상세 스탯 팝업 + 미니 성적 차트
- 평소: 이름/기수/배당률 표시
- 호버 시: 최근 5경주 미니 차트 + 상세 스탯 팝업

### 4. ConditionColorBadge.tsx
컨디션 등급 색상 코딩 뱃지
- props: `grade: string`
- 빨강→주황→노랑→연두→초록 색상 뱃지

### 5. RatingRadarChart.tsx
레이팅 레이더 차트 (5각형)
- props: `ratings: { label: string, value: number }[]`
- Recharts RadarChart 사용
- 호버 시 수치 표시

### 6. HorseCardSlideIn.tsx
말 카드 게이트 열리듯 순서대로 슬라이드 인
- 카드 목록이 위→아래 순서로 0.1초 간격으로 슬라이드 인
- CSS transition 또는 Framer Motion 사용

### 7. SimulationAnimation.tsx
경주 시뮬레이션 미니 애니메이션 (Phase 2 - Monte Carlo 연동)
- 간단한 말 아이콘들이 좌→우로 달리는 애니메이션
- // TODO: [Phase 2] Monte Carlo 시뮬레이션 데이터와 연동

### 8. SparklineChart.tsx
성적 추이 스파크라인 (최근 5경주)
- props: `ranks: number[]` (예: [3, 1, 2, 4, 1])
- 상승: 초록 / 하락: 빨강
- Recharts LineChart (미니 버전)

### 9. ResultRevealAnimation.tsx
착순 역순 공개 애니메이션 (5위→1위)
- 경주 결과를 5위부터 1위 순서로 순차 공개
- 각 순위 공개 시 effect 애니메이션

### 10. PaceLineChart.tsx
구간별 기록 라인 차트 (페이스 곡선 비교)
- props: `horses: { name: string, sections: number[] }[]`
- 각 말의 구간 기록을 꺾은선으로 표시
- Recharts LineChart 멀티 라인

### 11. PredictionVsActualGauge.tsx
예측 vs 실제 비교 게이지
- 예측 순위와 실제 순위를 나란히 표시
- 일치 시 골드, 불일치 시 회색

### 12. AccuracyCircleGauge.tsx
예측 정확도 대시보드 원형 게이지 + 카운트업
- props: `accuracy: number` (0~100)
- 0에서 실제 값까지 카운트업 숫자 애니메이션
- 원형 프로그레스 바 (CSS 또는 SVG)
- 70% 이상: 골드 / 미만: 회색

### 13. CollectionCountdown.tsx
다음 수집까지 카운트다운
- props: `nextUpdateAt: string` (ISO 날짜)
- HH:MM:SS 형식 실시간 카운트다운
- `data_status` 뱃지 함께 표시

### 14. RaceStartCountdown.tsx
경기 시작까지 카운트다운
- props: `startTime: string`
- D-day / HH:MM:SS 형식
- 1시간 이내: 골드 색상으로 강조

### 15. TypingAnimation.tsx
AI 해설 타이핑 애니메이션
- props: `text: string, speed?: number`
- 글자가 하나씩 타이핑되는 효과
- 커서 깜빡임 포함

### 16. LoadingAnimation.tsx
로딩 화면: 말 달리기 → 결승선 통과 → 트로피 등장
- CSS 애니메이션으로 말 아이콘이 달리는 효과
- 로딩 완료 시 트로피 아이콘 등장
- brand-gold 색상 사용

---

## 스토리북 (선택사항)
각 컴포넌트를 독립적으로 확인할 수 있는 데모 페이지
`src/pages/ComponentDemoPage.tsx` → 라우트: `/demo` (개발용)
- 16개 컴포넌트를 한 페이지에서 모두 확인 가능

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- CSS transition / animation 속성 설명
- useEffect + setInterval로 카운트다운 만드는 방법
- Recharts 각 컴포넌트(LineChart, RadarChart 등) 사용법
- keyframes 애니메이션 작성 방법
- props 타입 정의 (TypeScript interface) 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `/demo` 페이지에서 16개 컴포넌트 모두 렌더링 확인
2. 각 애니메이션 동작 확인
3. 모바일 화면(375px)에서 컴포넌트 깨지지 않음 확인
4. 컬러 하드코딩 없이 brand 토큰만 사용 확인
