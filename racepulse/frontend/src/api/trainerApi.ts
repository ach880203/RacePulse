// =============================================================================
// trainerApi.ts — 조교사 관련 API 호출 함수 모음
// =============================================================================
// TODO: [Phase 2] Spring Boot 조교사 API 완성 후 실제 엔드포인트로 교체

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { Trainer } from '../types/person'

/**
 * 조교사 1건 상세를 조회합니다.
 * Spring Boot: GET /api/v1/trainers/{trainerId}
 */
export async function fetchTrainerById(trainerId: number): Promise<Trainer> {
  const response = await axiosInstance.get<ApiResponse<Trainer>>(
    `/trainers/${trainerId}`,
  )
  return response.data.data
}
