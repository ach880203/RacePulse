// =============================================================================
// useCommentary.ts — AI 해설 데이터를 가져오는 React Query 훅
// =============================================================================
// 해설은 사전/결과 두 종류가 있고, 경주 상태와 탭 선택에 따라 필요한 것만 조회합니다.
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchPostRaceCommentary, fetchPreRaceCommentary } from '../api/commentaryApi'

export const commentaryKeys = {
  pre: (raceId: number) => ['commentary', raceId, 'pre'] as const,
  post: (raceId: number) => ['commentary', raceId, 'post'] as const,
}

/** 사전 해설은 경주 전후 모두 볼 수 있으므로 raceId가 있을 때만 조회합니다. */
export function usePreRaceCommentary(raceId: number | undefined) {
  return useQuery({
    queryKey: commentaryKeys.pre(raceId!),
    queryFn: () => fetchPreRaceCommentary(raceId!),
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}

/** 결과 해설은 완료 경주에서만 필요하므로 enabled로 불필요한 요청을 막습니다. */
export function usePostRaceCommentary(raceId: number | undefined, enabled: boolean) {
  return useQuery({
    queryKey: commentaryKeys.post(raceId!),
    queryFn: () => fetchPostRaceCommentary(raceId!),
    enabled: raceId != null && enabled,
    staleTime: 5 * 60 * 1000,
  })
}
