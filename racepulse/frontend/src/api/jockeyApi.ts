// =============================================================================
// jockeyApi.ts — 기수 관련 API 호출 함수 모음
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse, PageResponse } from '../types/race'
import type { Jockey, JockeyListParams } from '../types/person'

/**
 * 기수 목록을 페이지 단위로 조회합니다.
 * Spring Boot: GET /api/v1/jockeys
 */
export async function fetchJockeys(params: JockeyListParams = {}): Promise<PageResponse<Jockey>> {
  const response = await axiosInstance.get<ApiResponse<PageResponse<Jockey>>>('/jockeys', {
    params,
  })
  return response.data.data
}

/**
 * 기수 1건 상세를 조회합니다.
 * Spring Boot: GET /api/v1/jockeys/{jockeyId}
 */
export async function fetchJockeyById(jockeyId: number): Promise<Jockey> {
  const response = await axiosInstance.get<ApiResponse<Jockey>>(`/jockeys/${jockeyId}`)
  return response.data.data
}
