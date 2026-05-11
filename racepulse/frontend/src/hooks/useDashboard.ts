// =============================================================================
// useDashboard.ts — 대시보드 데이터를 가져오는 React Query 훅
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchAccuracyStats } from '../api/dashboardApi'

export const dashboardKeys = {
  accuracy: () => ['dashboard', 'accuracy'] as const,
}

/**
 * ML 모델 예측 정확도 통계를 가져오는 훅입니다.
 * staleTime을 10분으로 설정합니다. 정확도 통계는 자주 바뀌지 않습니다.
 */
export function useAccuracyStats() {
  return useQuery({
    queryKey: dashboardKeys.accuracy(),
    queryFn: fetchAccuracyStats,
    staleTime: 10 * 60 * 1000,
  })
}
