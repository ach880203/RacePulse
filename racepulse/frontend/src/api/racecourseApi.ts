// =============================================================================
// racecourseApi.ts — 경마장 관련 API 호출 함수 모음
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { Racecourse } from '../types/racecourse'

/**
 * 전체 경마장 목록을 조회합니다.
 * Spring Boot: GET /api/v1/racecourses
 * 경마장은 SC, BU, JJ 3개이므로 페이지네이션 없이 전체를 한 번에 가져옵니다.
 */
export async function fetchRacecourses(): Promise<Racecourse[]> {
  const response = await axiosInstance.get<ApiResponse<Racecourse[]>>('/racecourses')
  return response.data.data
}
