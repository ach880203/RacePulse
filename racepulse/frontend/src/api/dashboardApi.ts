// =============================================================================
// dashboardApi.ts — 대시보드 API 호출 함수
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { AccuracyStats } from '../types/dashboard'

/**
 * ML 모델 예측 정확도 통계를 조회합니다.
 * Spring Boot: GET /api/v1/dashboard/accuracy
 */
export async function fetchAccuracyStats(): Promise<AccuracyStats> {
  const response = await axiosInstance.get<ApiResponse<AccuracyStats>>(
    '/dashboard/accuracy',
  )
  return response.data.data
}
