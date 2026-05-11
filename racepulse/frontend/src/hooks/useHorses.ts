// =============================================================================
// useHorses.ts — 경주마 데이터를 가져오는 React Query 훅 모음
// =============================================================================

import { useQuery } from '@tanstack/react-query'
import { fetchHorseById, fetchHorses } from '../api/horseApi'
import type { HorseListParams } from '../types/horse'

export const horseKeys = {
  all:    ()                     => ['horses'] as const,
  list:   (params: HorseListParams) => ['horses', 'list', params] as const,
  detail: (id: number)           => ['horses', 'detail', id] as const,
}

/** 경주마 목록을 가져오는 훅입니다. */
export function useHorses(params: HorseListParams = {}) {
  return useQuery({
    queryKey: horseKeys.list(params),
    queryFn: () => fetchHorses(params),
    staleTime: 5 * 60 * 1000,
  })
}

/** 경주마 1건 상세를 가져오는 훅입니다. */
export function useHorse(horseId: number | undefined) {
  return useQuery({
    queryKey: horseKeys.detail(horseId!),
    queryFn: () => fetchHorseById(horseId!),
    enabled: horseId != null,
    staleTime: 5 * 60 * 1000,
  })
}
