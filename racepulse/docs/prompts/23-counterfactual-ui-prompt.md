# 23. RacePulse Counterfactual 인터랙티브 UI 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표

사용자가 경주 변수를 직접 바꿔가며 Monte Carlo 시뮬레이션 결과가 어떻게 달라지는지 인터랙티브하게 확인하는 UI를 구현합니다.

예시:
- "이 기수 대신 다른 기수가 탔다면?" → 승률 35% → 22%
- "마체중이 2kg 더 가벼웠다면?" → 승률 35% → 41%
- "트랙이 젖어있었다면?" → 패턴 변화 확인

**Web Worker 필수**: Monte Carlo 계산은 CPU 집중 작업이므로 UI 스레드를 차단하지 않도록 Web Worker에서 실행합니다.

---

## 프로젝트 환경

- React 18 / TypeScript / Vite
- Tailwind CSS v4 (`brand-navy-950`, `brand-gold-500` 토큰)
- 폰트: Playfair Display (제목) / Inter (본문) / JetBrains Mono (수치)
- 디자인 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 애니메이션 토큰: duration-fast(150ms) ~ duration-hero(1200ms)
- Web Worker API (브라우저 내장)
- Recharts (차트 라이브러리)

---

## 현재 파일/폴더 구조

```
frontend/src/
├── components/
│   └── dynamic/
│       ├── SimulationAnimation.tsx   ← 기존 Monte Carlo 애니메이션
│       ├── WinProbabilityBar.tsx     ← 기존 승률 바
│       └── (기타 16개 동적 UI)
├── pages/
│   └── race/
│       └── RacePredictionPage.tsx   ← 예측 결과 페이지 (여기에 통합)
├── api/
│   └── (API 호출 파일들)
└── App.tsx
```

---

## 구현 사항

### 1. Web Worker 파일

**`frontend/src/workers/monte-carlo.worker.ts`**

```typescript
// Monte Carlo 시뮬레이션을 Web Worker에서 실행합니다.
// UI 스레드(화면)를 차단하지 않아 버튼 클릭, 슬라이더 조작이 부드럽게 유지됩니다.

interface SimulationInput {
  horses: Array<{
    horse_id: number
    horse_name: string
    win_prob: number        // 기본 승률 (0~1)
    gate_no: number
    odds_win: number | null
    // Counterfactual 조정값
    prob_adjustment: number // -0.5 ~ +0.5 (사용자 조작)
  }>
  n_simulations: number    // 10,000 ~ 50,000
}

interface SimulationResult {
  horse_id: number
  rank_distribution: { "1": number; "2": number; "3": number; "4+": number }
  expected_rank: number
  win_prob_adjusted: number
}

// Worker가 메시지를 받으면 시뮬레이션 실행
self.onmessage = (e: MessageEvent<SimulationInput>) => { ... }
```

### 2. Counterfactual UI 컴포넌트

**`frontend/src/components/dynamic/CounterfactualUI.tsx`**

구현 내용:
- 각 말별로 승률 조정 슬라이더 (-50% ~ +50%)
- 실시간 Monte Carlo 재계산 (슬라이더 드래그 완료 후 Worker 실행)
- 기본값 대비 변화량 표시 (▲+12%, ▼-8%)
- "초기화" 버튼으로 전체 리셋
- 시나리오 이름 저장 ("기수 변경 시나리오", "날씨 변화 시나리오")

**시각화 요소:**
- 조정 전/후 승률 바 비교 (기존 WinProbabilityBar 재활용)
- 변화량 차이를 골드/레드로 색상 구분
  - 상승: `brand-gold-500` + ▲ 아이콘
  - 하락: `#E53E3E` + ▼ 아이콘
- 로딩 중: 말 달리기 로딩 애니메이션 (기존 LoadingAnimation 재활용)

### 3. RacePredictionPage.tsx 통합

기존 예측 페이지 하단에 "가상 시나리오 분석" 섹션 추가:

```tsx
// 탭 구조:
// [기본 예측] [가상 시나리오] [Monte Carlo 상세]
```

- "가상 시나리오" 탭 클릭 시 CounterfactualUI 컴포넌트 렌더링
- Web Worker 초기화는 탭 선택 시 lazy하게 수행

### 4. API 연동

`frontend/src/api/mlApi.ts` 에 추가:
```typescript
// GET /ml/predict/{raceId} → 기본 예측 데이터 조회
// GET /ml/simulate/{raceId}/result → Monte Carlo 기본 결과 조회
// Counterfactual 자체 계산은 브라우저 Web Worker에서 수행 (서버 요청 없음)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `Web Worker`가 무엇인지 쉽게 설명 (별도 작업실 비유)
- `postMessage` / `onmessage` 통신 방식 설명
- `Counterfactual(반사실적 분석)`이란 무엇인지 쉽게 설명
- `useRef`로 Worker 인스턴스를 관리하는 이유 설명
- 슬라이더 `debounce` 처리가 왜 필요한지 설명 (매번 계산 방지)
- TypeScript 타입 정의 하나하나 설명

---

## 인코딩 주의사항 ⚠️

- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 저장 전 확인
- Worker 파일도 UTF-8로 저장

---

## Git 규칙

```
브랜치: feat/phase2-fe-counterfactual-ui
커밋 메시지: feat: [prompt-23] Counterfactual 인터랙티브 UI 구현 (Web Worker 기반)
```

---

## 완료 기준

```bash
# 1. 타입 체크
cd racepulse/frontend
npm run build
# → 타입 오류 없이 빌드 성공

# 2. 동작 확인
# - /races/:raceId/prediction 접속
# - "가상 시나리오" 탭 클릭
# - 슬라이더 조작 시 승률 변화 확인
# - 로딩 애니메이션 표시 후 결과 업데이트 확인
# - "초기화" 버튼 동작 확인
```
