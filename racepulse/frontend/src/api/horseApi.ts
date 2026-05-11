// =============================================================================
// horseApi.ts — 경주마 관련 API 호출 함수 모음
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse, PageResponse } from '../types/race'
import type { Horse, HorseListParams } from '../types/horse'

/**
 * 경주마 목록을 페이지 단위로 조회합니다.
 * Spring Boot: GET /api/v1/horses
 */
export async function fetchHorses(params: HorseListParams = {}): Promise<PageResponse<Horse>> {
  const response = await axiosInstance.get<ApiResponse<PageResponse<Horse>>>('/horses', {
    params,
  })
  return response.data.data
}

/**
 * 경주마 1건 상세를 조회합니다.
 * Spring Boot: GET /api/v1/horses/{horseId}
 */
export async function fetchHorseById(horseId: number): Promise<Horse> {
  const response = await axiosInstance.get<ApiResponse<Horse>>(`/horses/${horseId}`)
  return response.data.data
}
