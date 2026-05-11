// =============================================================================
// useRaces.ts — 경주 데이터를 가져오는 React Query 훅 모음
// =============================================================================
// React Query(@tanstack/react-query)란?
//   서버에서 데이터를 가져오고, 캐시하고, 화면을 자동으로 업데이트해주는 라이브러리입니다.
//
//   useState 만 쓸 때 문제:
//     - 로딩 중인지, 오류가 났는지 직접 상태를 만들어야 합니다.
//     - 같은 API를 여러 컴포넌트에서 쓰면 중복 요청이 발생합니다.
//     - 데이터가 오래됐는지 직접 확인해야 합니다.
//
//   React Query를 쓰면:
//     - isLoading, isError, data 상태를 자동으로 관리해줍니다.
//     - 같은 queryKey의 데이터는 캐시에서 바로 꺼내줍니다 (중복 요청 방지).
//     - staleTime 이후 자동으로 데이터를 새로 불러옵니다.
// =============================================================================

// useQuery = 서버에서 데이터를 읽어오는 React Query 핵심 훅입니다.
import { useQuery } from '@tanstack/react-query'
import {
  fetchRaceById,
  fetchRaceEntries,
  fetchRaceResult,
  fetchRaces,
  fetchUpcomingRaces,
  fetchWeather,
} from '../api/raceApi'
import type { RaceListParams } from '../types/race'

// =============================================================================
// Query Key 상수
// =============================================================================
// queryKey = React Query가 캐시를 구분하는 고유 식별자입니다.
// 배열 형식으로 작성하면 계층적으로 관리하기 쉽습니다.
// 예: ['races', { meetCode: 'SC', rcDate: '2026-05-07' }]
export const raceKeys = {
  all:      ()                        => ['races'] as const,
  list:     (params: RaceListParams)  => ['races', 'list', params] as const,
  detail:   (id: number)              => ['races', 'detail', id] as const,
  upcoming: ()                        => ['races', 'upcoming'] as const,
  entries:  (id: number)              => ['races', 'entries', id] as const,
  result:   (id: number)              => ['races', 'result', id] as const,
  weather:  (meet: string, date: string) => ['weather', meet, date] as const,
}

/**
 * 경주 목록을 가져오는 훅입니다.
 * 파라미터가 바뀌면 자동으로 API를 다시 호출합니다.
 */
export function useRaces(params: RaceListParams = {}) {
  return useQuery({
    // queryKey가 바뀌면(필터 변경 시) React Query가 자동으로 새 데이터를 가져옵니다.
    queryKey: raceKeys.list(params),
    queryFn: () => fetchRaces(params),

    // staleTime = 데이터를 "신선하다"고 판단하는 시간입니다.
    // 5분 동안은 같은 데이터를 다시 요청하지 않습니다.
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * 경주 1건 상세를 가져오는 훅입니다.
 */
export function useRace(raceId: number | undefined) {
  return useQuery({
    queryKey: raceKeys.detail(raceId!),
    queryFn: () => fetchRaceById(raceId!),
    // raceId가 없으면 쿼리를 실행하지 않습니다.
    // enabled = false 이면 자동 실행이 멈춥니다.
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * 오늘 예정된 경주 목록을 가져오는 훅입니다.
 * 홈 페이지 "오늘의 경주" 섹션에서 사용합니다.
 */
export function useUpcomingRaces() {
  return useQuery({
    queryKey: raceKeys.upcoming(),
    queryFn: fetchUpcomingRaces,
    staleTime: 5 * 60 * 1000,
  })
}

/** 특정 경주의 출전 명단을 가져오는 훅입니다. */
export function useRaceEntries(raceId: number | undefined) {
  return useQuery({
    queryKey: raceKeys.entries(raceId!),
    queryFn: () => fetchRaceEntries(raceId!),
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}

/** 특정 경주의 결과를 가져오는 훅입니다. */
export function useRaceResult(raceId: number | undefined) {
  return useQuery({
    queryKey: raceKeys.result(raceId!),
    queryFn: () => fetchRaceResult(raceId!),
    enabled: raceId != null,
    staleTime: 5 * 60 * 1000,
  })
}

/** 경마장·날짜 날씨 예보를 가져오는 훅입니다. */
export function useWeather(meetCode: string | undefined, date: string | undefined) {
  return useQuery({
    queryKey: raceKeys.weather(meetCode!, date!),
    queryFn: () => fetchWeather(meetCode!, date!),
    enabled: !!meetCode && !!date,
    staleTime: 60 * 60 * 1000, // 날씨는 1시간 캐시
  })
}
