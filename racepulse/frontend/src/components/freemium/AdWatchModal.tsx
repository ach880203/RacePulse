// =============================================================================
// AdWatchModal.tsx — 광고 시청 타이머 모달
// =============================================================================
// 역할:
//   실제 광고 SDK 연동은 Phase 4에서 합니다.
//   현재는 타이머를 이용해 광고를 "기다리는 경험"을 구현합니다.
//   타이머가 끝나면 서버에 광고 완료를 알리고, 잠금 해제 콜백을 실행합니다.
// =============================================================================

// useState  = 컴포넌트 안에서 변하는 값(상태)을 관리합니다.
// useEffect = 컴포넌트가 화면에 나타났을 때 또는 값이 바뀔 때 실행됩니다.
// useRef    = 값을 저장하지만, 변해도 화면을 다시 그리지 않습니다. (타이머 ID 저장에 사용)
import { useState, useEffect, useRef } from 'react'

// useMutation = 서버 데이터를 바꾸는 API 호출(POST/PUT/DELETE)을 관리하는 React Query 훅입니다.
// useQueryClient = 특정 쿼리의 캐시를 직접 갱신하거나 무효화할 때 사용합니다.
import { useMutation, useQueryClient } from '@tanstack/react-query'

// earnAd = 광고 시청 완료를 서버에 알리는 API 함수입니다.
import { earnAd } from '../../api/walletApi'

// AdDuration = 광고 시간 타입 (15 | 30 | 60)
import type { AdDuration } from '../../types/wallet'

// -----------------------------------------------------------------------------
// Props — 이 컴포넌트가 부모로부터 받는 데이터
// -----------------------------------------------------------------------------
interface AdWatchModalProps {
  duration: AdDuration             // 광고 시청 시간 (초)
  onComplete: () => void           // 광고 완료 후 실행할 함수 (잠금 해제 처리)
  onClose: () => void              // 모달 닫기 버튼을 눌렀을 때 실행할 함수
}

function AdWatchModal({ duration, onComplete, onClose }: AdWatchModalProps) {
  // remaining = 남은 초. duration부터 시작해서 1씩 줄어듭니다.
  const [remaining, setRemaining] = useState<number>(duration)

  // canSkip = 건너뛰기 버튼 활성화 여부.
  // 15초 광고는 15초 후(즉, 즉시 = remaining이 0일 때) 건너뛸 수 있습니다.
  // 실제 의미: 15초 광고는 끝까지 보면 건너뛸 수 있고,
  //           30초 이상 광고는 건너뛰기 자체가 없습니다.
  const [canSkip, setCanSkip] = useState<boolean>(false)

  // isCompleted = 타이머가 완전히 끝났는지 여부.
  // true가 되면 API를 호출하고 잠금 해제합니다.
  const [isCompleted, setIsCompleted] = useState<boolean>(false)

  // intervalRef = setInterval이 반환하는 ID를 보관합니다.
  // useRef를 쓰는 이유: ID가 바뀌어도 화면을 다시 그릴 필요가 없기 때문입니다.
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // queryClient = React Query 캐시를 다루는 객체입니다.
  // 광고 완료 후 지갑 정보를 새로 받아오도록 캐시를 무효화합니다.
  const queryClient = useQueryClient()

  // useMutation = API를 호출하는 버튼/이벤트에 연결하는 훅입니다.
  // mutateAsync = async/await로 호출할 수 있는 버전입니다.
  const earnAdMutation = useMutation({
    mutationFn: () => earnAd(duration),
    onSuccess: () => {
      // 광고 완료 API 성공 → 지갑 캐시를 무효화해서 잔액을 새로 불러옵니다.
      queryClient.invalidateQueries({ queryKey: ['wallet'] })
      // 부모 컴포넌트에 잠금 해제를 알립니다.
      onComplete()
    },
  })

  // useEffect = 컴포넌트가 처음 화면에 나타날 때 타이머를 시작합니다.
  // 두 번째 인자 [] = "처음 한 번만 실행"이라는 의미입니다.
  useEffect(() => {
    // setInterval = 지정한 밀리초(ms)마다 함수를 반복 실행합니다.
    // 1000ms = 1초마다 remaining을 1 감소시킵니다.
    intervalRef.current = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          // 타이머가 끝났으면 interval을 정지합니다.
          if (intervalRef.current) clearInterval(intervalRef.current)
          setIsCompleted(true)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    // cleanup 함수: 모달이 닫힐 때 타이머를 정리합니다.
    // 정리하지 않으면 모달이 닫혀도 타이머가 계속 돌아갑니다 (메모리 누수).
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [])

  // useEffect — 타이머 완료 시 건너뛰기 버튼 활성화 및 API 호출
  useEffect(() => {
    if (!isCompleted) return

    // 15초 광고는 완료 즉시 건너뛰기 버튼(= 완료 버튼)이 생깁니다.
    // 30초 이상 광고는 건너뛰기가 없으므로 자동으로 API를 호출합니다.
    if (duration === 15) {
      setCanSkip(true)
    } else {
      // 30초 / 60초 광고는 타이머 끝나면 자동으로 완료 처리합니다.
      earnAdMutation.mutate()
    }
  }, [isCompleted]) // isCompleted가 바뀔 때만 실행합니다.

  // progress = 진행률 (0 ~ 100). 남은 시간을 전체 시간으로 나눈 후 100을 곱합니다.
  // 예: remaining=20, duration=30 → progress = (1 - 20/30) * 100 ≈ 33.3
  const progress = Math.round(((duration - remaining) / duration) * 100)

  return (
    // 모달 배경: 화면 전체를 어둡게 덮습니다.
    // fixed inset-0 = 브라우저 화면 전체를 기준으로 사방(top/right/bottom/left = 0)을 채웁니다.
    // z-50 = 다른 요소들 위에 쌓이도록 z-index를 높게 설정합니다.
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      {/* 모달 카드 */}
      <div className="w-full max-w-sm rounded-3xl border border-white/15 bg-brand-navy-900 p-8 shadow-2xl">
        {/* 타이틀 */}
        <div className="mb-6 text-center">
          <p className="text-3xl">📺</p>
          <h2 className="mt-2 font-heading text-xl text-white">광고 시청 중...</h2>
          <p className="mt-1 text-sm text-white/50">
            광고를 끝까지 시청하면 콘텐츠가 열립니다.
          </p>
        </div>

        {/* 진행 바 */}
        {/* 아래 div가 회색 배경 트랙, 내부 div가 실제 진행된 양을 나타냅니다. */}
        <div className="mb-3 h-3 overflow-hidden rounded-full bg-white/15">
          <div
            className="h-full rounded-full bg-brand-gold-400 transition-all duration-1000"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 남은 시간 표시 */}
        <div className="mb-6 flex items-center justify-between text-sm">
          <span className="text-white/50">남은 시간</span>
          <span className="font-heading text-brand-gold-400">{remaining}초</span>
        </div>

        {/* 건너뛰기 안내 */}
        {duration === 15 && !canSkip && (
          <p className="mb-4 text-center text-xs text-white/40">
            광고 완료 후 닫기 가능
          </p>
        )}

        {/* 버튼 영역 */}
        <div className="flex flex-col gap-2">
          {/* 타이머가 완료된 경우: 완료 버튼을 보여줍니다. */}
          {canSkip && (
            <button
              onClick={() => earnAdMutation.mutate()}
              disabled={earnAdMutation.isPending}
              className="w-full rounded-2xl bg-brand-gold-400 py-3 font-heading text-brand-navy-950 transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {earnAdMutation.isPending ? '처리 중...' : '✅ 완료 — 콘텐츠 열기'}
            </button>
          )}

          {/* 닫기 버튼: 타이머가 끝나지 않으면 비활성화합니다. */}
          {/* 광고 중간에 닫으면 보상을 받을 수 없음을 안내합니다. */}
          <button
            onClick={onClose}
            disabled={!isCompleted}
            className="w-full rounded-2xl border border-white/15 py-3 text-sm text-white/60 transition-colors hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-30"
          >
            {isCompleted ? '× 닫기' : `× 닫기 (${remaining}초 남음)`}
          </button>
        </div>

        {/* API 오류 안내 */}
        {earnAdMutation.isError && (
          <p className="mt-3 text-center text-xs text-red-400">
            처리 중 오류가 발생했습니다. 다시 시도해 주세요.
          </p>
        )}

        {/* TODO: [Phase 4] Google AdSense / 카카오 광고 SDK 연동 후 실제 광고 영상으로 교체 */}
      </div>
    </div>
  )
}

export default AdWatchModal
