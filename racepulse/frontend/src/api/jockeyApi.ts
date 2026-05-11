// =============================================================================
// jockeyApi.ts — 기수 관련 API 호출 함수 모음
// =============================================================================
// TODO: [Phase 2] Spring Boot 기수 API 완성 후 실제 엔드포인트로 교체

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { Jockey } from '../types/person'

/**
 * 기수 1건 상세를 조회합니다.
 * Spring Boot: GET /api/v1/jockeys/{jockeyId}
 */
export async function fetchJockeyById(jockeyId: number): Promise<Jockey> {
  const response = await axiosInstance.get<ApiResponse<Jockey>>(
    `/jockeys/${jockeyId}`,
  )
  return response.data.data
}
