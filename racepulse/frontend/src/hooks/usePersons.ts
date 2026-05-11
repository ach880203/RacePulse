// =============================================================================
// usePersons.ts — 기수 / 조교사 데이터를 가져오는 React Query 훅 모음
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchJockeyById } from '../api/jockeyApi'
import { fetchTrainerById } from '../api/trainerApi'

export const jockeyKeys = {
  detail: (id: number) => ['jockeys', 'detail', id] as const,
}

export const trainerKeys = {
  detail: (id: number) => ['trainers', 'detail', id] as const,
}

/** 기수 1건 상세를 가져오는 훅입니다. */
export function useJockey(jockeyId: number | undefined) {
  return useQuery({
    queryKey: jockeyKeys.detail(jockeyId!),
    queryFn: () => fetchJockeyById(jockeyId!),
    enabled: jockeyId != null,
    staleTime: 10 * 60 * 1000,
  })
}

/** 조교사 1건 상세를 가져오는 훅입니다. */
export function useTrainer(trainerId: number | undefined) {
  return useQuery({
    queryKey: trainerKeys.detail(trainerId!),
    queryFn: () => fetchTrainerById(trainerId!),
    enabled: trainerId != null,
    staleTime: 10 * 60 * 1000,
  })
}
