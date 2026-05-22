# 40. RacePulse 말 Stat 카드 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, FE 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (말 Stat 카드 Option 1+3 합체)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: 없음 — 독립 구현 가능

---

## 🗂️ 지금까지 한 작업 요약

### 14차 회의 확정 (동적 UI 32번)
- **Option 1 + Option 3 합체**: FIFA 카드 스타일 + 수치 게이지
- 스탯 8개: 속도, 지구력, 출발, 회전, 적응력, 컨디션, 집중력, 협조성
- ML 예측 모델의 피처 중요도(SHAP) 기반으로 수치 도출
- 프리미엄 잠금: FREE 유저는 "속도" 1개만, 나머지 7개는 `LockedContent`로 잠금

### 기존 FE 구조
- `src/components/dynamic/` — 동적 UI 컴포넌트 디렉터리
- `src/pages/horse/HorseDetailPage.tsx` — 말 상세 페이지 (여기에 카드 삽입)
- 디자인 철학: "Bloomberg Terminal × Premium Sports Analytics"

---

## 목표

신규 파일 2개를 작성합니다.

1. `src/components/dynamic/HorseStatCard.tsx` — FIFA 카드 + 수치 게이지 합체 (핵심)
2. `src/api/horseStatApi.ts` — 말 스탯 API 호출

그리고 `HorseDetailPage.tsx`에 `HorseStatCard` 삽입합니다.

---

## 스탯 8개 정의

| # | 스탯명 | 설명 | 계산 기반 |
|---|--------|------|-----------|
| 1 | 속도 | 최고 기록 기반 절대 속도 | 최근 3경주 구간 기록 |
| 2 | 지구력 | 장거리 성적 유지 능력 | 1,600m+ 경주 성적 비율 |
| 3 | 출발 | 게이트 출발 후 초반 순위 | 1구간 통과 순위 평균 |
| 4 | 회전 | 코너 구간 속도 유지 | 코너 구간 기록 vs 직선 |
| 5 | 적응력 | 다양한 트랙 조건 대응 | 트랙 상태별 성적 편차 |
| 6 | 컨디션 | 현재 컨디션 지수 | 마체중 변화 + 최근 폼 |
| 7 | 집중력 | 기수와의 협력 지수 | 기수-말 조합 성적 |
| 8 | 협조성 | 경쟁마와의 경합 능력 | 박빙 경주에서 성적 |

스탯 값은 0~99 정수 (FIFA 카드 방식).

---

## 구현 사항

### 1. `src/api/horseStatApi.ts`

```typescript
// GET /api/v1/horses/{horseId}/stats 호출
// ML 서버가 계산한 스탯 8개를 가져옵니다.
// TODO: [Phase 4] ML 서버에 스탯 계산 엔드포인트 추가 후 실제 연동
// 현재는 mock 데이터로 동작

export interface HorseStat {
  horseId: number
  horseName: string
  imageUrl?: string   // 마사회 API 말 사진 URL
  stats: {
    speed: number        // 속도 (0~99)
    endurance: number    // 지구력
    start: number        // 출발
    cornering: number    // 회전
    adaptability: number // 적응력
    condition: number    // 컨디션
    focus: number        // 집중력
    cooperation: number  // 협조성
  }
  overallRating: number  // 전체 종합 점수 (0~99)
  ratingGrade: 'S' | 'A' | 'B' | 'C' | 'D'
}
```

### 2. `src/components/dynamic/HorseStatCard.tsx` (핵심)

**FIFA 카드 + 수치 게이지 합체 디자인:**

```
┌────────────────────────────────────┐
│  S  [말 사진/실루엣]               │  ← 등급 + 사진
│ 87                                 │  ← 종합 점수
│ 천하무적                           │  ← 말 이름
│ ─────────────────────────────────  │
│ 속도   █████████░  87              │  ← 게이지 + 수치
│ 지구력 ████████░░  78  [🔒]        │  ← FREE 유저는 잠금
│ 출발   ███████░░░  72  [🔒]        │
│ 회전   ██████░░░░  65  [🔒]        │
│ 적응력 █████░░░░░  54  [🔒]        │
│ 컨디션 ██████░░░░  61  [🔒]        │
│ 집중력 ████░░░░░░  48  [🔒]        │
│ 협조성 ███████░░░  71  [🔒]        │
└────────────────────────────────────┘
```

**스타일 상세:**

```typescript
// 카드 컨테이너
// 배경: 세로 그라디언트 (위: brand-navy-900, 아래: brand-navy-950)
// 테두리: brand-gold-600/40
// 모서리: rounded-2xl
// 너비: 280px 고정

// 등급별 색상
const GRADE_COLORS = {
  S: 'text-yellow-300',   // 금색
  A: 'text-brand-gold-400',
  B: 'text-lime-400',
  C: 'text-blue-400',
  D: 'text-white/60',
}

// 스탯 게이지 바
// 배경: white/10
// 채움: brand-gold-400 (속도), 나머지는 수치에 따라 색상 변화
//   90+: #FFD700 (금)
//   70~89: #90EE90 (라임)
//   50~69: #87CEEB (스카이블루)
//   0~49: #FF6B6B (연빨강)

// 애니메이션: 카드 진입 시 게이지가 0에서 채워지는 애니메이션 (0.8초)
// framer-motion 또는 CSS transition 사용
```

**말 사진 처리:**
```typescript
// 마사회 API 사진이 있으면 표시, 없으면 말 실루엣 SVG 사용
const horseImage = stat.imageUrl
  ? <img src={stat.imageUrl} alt={stat.horseName} className="w-full h-32 object-cover" />
  : <HorseSilhouetteIcon className="w-24 h-24 text-white/20" />
```

**프리미엄 잠금 연동 (prompt-39의 LockedContent 사용):**
```tsx
// FREE 유저: 속도만 보이고, 나머지 7개는 잠금
{statList.map((stat, index) => (
  index === 0 ? (
    // 속도: 무료 공개
    <StatRow key={stat.key} stat={stat} value={horseStats[stat.key]} />
  ) : (
    // 나머지: LockedContent로 감싸기
    <LockedContent key={stat.key} contentType="STAT">
      <StatRow stat={stat} value={horseStats[stat.key]} />
    </LockedContent>
  )
))}
```

**카드 플립 효과 (앞면: 카드 / 뒷면: 레이더 차트):**
```tsx
// 카드를 클릭하면 뒤집어서 RatingRadarChart를 보여줍니다
// (이미 구현된 RatingRadarChart 컴포넌트 재사용)
const [flipped, setFlipped] = useState(false)

<div
  onClick={() => setFlipped(!flipped)}
  className="cursor-pointer transition-transform duration-500"
  style={{ transform: flipped ? 'rotateY(180deg)' : 'rotateY(0deg)' }}
>
  {flipped ? <RadarChartBack /> : <FIFACardFront />}
</div>
```

### 3. `HorseDetailPage.tsx` 수정

말 상세 페이지 상단에 `HorseStatCard` 삽입:
```tsx
import HorseStatCard from '../../components/dynamic/HorseStatCard'

// 기존 말 기본정보 섹션 아래에
<HorseStatCard horseId={horseId} />
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `rotateY(180deg)` CSS 3D 변환이 뭔지 설명 (카드 뒤집기 효과)
- `object-cover`가 왜 필요한지 설명 (사진 비율을 유지하며 영역을 꽉 채움)
- 스탯 수치가 0~99인 이유 설명 (FIFA 카드 방식 — 직관적 비교)
- `transition-transform duration-500`이 뭔지 설명 (0.5초 동안 부드럽게 변환)
- 게이지 바 애니메이션이 왜 UX에 중요한지 설명 (숫자보다 시각적으로 빠르게 파악)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-fe-ui
커밋 메시지: feat: [prompt-40] 말 Stat 카드 — FIFA 카드 + 수치 게이지 합체 + 카드 플립 + Freemium 잠금 연동
```

---

## 완료 기준

```bash
# 1. FE 빌드 성공
npm run build

# 2. 동작 확인
# - /horses/1 접속 → HorseStatCard 표시 확인
# - 8개 스탯 게이지 바 애니메이션 확인
# - 카드 클릭 → 뒤집기 → 레이더 차트 전환 확인
# - FREE 유저: 속도만 보이고 나머지 7개 잠금 확인
```
