// =============================================================================
// useRacecourses.ts — 경마장 데이터를 가져오는 React Query 훅
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchRacecourses } from '../api/racecourseApi'

export const racecourseKeys = {
  all: () => ['racecourses'] as const,
}

/**
 * 전체 경마장 목록을 가져오는 훅입니다.
 * 경마장은 3개뿐이고 거의 바뀌지 않으므로 staleTime을 1시간으로 설정합니다.
 */
export function useRacecourses() {
  return useQuery({
    queryKey: racecourseKeys.all(),
    queryFn: fetchRacecourses,
    // 1시간 동안 캐시를 유지합니다. 경마장 정보는 자주 바뀌지 않습니다.
    staleTime: 60 * 60 * 1000,
  })
}
