// =============================================================================
// usePrediction.ts — 예측 결과를 가져오는 React Query 훅
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchPrediction, fetchPredictionSimulation } from '../api/predictionApi'

export const predictionKeys = {
  detail: (raceId: number) => ['predictions', raceId] as const,
  simulation: (raceId: number) => ['predictions', raceId, 'simulation'] as const,
}

/**
 * raceId가 있을 때만 예측 결과를 조회합니다.
 * 경주 상세 페이지에서 이동하는 구조라 raceId가 비어 있는 경우를 안전하게 막아둡니다.
 */
export function usePrediction(raceId: number | undefined) {
  return useQuery({
    queryKey: predictionKeys.detail(raceId!),
    queryFn: () => fetchPrediction(raceId!),
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePredictionSimulation(raceId: number | undefined) {
  return useQuery({
    queryKey: predictionKeys.simulation(raceId!),
    queryFn: () => fetchPredictionSimulation(raceId!),
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}
