// =============================================================================
// predictionApi.ts — 예측 결과 API 호출 함수
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { PredictionResponse, SimulationResponse } from '../types/prediction'

/**
 * 특정 경주의 예측 결과를 조회합니다.
 * Spring Boot: GET /api/v1/predictions/{raceId}
 */
export async function fetchPrediction(raceId: number): Promise<PredictionResponse> {
  const response = await axiosInstance.get<ApiResponse<PredictionResponse>>(
    `/predictions/${raceId}`,
  )
  return response.data.data
}

export async function fetchPredictionSimulation(raceId: number): Promise<SimulationResponse> {
  const response = await axiosInstance.get<ApiResponse<SimulationResponse>>(
    `/predictions/${raceId}/simulation`,
  )
  return response.data.data
}
