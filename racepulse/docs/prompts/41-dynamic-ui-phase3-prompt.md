# 41. RacePulse 동적 UI Phase 3 (27~32번) 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, 기존 동적 UI 1~16종 구현 현황
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (동적 UI 27~32번)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**:
- `prompt-30 (Bayesian MC)` 완료 — Bayesian 확률 데이터 API 사용 가능
- `prompt-31 (Sequential)` 완료 — Sequential 컨디션 갱신 API 사용 가능
- `prompt-35 (AI 해설 고도화)` 완료 — 품질 점수 데이터 포함

---

## 🗂️ 지금까지 한 작업 요약

### 기존 동적 UI (Phase 1·2 완료, 1~26번)
- Phase 1 (1~6번): 컨디션 뱃지, 우승확률 바, 컨디션 게이지, 카드 슬라이드인, 시뮬레이션 애니메이션, 카드 호버
- Phase 2 (7~16번): 결과 리빌, 예측 vs 실제, 정확도 서클, 수집 카운트다운, 경주 시작 카운트다운, 로딩 + 타이핑 + 폼 트렌드 + 게이트 편향 + OddsMovement + MC 히트맵 + 레이더차트 + 리벨H2H + 페이스라인 + 날씨영향 + 신뢰도미터 + 카운터팩추얼 + 스타일매칭 + 랭크분포
- 위치: `src/components/dynamic/`

### Phase 3 추가 6종 (14차 회의 확정)
| # | UI 요소 | 위치 |
|---|---------|------|
| 27 | Bayesian 확률 업데이트 애니메이션 | `RacePredictionPage` |
| 28 | Sequential Race 실시간 컨디션 갱신 바 | `RacePredictionPage` |
| 29 | AI 해설 품질 뱃지 (HIGH/MED/LOW) | `RaceDetailPage` 해설 섹션 |
| 30 | 사행성 팝업 스크롤 진행 바 | `TermsConsentModal` (prompt-38) |
| 31 | 변경사항 복합 신뢰도 게이지 | `RacePredictionPage` |
| 32 | 말 Stat 카드 | `HorseDetailPage` (prompt-40) |

> **32번(말 Stat 카드)은 prompt-40에서 구현합니다. 여기서는 27~31번만 구현합니다.**

---

## 목표

`src/components/dynamic/`에 신규 파일 5개를 작성합니다:

1. `BayesianUpdateAnimation.tsx` — 동적 UI 27번
2. `SequentialConditionBar.tsx` — 동적 UI 28번
3. `CommentaryQualityBadge.tsx` — 동적 UI 29번
4. `TermsScrollProgressBar.tsx` — 동적 UI 30번 (prompt-38에서 import해서 사용)
5. `ChangeReliabilityGauge.tsx` — 동적 UI 31번

---

## 구현 사항

### 27. `BayesianUpdateAnimation.tsx` — Bayesian 확률 업데이트

**개념**: ML 모델이 "30%"라고 예측했는데, 최근 2회 우승으로 "38.5%"로 업데이트됨을 시각화

```
ML 예측    Bayesian 업데이트 후
  30%   →→→→→→→→→→→→→   38.5%
        [카운트업 애니메이션]
        ▲ 최근 2경주 반영
```

**Props:**
```typescript
interface Props {
  priorProb: number     // ML 예측값 (예: 0.30)
  posteriorProb: number // Bayesian 업데이트 후 (예: 0.385)
  recentRaces: number   // 반영된 최근 경주 수 (예: 3)
}
```

**동작:**
- 마운트 시 `priorProb`에서 시작해 1.5초 동안 `posteriorProb`까지 카운트업
- 상승이면 골드/초록, 하락이면 흰색/빨강으로 색상 변화
- 오른쪽 소형 텍스트: "최근 N경주 반영"
- 컨테이너: `bg-brand-navy-900/50 border border-brand-gold-400/20 rounded-lg px-4 py-2`

**카운트업 로직:**
```typescript
useEffect(() => {
  const start = priorProb
  const end = posteriorProb
  const duration = 1500  // 1.5초
  const startTime = Date.now()
  
  const tick = () => {
    const progress = Math.min((Date.now() - startTime) / duration, 1)
    // easeOut 함수: 처음엔 빠르고 끝에 천천히
    const eased = 1 - Math.pow(1 - progress, 3)
    setCurrent(start + (end - start) * eased)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)
}, [priorProb, posteriorProb])
```

---

### 28. `SequentialConditionBar.tsx` — Sequential 실시간 컨디션 갱신

**개념**: 앞 경주 결과가 반영되어 뒷 경주 예측이 업데이트됐음을 표시

```
1경주 ✅  2경주 ✅  3경주 🔄  4경주 ⏳  5경주 ⏳
          └─ "2경주 결과 반영 완료 — 트랙 습윤→건조 변경으로 선행마 확률 조정됨"
```

**Props:**
```typescript
interface Props {
  currentRaceNo: number           // 현재 보고 있는 경주 번호
  completedRaces: number[]        // 완료된 경주 번호 목록
  lastUpdate?: {
    raceNo: number
    trackChanged: boolean
    message: string               // "1경주 결과 반영 완료"
  }
}
```

**동작:**
- 완료 경주: ✅ 초록 원
- 현재 경주: 🔄 골드 펄스 애니메이션
- 미완료 경주: ⏳ 흰색/30 원
- 업데이트 메시지: 하단에 페이드인으로 표시 (3초 후 자동 사라짐)
- 트랙 변경 시 메시지에 파란 뱃지 추가: `[🔵 트랙 변경]`

---

### 29. `CommentaryQualityBadge.tsx` — AI 해설 품질 뱃지

**개념**: GPT가 생성한 해설의 품질 등급을 표시 (관리자/고급 유저용 정보)

```
[HIGH ⭐ GPT-4.1]    점수: 92/100
[MED  ⚡ GPT-4.1-mini]  점수: 63/100
[LOW  ⚠️ fallback]      점수: 10/100
```

**Props:**
```typescript
interface Props {
  qualityScore: number    // 0~100
  modelUsed: string       // "gpt-4.1" | "gpt-4.1-mini"
  retryCount: number      // 재시도 횟수
  generationMs?: number   // 생성 소요 시간
}
```

**등급 기준 (14차 회의 확정):**
```typescript
const getGrade = (score: number) => {
  if (score >= 80) return { label: 'HIGH', color: 'text-green-400 bg-green-400/10 border-green-400/30' }
  if (score >= 50) return { label: 'MED',  color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30' }
  return              { label: 'LOW',  color: 'text-red-400 bg-red-400/10 border-red-400/30' }
}
```

**크기**: 인라인 소형 뱃지 (`text-xs px-2 py-0.5 rounded-full border`)
**위치**: AI 해설 텍스트 우측 상단 모서리

---

### 30. `TermsScrollProgressBar.tsx` — 사행성 팝업 스크롤 진행 바

**개념**: 약관을 얼마나 읽었는지 시각적으로 표시 (골드 진행 바)

**Props:**
```typescript
interface Props {
  scrollPercent: number   // 0~100
  isComplete: boolean     // 스크롤 100% 도달 여부
}
```

```
[===========>              ] 45%   (진행 중 — 골드)
[==========================] 100% ✓ (완료 — 골드 글로우)
```

**스타일:**
- 컨테이너: `w-full h-1.5 bg-white/10 rounded-full`
- 채움: `h-full bg-brand-gold-400 rounded-full transition-all duration-200`
- 완료 시: `shadow-[0_0_8px_rgba(212,168,67,0.8)]` 골드 글로우 효과
- 완료 체크: 바 오른쪽에 작은 ✓ 표시

**사용 위치**: `TermsConsentModal.tsx` (prompt-38)에서 import

---

### 31. `ChangeReliabilityGauge.tsx` — 변경사항 복합 신뢰도 게이지

**개념**: 변경사항이 많을수록 예측 신뢰도가 낮아짐을 실시간으로 시각화

```
예측 신뢰도: ████████░░  78%
             ↑ 기수 변경으로 신뢰도 하락 중...
```

**Props:**
```typescript
interface Props {
  baseReliability: number     // 기본 신뢰도 (0~100)
  changes: Array<{
    type: 'JOCKEY' | 'SCRATCH' | 'TRAINER' | 'EQUIPMENT' | 'TRACK'
    impact: 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW'
  }>
}
```

**신뢰도 감소 계산:**
```typescript
const IMPACT_REDUCTION = {
  VERY_HIGH: 15,   // 기수변경/출전취소: -15%
  HIGH: 10,
  MEDIUM: 5,       // 조교사/장비/트랙: -5%
  LOW: 2,
}

const currentReliability = Math.max(
  0,
  baseReliability - changes.reduce((acc, c) => acc + IMPACT_REDUCTION[c.impact], 0)
)
```

**스타일:**
- 게이지 색상: 80+ 초록 → 60~79 노랑 → 40~59 주황 → 0~39 빨강
- 변경 감지 시 게이지가 부드럽게 감소하는 애니메이션 (CSS transition)
- 변경 타입별 뱃지: 🔴🟠🟡⚫🔵 인라인으로 나열
- 컨테이너: `bg-brand-navy-900/50 border border-white/10 rounded-lg p-3`

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `requestAnimationFrame`이 뭔지 설명 (브라우저가 화면 그리기 직전에 호출하는 함수)
- easeOut 함수가 왜 필요한지 설명 (처음엔 빠르고 끝에 천천히 → 자연스러운 애니메이션)
- `Math.max(0, ...)` 패턴이 왜 필요한지 설명 (신뢰도가 음수가 되지 않게 하한선 설정)
- 골드 글로우 `shadow-[...]`가 무엇인지 설명 (Tailwind 임의 값으로 그림자 효과)
- `transition-all duration-200`이 뭔지 설명 (0.2초 동안 모든 속성 부드럽게 변화)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-fe-ui
커밋 메시지: feat: [prompt-41] 동적 UI Phase 3 (27~31번) — Bayesian 애니메이션 / Sequential 갱신 바 / 품질 뱃지 / 스크롤 바 / 신뢰도 게이지
```

---

## 완료 기준

```bash
npm run build  # 빌드 성공

# 각 컴포넌트 /demo 페이지에서 확인
# - BayesianUpdateAnimation: 30% → 38.5% 카운트업 확인
# - SequentialConditionBar: 1,2 완료 / 3 진행 중 표시 확인
# - CommentaryQualityBadge: HIGH/MED/LOW 뱃지 색상 확인
# - TermsScrollProgressBar: 스크롤에 따라 골드 바 증가 확인
# - ChangeReliabilityGauge: 변경 추가 시 수치 감소 애니메이션 확인
```
