# Codex 프롬프트 — Phase 4-5: 경주 결과 + AI 해설 화면 구현

## 작업 개요
`/races/:raceId/result`와 `/races/:raceId/commentary` 두 화면이 Placeholder 상태입니다.
두 화면 모두 **BE API가 이미 200 정상 응답**하므로 화면 구현만 하면 됩니다.

## 기술 스택
- React 18 / TypeScript / Tailwind CSS v4
- API 베이스: `/api/v1/`
- 기존 훅 참고: `src/hooks/useRaces.ts`, `src/hooks/usePrediction.ts`

---

## 화면 1: 경주 결과 (`/races/:raceId/result`)

### API
```
GET /api/v1/races/{id}/result
응답 필드 (기존 RaceService 코드 확인 후 맞춰서 사용):
- raceName, meetCode, rcDate
- results: [{ rank, horseName, gateNo, jockeyName, finalTime, margin }]
```

### 레이아웃
```
← 경주 목록  /  서울 3경주  /  경주 결과

┌─────────────────────────────────────────┐
│ 서울경마공원                              │
│ 제00회 서울 3경주   2026-05-16           │
│ 거리: 1400m  트랙: 양호                  │
└─────────────────────────────────────────┘

[최종 순위]
1위  ┃ 말이름  ┃ 기수명  ┃ 1:24.5  ┃  —
2위  ┃ 말이름  ┃ 기수명  ┃ 1:24.8  ┃ 0.3초 차
3위  ┃ 말이름  ┃ 기수명  ┃ 1:25.1  ┃ 0.6초 차

[예측 vs 실제] ← 예측 데이터가 있는 경우만 표시
이 경주의 AI 예측과 실제 결과를 비교합니다.

[AI 해설 보기] 버튼 → /races/:raceId/commentary
```

### 구현 요구사항
- 1위는 골드(`text-brand-gold-400`), 2~3위는 흰색
- 로딩 중: 스켈레톤 UI (기존 패턴 참고)
- 결과 없음: "결과 데이터가 없습니다" 안내
- 주석: 각 섹션이 무엇을 표시하는지 설명

---

## 화면 2: AI 해설 (`/races/:raceId/commentary`)

### API
```
GET /api/v1/commentary/{raceId}/pre   ← 사전 해설 (경주 전)
GET /api/v1/commentary/{raceId}/post  ← 결과 해설 (경주 후)
```

경주 상태에 따라:
- 경주 전(SCHEDULED): pre 해설만 표시
- 경주 후(COMPLETED): post 해설 표시, pre 해설 탭으로 전환 가능

### 레이아웃
```
← 경주 상세  /  서울 3경주  /  AI 해설

┌─────────────────────────────────────────┐
│ 🤖 AI 해설                               │
│ GPT-4.1 기반 경주 분석 해설입니다.       │
└─────────────────────────────────────────┘

[사전 해설] [결과 해설]  ← 탭 (결과 있을 때만 결과 탭 활성화)

해설 본문 (600~1200자 텍스트)
줄바꿈 처리: whitespace-pre-wrap

─────────────────────────────────────────
⚠️ 본 해설은 순수 데이터 분석 목적이며,
베팅 등 사행 행위와 무관합니다.   ← 필수 고정 문구
```

### 구현 요구사항
- 해설 텍스트: `whitespace-pre-wrap` (줄바꿈 보존)
- 품질 점수(`qualityScore`)가 있으면 상단에 "AI 신뢰도 87점" 표시
- 로딩 중: 타이핑 애니메이션 (TypingAnimation 컴포넌트가 `src/components/dynamic/`에 있음)
- **면책 문구 필수**: 화면 하단 고정 (사행성 방지 규칙)
- 주석: 면책 문구가 왜 필수인지, 탭 전환 로직 설명

---

## App.tsx 라우트 등록 업데이트

```tsx
const RaceResultPage = lazy(() => import('./pages/race/RaceResultPage'))
const CommentaryPage = lazy(() => import('./pages/race/CommentaryPage'))

<Route path="/races/:raceId/result"     element={<RaceResultPage />} />
<Route path="/races/:raceId/commentary" element={<CommentaryPage />} />
```

---

## 완료 기준
- `/races/1/result` → 경주 결과 테이블 표시
- `/races/1/commentary` → AI 해설 텍스트 표시
- 면책 문구 반드시 존재 확인
- 로딩/에러 상태 처리 확인
