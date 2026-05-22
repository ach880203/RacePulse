# 42. RacePulse 변경사항 FE UI 프롬프트

> 이 프롬프트를 실행하기 전에 docs/PROJECT_RULES.md 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, FE 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (변경감지 UI)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**:
- `prompt-34 (변경감지 BE API)` 완료 — `GET /api/v1/races/{id}/changes` 사용 가능
- `prompt-33 (변경감지 ML)` 완료 — Redis Pub/Sub 이벤트 발행

---

## 🗂️ 지금까지 한 작업 요약

### 14차 회의 확정 변경감지 UI 목록
- **인라인 ★ 뱃지**: 출전표 목록에서 변경된 말에 빨간 별 표시
- **오늘의 변동사항 카드**: 홈/대시보드 상단 경보 배너
- **타임라인**: 변경 이력을 시간순으로 정렬
- **비교 툴팁**: 변경 전/후 값 툴팁으로 비교
- **알림 센터 벨 아이콘**: 헤더 벨 아이콘 + 배지 카운트
- **SSE 실시간 업데이트**: 페이지 새로고침 없이 변경 감지

### 변경 5종 뱃지 확정
| 변경 | 뱃지 | 영향도 |
|------|------|--------|
| 기수변경 | 🔴 빨강 | VERY_HIGH |
| 출전취소 | ⚫ 회색 | VERY_HIGH |
| 조교사변경 | 🟠 주황 | MEDIUM |
| 장비변경 | 🟡 노랑 | MEDIUM |
| 트랙급변 | 🔵 파랑 | MEDIUM |

---

## 목표

신규 파일 4개 + 기존 파일 수정 3개를 작성합니다.

**신규:**
1. `src/components/change/ChangeBadge.tsx` — 인라인 뱃지 (🔴⚫🟠🟡🔵)
2. `src/components/change/ChangeSummaryCard.tsx` — 오늘의 변동사항 카드
3. `src/components/change/ChangeTimeline.tsx` — 변경 이력 타임라인
4. `src/api/changeApi.ts` — 변경감지 API 호출
5. `src/hooks/useChanges.ts` — 변경사항 React Query 훅

**수정:**
6. `src/pages/race/RaceEntriesPage.tsx` — 출전표에 ChangeBadge 인라인 삽입
7. `src/pages/HomePage.tsx` — ChangeSummaryCard 홈 상단 삽입
8. `src/components/layout/Header.tsx` — 벨 아이콘 + 알림 배지 추가

---

## 프로젝트 환경

- **FE**: React 18 / TypeScript / Tailwind CSS v4 / Vite
- **BE API**:
  - `GET /api/v1/races/{raceId}/changes` → 특정 경주 변경사항 목록
  - `GET /api/v1/races/changes/today` → 오늘 전체 변경사항 (홈 배너·벨 아이콘용)
  - `POST /api/v1/races/{raceId}/changes/subscribe` → 변경 알림 구독 (USER 권한)
- **상태관리**: React Query (`refetchInterval: 30분` 자동 갱신)
- **라우팅**: React Router v6 — 경주 상세 `/races/{id}` 탭에 변경이력 추가
- **디자인**: "Bloomberg Terminal × Premium Sports Analytics"
- **컬러 토큰**: `brand-navy-950`(배경) / `brand-gold-400`(골드) — 하드코딩 금지 (규칙 10)
- **폰트**: Playfair Display(브랜드) / Inter(본문) / JetBrains Mono(시간 수치)

---

## 현재 파일 구조 (추가/수정할 위치)

```
frontend/src/
├── api/
│   ├── axiosInstance.ts                   ← 공통 axios 인스턴스 (기존)
│   └── changeApi.ts                       ← 신규 생성 ✅
│
├── hooks/
│   ├── useRaces.ts                        ← 기존
│   └── useChanges.ts                      ← 신규 생성 ✅
│
├── components/
│   ├── layout/
│   │   └── Header.tsx                     ← 수정 (벨 아이콘 + 알림 배지) ✅
│   └── change/                            ← 신규 디렉터리 ✅
│       ├── ChangeBadge.tsx                ← 신규 생성 ✅
│       ├── ChangeSummaryCard.tsx           ← 신규 생성 ✅
│       └── ChangeTimeline.tsx             ← 신규 생성 ✅
│
└── pages/
    ├── HomePage.tsx                       ← 수정 (ChangeSummaryCard 삽입) ✅
    └── race/
        └── RaceEntriesPage.tsx            ← 수정 (ChangeBadge 인라인 삽입) ✅
```

---

## 구현 사항

### 1. `src/api/changeApi.ts`

```typescript
// 변경사항 관련 BE API 호출

// GET /api/v1/races/{raceId}/changes
export const fetchRaceChanges = async (raceId: number): Promise<ChangeResponse>

// GET /api/v1/races/changes/today
export const fetchTodayChanges = async (): Promise<TodayChangesResponse>

// POST /api/v1/races/{raceId}/changes/subscribe (로그인 유저)
export const subscribeRaceChanges = async (raceId: number, subscribe: boolean): Promise<void>

// 타입 정의
export interface ChangeItem {
  type: 'JOCKEY' | 'SCRATCH' | 'TRAINER' | 'EQUIPMENT' | 'TRACK'
  badge: string           // 이모지 (🔴, ⚫, 🟠, 🟡, 🔵)
  impact: 'VERY_HIGH' | 'HIGH' | 'MEDIUM' | 'LOW'
  raceId: number
  horseId?: number
  horseName?: string
  oldValue?: string
  newValue: string
  detectedAt: string      // ISO 8601
}

export interface TodayChangesResponse {
  date: string
  totalCount: number
  highImpactCount: number
  changes: ChangeItem[]
}
```

### 2. `src/components/change/ChangeBadge.tsx` — 인라인 뱃지

**사용 방법:**
```tsx
// 출전표 말 이름 옆에 삽입
<span>{horse.name}</span>
<ChangeBadge changes={horse.changes} />
```

**외형:**
```
천하무적  [🔴 기수변경] [🟡 블링커]
바람처럼  [⚫ 출전취소]
```

- 뱃지는 최대 2개까지 인라인으로 표시 (그 이상은 +N)
- 각 뱃지는 호버 시 툴팁으로 `"박기수 → 김기수"` (변경 전/후 값) 표시
- VERY_HIGH 변경이 있으면 뱃지 주변에 골드 펄스 애니메이션

```typescript
// 골드 펄스 애니메이션 (VERY_HIGH 변경 시)
// Tailwind: animate-pulse 또는 커스텀 keyframe
const isPulse = changes.some(c => c.impact === 'VERY_HIGH')
```

**스타일:**
```typescript
const BADGE_STYLES = {
  JOCKEY:    'bg-red-500/20 text-red-400 border-red-500/40',
  SCRATCH:   'bg-gray-500/20 text-gray-400 border-gray-500/40',
  TRAINER:   'bg-orange-500/20 text-orange-400 border-orange-500/40',
  EQUIPMENT: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40',
  TRACK:     'bg-blue-500/20 text-blue-400 border-blue-500/40',
}
// 크기: text-xs px-1.5 py-0.5 rounded border
```

### 3. `src/components/change/ChangeSummaryCard.tsx` — 오늘의 변동사항 카드

**홈 화면 상단 경보 배너 (변경이 1건 이상일 때만 표시):**

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚡ 오늘의 변동사항 — 총 5건 (영향 큰 변경 2건)        [전체보기 →] │
│                                                                  │
│ 🔴 천하무적 기수 변경    박기수 → 김기수           3경주 · 12분 전 │
│ ⚫ 바람처럼 출전 취소                              5경주 · 28분 전 │
│ 🟡 질주본능 블링커 착용  없음 → 착용 (첫 착용)     7경주 · 1시간 전│
└─────────────────────────────────────────────────────────────────┘
```

**Props:**
```typescript
interface Props {
  maxItems?: number   // 기본 3개까지 표시
}
```

**스타일:**
- 배경: `bg-brand-navy-900 border-l-4 border-brand-gold-400`
- 헤더: `text-brand-gold-400 font-bold`
- 각 항목: 클릭 시 해당 경주 페이지(`/races/{raceId}`)로 이동
- 고영향 변경(VERY_HIGH)이 있을 때 배너 배경에 미세한 빨간 글로우

### 4. `src/components/change/ChangeTimeline.tsx` — 변경 이력 타임라인

**경주 상세 페이지 하단 탭으로 표시:**

```
[기본정보] [출전표] [예측] [변경이력 🔴]   ← 변경 있으면 뱃지

변경 이력
│
├── 09:30  🔴 기수 변경  [VERY_HIGH]
│           박기수 → 김기수
│           예측 신뢰도 하락 · 해설 재생성 완료
│
├── 10:00  🟡 장비 변경  [MEDIUM]
│           블링커 없음 → 블링커 착용 (첫 착용)
│
└── 11:30  🔵 트랙 급변  [MEDIUM]
            건조 → 습윤 (1단계 변화)
            추입마 확률 조정됨
```

**Props:**
```typescript
interface Props {
  raceId: number
}
```

**스타일:**
- 타임라인 선: `border-l-2 border-white/20`
- 시간 마커: `bg-brand-navy-900 text-white/40 text-xs JetBrains Mono`
- VERY_HIGH 항목: 배경 `bg-red-500/5 border border-red-500/20 rounded-lg`
- 각 항목 호버: 배경 밝아지는 효과

### 5. `RaceEntriesPage.tsx` 수정

출전표 목록에 ChangeBadge 삽입:
```tsx
import ChangeBadge from '../../components/change/ChangeBadge'
import { useRaceChanges } from '../../hooks/useChanges'

const { data: changesData } = useRaceChanges(raceId)

// 각 말 행에 추가
<tr key={entry.horseId}>
  <td>{entry.gateNo}</td>
  <td>
    {entry.horseName}
    <ChangeBadge
      changes={changesData?.changes.filter(c => c.horseId === entry.horseId) ?? []}
    />
  </td>
  ...
</tr>
```

### 6. `HomePage.tsx` 수정

```tsx
import ChangeSummaryCard from '../components/change/ChangeSummaryCard'

// 홈 상단 (경주 목록 위)에 삽입
<ChangeSummaryCard maxItems={3} />
```

### 7. `Header.tsx` 수정 — 벨 아이콘 + 알림 배지

```tsx
// 헤더 우측에 벨 아이콘 추가
<button className="relative">
  <BellIcon className="w-5 h-5 text-white/60 hover:text-white" />
  {/* 오늘 변경 건수 배지 */}
  {todayHighImpactCount > 0 && (
    <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full
                     text-[10px] text-white flex items-center justify-center">
      {todayHighImpactCount > 9 ? '9+' : todayHighImpactCount}
    </span>
  )}
</button>
```

**커스텀 훅 `src/hooks/useChanges.ts` 신규:**
```typescript
// useRaceChanges(raceId): 특정 경주 변경사항 조회 (React Query)
// useTodayChanges(): 오늘 전체 변경사항 조회 (30분 refetch interval)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `border-l-4`가 왜 타임라인에 쓰이는지 설명 (왼쪽 세로선으로 시간 흐름 표현)
- `refetchInterval: 30 * 60 * 1000`이 뭔지 설명 (30분마다 자동으로 데이터 다시 가져옴)
- `filter(c => c.horseId === entry.horseId)`가 왜 필요한지 설명 (경주 전체 변경 중 해당 말만 추출)
- 툴팁이 `title` 속성이 아닌 커스텀 컴포넌트인 이유 설명 (디자인 일관성, 위치 제어)
- `absolute -top-1 -right-1`이 뭔지 설명 (벨 아이콘 우측 상단 모서리에 배지 붙이기)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-fe-ui
커밋 메시지: feat: [prompt-42] 변경사항 FE UI — ChangeBadge / 오늘의 변동사항 카드 / 타임라인 / 헤더 벨 아이콘
```

---

## 완료 기준

```bash
# 1. FE 빌드 성공
npm run build

# 2. 동작 확인
# - 홈페이지 상단 ChangeSummaryCard 표시 (변경 없으면 미표시)
# - /races/1/entries 출전표에 뱃지 표시
# - 뱃지 호버 → 변경 전/후 값 툴팁 표시
# - 헤더 벨 아이콘 + 빨간 배지 카운트 표시
# - /races/1 상세 페이지 → '변경이력' 탭 → 타임라인 표시
```
