// =============================================================================
// WalletHUD.tsx — 헤더 편자 잔액 표시 컴포넌트
// =============================================================================
// 역할:
//   헤더에 현재 편자(🔩)와 건초(🥇) 잔액을 표시합니다.
//   클릭하면 /wallet 페이지로 이동합니다.
//   로그인하지 않은 경우에는 아무것도 표시하지 않습니다.
//   오늘 광고 시청 한도에 도달하면 🔩 옆에 빨간 뱃지를 표시합니다.
// =============================================================================

// useQuery = 서버 데이터를 조회하고 캐싱하는 React Query 훅입니다.
import { useQuery } from '@tanstack/react-query'

// Link = 페이지 전체 새로고침 없이 SPA 내부 페이지로 이동하는 링크입니다.
import { Link } from 'react-router-dom'

// getAuthSnapshot = 현재 로그인 상태(토큰 존재 여부)를 확인하는 함수입니다.
import { getAuthSnapshot } from '../../store/authStore'

// fetchWallet = 편자 지갑 잔액을 서버에서 조회하는 API 함수입니다.
import { fetchWallet } from '../../api/walletApi'

function WalletHUD() {
  // isLoggedIn = 현재 로그인 상태입니다. 로그인 안 하면 지갑 조회를 하지 않습니다.
  const isLoggedIn = getAuthSnapshot()

  // useQuery로 지갑 잔액을 가져옵니다.
  // queryKey: ['wallet'] = 이 키로 캐시를 저장합니다.
  //   LockedContent.tsx에서도 같은 키를 사용하므로, 한 번 불러온 데이터를 공유합니다.
  // staleTime = 1분간 캐시를 신선하게 유지합니다. (1분마다 자동 새로고침)
  // refetchInterval = 2분마다 자동으로 서버에서 최신 잔액을 가져옵니다.
  // enabled: isLoggedIn = 로그인된 경우에만 조회합니다.
  const { data: wallet } = useQuery({
    queryKey: ['wallet'],
    queryFn: fetchWallet,
    staleTime: 60 * 1000,
    refetchInterval: 2 * 60 * 1000,
    enabled: isLoggedIn,
  })

  // 로그인하지 않은 경우 아무것도 표시하지 않습니다.
  // null을 반환하면 React가 아무것도 그리지 않습니다.
  if (!isLoggedIn || !wallet) return null

  // adLimitReached = 오늘 광고 시청 한도에 도달했는지 여부입니다.
  // adWatchedToday >= adLimitToday 이면 더 이상 광고를 볼 수 없습니다.
  const adLimitReached = wallet.adWatchedToday >= wallet.adLimitToday

  return (
    // Link = 클릭 시 /wallet 페이지로 이동합니다.
    // flex items-center gap-3 = 편자와 건초 아이콘을 한 줄로 가로 정렬합니다.
    <Link
      to="/wallet"
      className="flex items-center gap-3 rounded-2xl border border-white/15 bg-white/5 px-4 py-2 text-sm transition-colors hover:bg-white/10"
      aria-label="내 편자 지갑 보기"
    >
      {/* 편자(🔩) 잔액 */}
      <span className="relative flex items-center gap-1">
        {/* 광고 한도 도달 시 빨간 뱃지를 표시합니다.
            absolute -top-1 -right-1 = 부모 span의 우측 상단 모서리에 붙입니다. */}
        {adLimitReached && (
          <span
            className="absolute -right-1 -top-1 flex h-2 w-2 rounded-full bg-red-500"
            title="오늘 광고 시청 한도에 도달했습니다."
          />
        )}
        <span>🔩</span>
        {/* font-heading = 브랜드 전용 폰트. 숫자가 더 명확하게 보입니다. */}
        <span className="font-heading text-white">{wallet.totalHorseshoe.toLocaleString()}</span>
      </span>

      {/* 구분선 */}
      <span className="text-white/20">|</span>

      {/* 건초(🥇) 잔액 */}
      <span className="flex items-center gap-1">
        <span>🥇</span>
        <span className="font-heading text-white">{wallet.totalHay.toLocaleString()}</span>
      </span>
    </Link>
  )
}

export default WalletHUD
