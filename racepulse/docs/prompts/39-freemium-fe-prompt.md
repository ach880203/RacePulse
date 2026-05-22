# 39. RacePulse Freemium 잠금 UI 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, FE 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 편자 시스템 전체 확정사항
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: `prompt-37 (편자 시스템 BE)` 완료 — `/api/v1/wallet` API 사용 가능

---

## 🗂️ 지금까지 한 작업 요약

### 편자 시스템 확정 내역 (14차 회의)

**콘텐츠 접근 방식:**
| 콘텐츠 | 광고 직접 시청 | 편자 비용 |
|--------|-------------|---------|
| 말 Stat 개별 항목 | ✅ 15초 → 건초 | 1편자 |
| 변경사항 상세 | ✅ 15초 → 건초 | 1편자 |
| Top-3 확률 전체 | ✅ 30초 | 3편자 |
| AI **결과** 해설 | ✅ 30초 | 3편자 |
| AI **사전** 해설 | ❌ 불가 | 25편자 |
| Counterfactual | ❌ 불가 | 18편자 |
| Top-1 확률 | ❌ 불가 | 35편자 |
| 앙상블 전체 | ❌ 불가 | 50편자 |

**가입 후 7일 전체 무료** — FREE 유저도 첫 7일은 모든 콘텐츠 접근 가능

---

## 목표

신규 파일 3개 + API 파일 1개를 작성합니다.

**신규:**
1. `src/components/freemium/LockedContent.tsx` — 잠금 오버레이 컴포넌트 (핵심)
2. `src/components/freemium/WalletHUD.tsx` — 헤더 편자 잔액 표시 (🔩N + 🥇N)
3. `src/components/freemium/AdWatchModal.tsx` — 광고 시청 모달 (타이머)
4. `src/api/walletApi.ts` — 지갑 API 호출

---

## 구현 사항

### 1. `src/api/walletApi.ts`

```typescript
// 편자 지갑 관련 API 호출

export const fetchWallet = async (): Promise<WalletResponse>
export const earnAttendance = async (): Promise<WalletResponse>
export const earnAd = async (duration: 15 | 30 | 60): Promise<WalletResponse>
export const earnQuiz = async (): Promise<WalletResponse>
export const spendHorseshoe = async (params: {
  contentType: ContentType
  raceId?: number
}): Promise<SpendResponse>
export const fetchTransactions = async (page: number): Promise<PageResponse<Transaction>>
```

타입 정의 (`src/types/wallet.ts`):
```typescript
export type ContentType =
  | 'TOP_1'       // 35편자
  | 'ENSEMBLE'    // 50편자
  | 'AI_PRE'      // 25편자
  | 'COUNTERFACTUAL' // 18편자
  | 'TOP_3'       // 3편자
  | 'AI_POST'     // 3편자
  | 'STAT'        // 1편자
  | 'CHANGE_DETAIL' // 1편자

// 콘텐츠별 비용 상수 (FE에서도 알아야 UI 렌더링 가능)
export const CONTENT_COST: Record<ContentType, number> = {
  TOP_1: 35, ENSEMBLE: 50, AI_PRE: 25, COUNTERFACTUAL: 18,
  TOP_3: 3, AI_POST: 3, STAT: 1, CHANGE_DETAIL: 1,
}

// 광고 시청 허용 여부
export const AD_ALLOWED: Record<ContentType, boolean> = {
  TOP_1: false, ENSEMBLE: false, AI_PRE: false, COUNTERFACTUAL: false,
  TOP_3: true, AI_POST: true, STAT: true, CHANGE_DETAIL: true,
}
```

### 2. `src/components/freemium/LockedContent.tsx` (핵심)

**사용 방법 (다른 컴포넌트에서 감싸서 사용):**
```tsx
<LockedContent contentType="TOP_1" raceId={123}>
  <Top1PredictionCard data={top1Data} />
</LockedContent>
```

**잠금 상태 UI:**
```
┌──────────────────────────────────────┐
│ [blur 4px 흐릿한 콘텐츠 미리보기]    │
│ ████ ██████ ██ ████ ██████           │  ← 실제 콘텐츠가 흐리게 보임
│                                      │
│ ┌──────────────────────────────┐    │
│ │    🔒 Top-1 확률              │    │
│ │    🔩 35편자로 열기           │    │
│ │   [ 편자 소비하기 ]          │    │  ← 편자 충분 시
│ │                              │    │
│ │   편자가 부족하신가요?        │    │
│ │   [ 🔩 편자 더 얻기 ]       │    │
│ └──────────────────────────────┘    │
└──────────────────────────────────────┘
```

**광고 허용 콘텐츠일 때 추가 버튼:**
```
│ │   또는                        │    │
│ │   [ 📺 30초 광고 보고 열기 ] │    │
```

**구현 로직:**
```typescript
const LockedContent = ({ contentType, raceId, children }) => {
  const [unlocked, setUnlocked] = useState(false)
  const { data: wallet } = useWallet()  // React Query로 지갑 조회
  
  // 잠금 해제 조건: 이미 열었거나 7일 무료 기간이거나 PRO 유저
  if (unlocked || isFreeTrial() || isPro()) {
    return <>{children}</>
  }
  
  // 잠금 상태 렌더링
  return (
    <div className="relative">
      {/* 실제 콘텐츠를 blur 처리해서 미리보기 */}
      <div className="pointer-events-none blur-[4px] select-none">
        {children}
      </div>
      {/* 잠금 오버레이 */}
      <div className="absolute inset-0 flex items-center justify-center
                      bg-brand-navy-950/60 backdrop-blur-[2px]">
        <LockCard
          contentType={contentType}
          cost={CONTENT_COST[contentType]}
          adAllowed={AD_ALLOWED[contentType]}
          hasEnough={wallet?.totalHorseshoe >= CONTENT_COST[contentType]}
          onSpend={() => handleSpend(contentType, raceId)}
          onWatchAd={() => setShowAdModal(true)}
        />
      </div>
    </div>
  )
}
```

**7일 무료 판단:**
```typescript
function isFreeTrial(): boolean {
  // JWT 토큰의 createdAt 또는 localStorage의 가입일로부터 7일 이내
  const registeredAt = localStorage.getItem('racepulse_registered_at')
  if (!registeredAt) return false
  const diff = Date.now() - new Date(registeredAt).getTime()
  return diff < 7 * 24 * 60 * 60 * 1000
}
```

편자 소비 성공 → `setUnlocked(true)` → 잠금 해제, 콘텐츠 표시

### 3. `src/components/freemium/AdWatchModal.tsx`

광고 대신 타이머로 구현 (실제 광고 SDK는 Phase 4):
```
┌────────────────────────────────┐
│ 📺 광고 시청 중...             │
│                                │
│ [=======>             ] 30초  │
│                                │
│ 15초 후 건너뛰기 가능          │
│                                │
│      [× 닫기]                  │
└────────────────────────────────┘
```

- `duration`: 15 / 30 / 60초 타이머
- 타이머 완료 → `earnAd(duration)` API 호출 → 지갑 업데이트 → 잠금 해제
- 30초 이상 광고는 건너뛰기 불가 (15초 후 건너뛰기 버튼은 15초 광고만)

### 4. `src/components/freemium/WalletHUD.tsx`

헤더에 삽입할 편자 잔액 표시:
```
🔩15  🥇230
```
- 클릭 시 `/wallet` 페이지로 이동 (또는 드롭다운)
- 로그인하지 않은 경우 미표시
- 오늘 광고 상한 도달 시 🔩에 빨간 뱃지 표시

`Header.tsx`에 `<WalletHUD />` 삽입.

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `blur-[4px]`이 왜 `blur-sm`이 아니라 커스텀 값인지 설명 (4px가 딱 적당한 흐림 강도)
- `pointer-events-none`이 뭔지 설명 (클릭 이벤트가 통과 못 하게 막음 — 보안)
- `select-none`이 왜 필요한지 설명 (blur 상태에서 드래그로 텍스트 복사 방지)
- React Query `useWallet()`이 왜 편한지 설명 (캐싱으로 여러 컴포넌트가 공유)
- `isFreeTrial()` 로직이 왜 localStorage에서 가져오는지 설명 (서버 부하 없이 판단)
- `absolute inset-0`이 무엇인지 설명 (부모 기준 전체 영역을 덮는 포지셔닝)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-fe-freemium
커밋 메시지: feat: [prompt-39] Freemium 잠금 UI — blur 미리보기 + 편자 소비 버튼 + 광고 타이머 + WalletHUD
```

---

## 완료 기준

```bash
# 1. FE 빌드 성공
npm run build

# 2. 동작 확인 (개발 서버)
npm run dev

# - RacePredictionPage에서 Top-1 확률 영역에 LockedContent 적용 확인
# - blur 처리된 콘텐츠 미리보기 표시 확인
# - "편자 소비하기" 버튼 클릭 → API 호출 → 잠금 해제 확인
# - 편자 부족 시 "편자 더 얻기" 버튼 표시 확인
# - 헤더에 WalletHUD (🔩N 🥇N) 표시 확인
```
