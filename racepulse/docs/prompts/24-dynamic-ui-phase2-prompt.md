# 24. RacePulse 동적 UI Phase 2 (10종) 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표

4차 회의 확정사항인 Phase 2 동적 UI 10종을 구현합니다.
Phase 1의 16종(Bloomberg Terminal 기반 기본 UI)에 이어,
새로 추가된 ML 데이터(라이벌 대결, 주행 스타일, Monte Carlo 고도화)를 시각화합니다.

---

## 프로젝트 환경

- React 18 / TypeScript / Vite
- Tailwind CSS v4 (`brand-navy-950`, `brand-gold-500` 토큰)
- 폰트: Playfair Display / Inter / JetBrains Mono
- 디자인 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 컬러: `#07091A` (배경), `#D4A843` (골드), 골드 글로우 효과
- 애니메이션: duration-fast(150ms) ~ duration-hero(1200ms)
- Recharts (차트)

---

## 현재 파일/폴더 구조

```
frontend/src/components/dynamic/   ← Phase 1 완료 (16종)
├── ConditionColorBadge.tsx
├── WinProbabilityBar.tsx
├── ConditionGauge.tsx
├── SparklineChart.tsx
├── RatingRadarChart.tsx
├── HorseCardSlideIn.tsx
├── SimulationAnimation.tsx
├── HorseCardHover.tsx
├── ResultRevealAnimation.tsx
├── PaceLineChart.tsx
├── PredictionVsActualGauge.tsx
├── AccuracyCircleGauge.tsx
├── CollectionCountdown.tsx
├── RaceStartCountdown.tsx
├── TypingAnimation.tsx
└── LoadingAnimation.tsx
```

---

## 구현 사항 — Phase 2 신규 10종

모든 컴포넌트는 `frontend/src/components/dynamic/` 에 생성합니다.

---

### 1. `RivalH2HCard.tsx` — 라이벌 직접 대결 카드

```
두 말의 역대 직접 대결 전적을 카드 형태로 표시합니다.
예: "투어킹 vs 피엔에스트윈 — 3전 2승 (투어킹)"

애니메이션:
- 카드 flip 효과 (앞면: 현재 경주, 뒷면: 역대 전적)
- 승리 수 카운트업 애니메이션
- 마지막 대결 날짜 표시

API: GET /ml/rivals/{horseIdA}/{horseIdB}
```

Props:
```typescript
interface RivalH2HCardProps {
  horseAId: number
  horseBId: number
  horseAName: string
  horseBName: string
}
```

---

### 2. `RunningStyleBadge.tsx` — 주행 스타일 배지

```
각 말의 주행 스타일을 아이콘 + 텍스트 배지로 표시합니다.

스타일별 표시:
- LEADER  (선행) → 🏇 금색 배지 "선행"
- STALKER (추적) → 🔵 청색 배지 "추적"
- CLOSER  (추입) → 🟢 녹색 배지 "추입"
- UNKNOWN → 회색 배지 "분석중"

신뢰도(confidence)가 0.5 미만이면 배지에 물음표 표시
```

Props:
```typescript
interface RunningStyleBadgeProps {
  style: "LEADER" | "STALKER" | "CLOSER" | "PRESSER" | "UNKNOWN"
  confidence: number   // 0~1
  size?: "sm" | "md" | "lg"
}
```

---

### 3. `StyleMatchMatrix.tsx` — 주행 스타일 충돌 분석 매트릭스

```
이번 경주 출전마들의 스타일 분포를 시각화합니다.
선행마가 많으면 앞이 혼잡 → 추입마에게 유리 등 분석

표시 내용:
- 스타일별 말 수 도넛 차트
- "선행 혼잡 경주" / "추입 유리 경주" 텍스트 분석
- 각 스타일 말 이름 목록

API: GET /ml/running-style/{raceId}
```

---

### 4. `MonteCarloHeatmap.tsx` — 순위 분포 히트맵

```
각 말의 1~5위 확률을 색상 히트맵으로 표시합니다.
높은 확률 = 진한 골드, 낮은 확률 = 어두운 네이비

가로: 말 이름
세로: 1위, 2위, 3위, 4위, 5위
셀 색상: 확률에 따라 brand-gold 계열 그라디언트

호버: 해당 확률 수치 툴팁 표시
```

---

### 5. `OddsMovementChart.tsx` — 배당률 변화 + 스마트머니 탐지

```
경주 당일 배당률 변화를 라인 차트로 표시합니다.
15% 이상 하락 구간에 "스마트머니 감지" 하이라이트 표시

색상:
- 일반 변화: brand-gold-400 라인
- 스마트머니 구간: 빨간 점선 + "💰 스마트머니" 레이블
```

---

### 6. `GateBiasIndicator.tsx` — 게이트 편향 인디케이터

```
이번 경주의 게이트별 유불리를 수평 바 차트로 표시합니다.
내측 게이트(1~4) vs 외측 게이트(9+) 승률 차이 시각화

예:
게이트 1 ████████ +8%
게이트 8 ████ +2%
게이트 12 ██ -3%

색상: 양수=brand-gold, 음수=회색
```

---

### 7. `ConfidenceScoreMeter.tsx` — Monte Carlo 신뢰도 미터

```
Monte Carlo 시뮬레이션의 신뢰도 점수(0~100)를 반원 게이지로 표시합니다.

구간:
0~40: 빨간색 "데이터 부족"
41~70: 노란색 "보통"
71~100: 골드 "신뢰 가능"

애니메이션: 0에서 실제 점수까지 스윕 애니메이션 (duration-slow 500ms)
```

---

### 8. `FormTrendLine.tsx` — 최근 10경주 폼 트렌드

```
말의 최근 10경주 착순을 라인 차트로 표시합니다.
Phase 1의 SparklineChart(5경주)를 확장한 버전

추가 기능:
- 10경주 표시 (Phase 1은 5경주)
- 추세선 (Trend Line) 오버레이
- "상승세" / "하락세" / "안정" 텍스트 판정
- 경주 클릭 시 해당 경주 상세 링크
```

---

### 9. `WeatherRaceImpact.tsx` — 날씨-경주 영향 카드

```
오늘 예보된 날씨가 경주에 미치는 영향을 카드로 표시합니다.

표시 내용:
- 날씨 아이콘 (맑음/흐림/비)
- Monte Carlo weather_uncertainty_sigma 수치
- "오늘은 예측 변동성이 높습니다" 안내 텍스트
- 비 예보 시 "젖은 트랙 적합 말" 하이라이트

API: 기존 race 데이터의 weather 필드 활용
```

---

### 10. `RankDistributionBar.tsx` — 각 말의 순위 분포 가로 바

```
Monte Carlo 결과의 순위 분포를 스택 바 차트로 표시합니다.
Phase 1의 WinProbabilityBar를 확장 (1위 확률만 → 전체 분포)

예:
투어킹   [■■■■■■■■■□□□□□] 1위:29% 2위:24% 3위:18% 4+:29%
영원한스타 [■■■■■■□□□□□□□□□] 1위:22% 2위:21% 3위:18% 4+:39%

색상:
- 1위 구간: brand-gold-500
- 2위 구간: brand-gold-400 (연한)
- 3위 구간: brand-navy-800 (어두운)
- 4+위 구간: brand-navy-950 (최어둠)
```

---

## ComponentDemoPage.tsx 업데이트

`frontend/src/pages/ComponentDemoPage.tsx` 에 10종 전부 데모 섹션 추가:
```tsx
<section>
  <h2>Phase 2 동적 UI (10종)</h2>
  {/* 각 컴포넌트 더미 데이터로 렌더링 */}
</section>
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 각 컴포넌트의 역할과 사용 페이지 설명
- Recharts 주요 컴포넌트 (`LineChart`, `BarChart` 등) 설명
- `useEffect` 사용 이유 설명
- Tailwind 클래스명이 어떤 스타일인지 설명
- TypeScript interface 각 필드 설명
- 색상 토큰이 어떤 색깔인지 설명 (brand-gold-500 = 경마의 황금빛)

---

## 인코딩 주의사항 ⚠️

- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 저장 전 확인

---

## Git 규칙

```
브랜치: feat/phase2-fe-dynamic-ui-10
커밋 메시지: feat: [prompt-24] Phase 2 동적 UI 10종 구현 (라이벌/스타일/MC 시각화)
```

---

## 완료 기준

```bash
cd racepulse/frontend
npm run build
# → 타입 오류 없이 빌드 성공

# ComponentDemoPage (/demo) 에서 10종 전부 렌더링 확인
# 각 컴포넌트 더미 데이터로 정상 표시
```
