// =============================================================================
// LockedContent.tsx — 프리미엄 콘텐츠 잠금 오버레이 컴포넌트 (핵심)
// =============================================================================
// 역할:
//   이 컴포넌트는 자녀 컴포넌트를 "감싸서" 잠금 상태를 처리합니다.
//   잠금 상태일 때: 콘텐츠를 흐릿하게 보여주고 잠금 카드를 올립니다.
//   잠금 해제 조건:
//     1) 이미 열었거나 (unlocked = true)
//     2) 7일 무료 체험 기간이거나 (isFreeTrial)
//     3) PRO 유저이거나 (isPro)
//
// 사용 방법:
//   <LockedContent contentType="TOP_1" raceId={123}>
//     <Top1PredictionCard data={...} />
//   </LockedContent>
// =============================================================================

// useState = 컴포넌트 내부에서 바뀌는 값(상태)을 관리합니다.
// ReactNode = React 컴포넌트가 children으로 받을 수 있는 모든 것의 타입입니다.
import { useState } from 'react'
import type { ReactNode } from 'react'

// useMutation = 서버 데이터를 변경하는 API를 호출할 때 사용하는 React Query 훅입니다.
// useQuery    = 서버 데이터를 조회할 때 사용하는 React Query 훅입니다.
// useQueryClient = 캐시를 직접 다루는 객체입니다.
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

// useNavigate = 코드로 다른 페이지로 이동시킬 때 사용합니다.
import { useNavigate } from 'react-router-dom'

// getAuthSnapshot = 현재 로그인 상태(토큰 존재 여부)를 확인합니다.
import { getAuthSnapshot } from '../../store/authStore'

// fetchWallet = 편자 지갑 잔액을 서버에서 조회하는 API 함수입니다.
// spendHorseshoe = 편자를 소비하는 API 함수입니다.
import { fetchWallet, spendHorseshoe } from '../../api/walletApi'

// ContentType = 콘텐츠 종류 타입
// CONTENT_COST = 콘텐츠별 편자 비용 상수
// AD_ALLOWED = 광고 시청 허용 여부 상수
// CONTENT_LABEL = 콘텐츠 한국어 이름
import {
  CONTENT_COST,
  AD_ALLOWED,
  CONTENT_LABEL,
} from '../../types/wallet'
import type { ContentType, AdDuration } from '../../types/wallet'

// AdWatchModal = 광고 시청 타이머 모달 컴포넌트입니다.
import AdWatchModal from './AdWatchModal'

// -----------------------------------------------------------------------------
// isFreeTrial — 7일 무료 체험 기간인지 확인하는 함수
// -----------------------------------------------------------------------------
// localStorage에서 가입일을 읽어 현재 시각과 비교합니다.
// 서버에 요청하지 않고 판단하는 이유:
//   매 잠금 컴포넌트가 렌더링될 때마다 서버 호출을 하면 요청이 폭증합니다.
//   가입일은 자주 바뀌지 않으므로 로컬에 저장해두고 계산하는 것이 효율적입니다.
function isFreeTrial(): boolean {
  const registeredAt = localStorage.getItem('racepulse_registered_at')
  if (!registeredAt) return false
  // Date.now() = 현재 시각을 밀리초(ms)로 나타낸 숫자입니다.
  // new Date(registeredAt).getTime() = 가입일 문자열을 밀리초로 변환합니다.
  const diff = Date.now() - new Date(registeredAt).getTime()
  // 7 * 24 * 60 * 60 * 1000 = 7일을 밀리초로 표현한 값입니다.
  return diff < 7 * 24 * 60 * 60 * 1000
}

// -----------------------------------------------------------------------------
// useMe — 현재 로그인 유저의 등급(tier)을 확인하는 훅
// -----------------------------------------------------------------------------
// fetchMe API 대신 React Query 캐시에서 꺼내옵니다.
// 로그인 직후 ['me'] 캐시가 채워지므로 추가 서버 요청 없이 읽을 수 있습니다.
function useIsPro(): boolean {
  const { data } = useQuery<{ tier?: string }>({
    queryKey: ['me'],
    // enabled: false = 이 훅이 직접 API를 호출하지 않습니다.
    // 이미 다른 곳에서 ['me']를 호출해 캐시에 저장된 값만 읽습니다.
    enabled: false,
  })
  // tier가 'PRO'이면 true를 반환합니다.
  return data?.tier === 'PRO'
}

// -----------------------------------------------------------------------------
// useWallet — 편자 지갑 잔액을 React Query로 관리하는 훅
// -----------------------------------------------------------------------------
// React Query를 사용하는 이유:
//   같은 페이지에 LockedContent 컴포넌트가 여러 개 있어도
//   지갑 잔액은 한 번만 서버에서 받아오고 캐시를 공유합니다.
//   직접 fetch를 쓰면 컴포넌트 개수만큼 서버에 요청이 가게 됩니다.
function useWallet() {
  // 로그인된 경우에만 지갑을 조회합니다.
  const isLoggedIn = getAuthSnapshot()
  return useQuery({
    queryKey: ['wallet'],
    queryFn: fetchWallet,
    // staleTime = 캐시가 신선한 상태로 유지되는 시간입니다.
    // 1분 동안은 서버에 다시 요청하지 않고 캐시 값을 사용합니다.
    staleTime: 60 * 1000,
    // 로그인하지 않은 경우 쿼리를 실행하지 않습니다.
    enabled: isLoggedIn,
  })
}

// -----------------------------------------------------------------------------
// LockCard — 잠금 오버레이 안에 표시되는 카드 UI
// -----------------------------------------------------------------------------
// 이 컴포넌트는 LockedContent 내부에서만 사용하므로 export하지 않습니다.
interface LockCardProps {
  contentType: ContentType
  cost: number
  adAllowed: boolean
  hasEnough: boolean        // 편자 잔액이 비용보다 많은가?
  isPending: boolean        // API 호출 중인가? (버튼 비활성화용)
  onSpend: () => void       // "편자 소비하기" 버튼 클릭 핸들러
  onWatchAd: () => void     // "광고 보고 열기" 버튼 클릭 핸들러
  onGetMore: () => void     // "편자 더 얻기" 버튼 클릭 핸들러
}

function LockCard({
  contentType,
  cost,
  adAllowed,
  hasEnough,
  isPending,
  onSpend,
  onWatchAd,
  onGetMore,
}: LockCardProps) {
  // 광고 시청 시간: 비용이 3편자 이상이면 30초, 1편자짜리는 15초 광고입니다.
  const adDuration: AdDuration = cost >= 3 ? 30 : 15

  return (
    // 잠금 카드 컨테이너
    // rounded-3xl = 모서리가 크게 둥근 카드 형태입니다.
    // backdrop-blur-[2px] = 배경을 살짝 흐리게 해서 카드를 돋보이게 합니다.
    <div className="w-72 rounded-3xl border border-white/20 bg-brand-navy-900/90 p-6 shadow-2xl backdrop-blur-[2px]">
      {/* 콘텐츠 이름과 자물쇠 아이콘 */}
      <div className="mb-4 text-center">
        <p className="text-3xl">🔒</p>
        <h3 className="mt-2 font-heading text-lg text-white">
          {CONTENT_LABEL[contentType]}
        </h3>
        <p className="mt-1 text-sm text-white/55">
          🔩 {cost}편자로 열 수 있습니다.
        </p>
      </div>

      {/* 편자 소비 버튼 — 잔액이 충분할 때만 활성화 */}
      {hasEnough ? (
        <button
          onClick={onSpend}
          disabled={isPending}
          className="mb-3 w-full rounded-2xl bg-brand-gold-400 py-2.5 font-heading text-sm text-brand-navy-950 transition-opacity hover:opacity-90 disabled:opacity-50"
        >
          {isPending ? '처리 중...' : `🔩 ${cost}편자 소비하기`}
        </button>
      ) : (
        // 편자가 부족하면 안내 문구와 "편자 더 얻기" 버튼을 보여줍니다.
        <>
          <p className="mb-2 text-center text-xs text-white/45">편자가 부족합니다.</p>
          <button
            onClick={onGetMore}
            className="mb-3 w-full rounded-2xl border border-brand-gold-400/60 py-2.5 text-sm text-brand-gold-400 transition-colors hover:bg-brand-gold-400/10"
          >
            🔩 편자 더 얻기
          </button>
        </>
      )}

      {/* 광고 시청 버튼 — 광고가 허용된 콘텐츠에만 표시 */}
      {adAllowed && (
        <>
          {/* 구분선 */}
          <div className="mb-3 flex items-center gap-2 text-xs text-white/30">
            <div className="flex-1 border-t border-white/15" />
            <span>또는</span>
            <div className="flex-1 border-t border-white/15" />
          </div>
          <button
            onClick={onWatchAd}
            className="w-full rounded-2xl border border-white/20 py-2.5 text-sm text-white/80 transition-colors hover:bg-white/8"
          >
            📺 {adDuration}초 광고 보고 열기
          </button>
        </>
      )}
    </div>
  )
}

// -----------------------------------------------------------------------------
// Props — LockedContent가 부모로부터 받는 데이터
// -----------------------------------------------------------------------------
interface LockedContentProps {
  contentType: ContentType   // 잠금할 콘텐츠 종류
  raceId?: number            // 경주 ID (선택, 경주별 콘텐츠에만 필요)
  children: ReactNode        // 잠금 처리할 실제 콘텐츠 (자식 컴포넌트)
}

// -----------------------------------------------------------------------------
// LockedContent — 메인 컴포넌트
// -----------------------------------------------------------------------------
function LockedContent({ contentType, raceId, children }: LockedContentProps) {
  // unlocked = 이 컴포넌트 단에서 잠금이 해제됐는지 여부입니다.
  // 편자 소비 또는 광고 시청 완료 시 true로 바뀝니다.
  const [unlocked, setUnlocked] = useState<boolean>(false)

  // showAdModal = 광고 시청 모달을 보여줄지 여부입니다.
  const [showAdModal, setShowAdModal] = useState<boolean>(false)

  // navigate = 코드에서 다른 페이지로 이동시키는 함수입니다.
  const navigate = useNavigate()

  // useWallet = 현재 편자 잔액을 React Query 캐시에서 읽어옵니다.
  // React Query를 사용하는 이유: 여러 LockedContent가 같은 지갑 데이터를 공유합니다.
  const { data: wallet } = useWallet()

  // isPro = PRO 유저인지 여부입니다.
  const isPro = useIsPro()

  // queryClient = 편자 소비 성공 후 지갑 캐시를 무효화해 잔액을 새로고침합니다.
  const queryClient = useQueryClient()

  // spendMutation = 편자 소비 API 호출을 관리합니다.
  const spendMutation = useMutation({
    mutationFn: () => spendHorseshoe({ contentType, raceId }),
    onSuccess: () => {
      // 편자 소비 성공 → 지갑 캐시를 무효화해서 새 잔액을 받아옵니다.
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      // 잠금 해제
      setUnlocked(true)
    },
  })

  // ── 잠금 해제 조건 ────────────────────────────────────────────────────────
  // 아래 세 가지 중 하나라도 해당하면 콘텐츠를 그대로 보여줍니다.
  if (
    unlocked          // 이 세션에서 이미 잠금 해제함
    || isFreeTrial()  // 가입 후 7일 이내 무료 체험 기간
    || isPro          // PRO 유저
  ) {
    // <>{children}</> = React Fragment. 불필요한 div 없이 자식을 그대로 반환합니다.
    return <>{children}</>
  }
  // ─────────────────────────────────────────────────────────────────────────

  // 편자 잔액이 충분한지 판단합니다.
  // wallet이 아직 로드되지 않으면 false로 처리합니다.
  const cost = CONTENT_COST[contentType]
  const hasEnough = (wallet?.totalHorseshoe ?? 0) >= cost

  // 광고 시청 시간: 1편자짜리는 15초, 3편자 이상은 30초
  const adDuration: AdDuration = cost >= 3 ? 30 : 15

  return (
    // relative = 자식의 absolute 포지셔닝이 이 div를 기준으로 잡히도록 합니다.
    // 즉, 오버레이가 콘텐츠 위에 정확히 겹치게 됩니다.
    <div className="relative">
      {/* ── 흐릿한 콘텐츠 미리보기 ──────────────────────────────────────── */}
      {/* pointer-events-none = 마우스 클릭/터치 이벤트가 이 div를 통과하지 못합니다.
          잠금 상태에서 사용자가 내용을 클릭하거나 버튼을 누르지 못하게 막는 보안 장치입니다. */}
      {/* blur-[4px] = 콘텐츠를 4픽셀만큼 흐리게 합니다.
          blur-sm(= 8px)은 너무 뭉개지고, blur-[4px]가 "보이긴 하지만 못 읽는" 딱 적당한 강도입니다. */}
      {/* select-none = 마우스 드래그로 텍스트를 선택(복사)하지 못하게 막습니다.
          흐린 상태에서도 드래그하면 텍스트가 복사될 수 있으므로 방지합니다. */}
      <div className="pointer-events-none select-none blur-[4px]">
        {children}
      </div>

      {/* ── 잠금 오버레이 ────────────────────────────────────────────────── */}
      {/* absolute inset-0 = 부모(relative div)의 전체 영역을 덮는 포지셔닝입니다.
          top:0, right:0, bottom:0, left:0 을 한꺼번에 지정하는 단축어입니다.
          콘텐츠가 아무리 길어도 오버레이가 항상 정확히 위에 덮입니다. */}
      {/* bg-brand-navy-950/60 = 어두운 네이비 색을 60% 불투명도로 덮어 흐린 콘텐츠를 더 가립니다. */}
      {/* backdrop-blur-[2px] = 오버레이 뒤쪽을 살짝 흐리게 해서 카드가 떠 있는 느낌을 줍니다. */}
      <div className="absolute inset-0 flex items-center justify-center bg-brand-navy-950/60 backdrop-blur-[2px]">
        <LockCard
          contentType={contentType}
          cost={cost}
          adAllowed={AD_ALLOWED[contentType]}
          hasEnough={hasEnough}
          isPending={spendMutation.isPending}
          onSpend={() => spendMutation.mutate()}
          onWatchAd={() => setShowAdModal(true)}
          onGetMore={() => navigate('/wallet')}
        />
      </div>

      {/* 편자 소비 오류 안내 */}
      {spendMutation.isError && (
        <div className="absolute bottom-2 left-0 right-0 text-center">
          <span className="rounded-full bg-red-500/90 px-3 py-1 text-xs text-white">
            편자 소비에 실패했습니다. 다시 시도해 주세요.
          </span>
        </div>
      )}

      {/* ── 광고 시청 모달 ──────────────────────────────────────────────── */}
      {/* showAdModal이 true일 때만 모달을 화면에 렌더링합니다. */}
      {showAdModal && (
        <AdWatchModal
          duration={adDuration}
          onComplete={() => {
            setShowAdModal(false)
            setUnlocked(true)
          }}
          onClose={() => setShowAdModal(false)}
        />
      )}
    </div>
  )
}

export default LockedContent
