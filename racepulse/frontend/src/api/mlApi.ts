// =============================================================================
// mlApi.ts — ML 서버 예측/시뮬레이션 API 호출 함수
// =============================================================================
// API 호출은 컴포넌트 안에 직접 쓰지 않고 api 폴더에 모아 둡니다.
// 이렇게 하면 화면은 "데이터를 보여 주는 일"에 집중하고, 서버 주소 변경은 이 파일에서 관리할 수 있습니다.
// =============================================================================

import axiosInstance from './axiosInstance' // 공통 서버 주소, JWT 토큰, 오류 처리가 설정된 Axios 객체입니다.
import type { ApiResponse } from '../types/race' // Spring Boot 공통 응답 모양을 설명하는 타입입니다.
import type { PredictionResponse, SimulationResponse } from '../types/prediction' // ML 예측/시뮬레이션 응답 타입입니다.

export async function fetchMlPrediction(raceId: number): Promise<PredictionResponse> {
  // GET /ml/predict/{raceId}
  // 기본 예측 데이터는 서버에서 조회하고, Counterfactual 자체 계산은 브라우저 Worker에서 처리합니다.
  const response = await axiosInstance.get<ApiResponse<PredictionResponse>>(
    `/ml/predict/${raceId}`,
  )

  return response.data.data
}

export async function fetchMlSimulationResult(raceId: number): Promise<SimulationResponse> {
  // GET /ml/simulate/{raceId}/result
  // 서버에 저장된 기본 Monte Carlo 결과를 조회할 때 사용하는 함수입니다.
  const response = await axiosInstance.get<ApiResponse<SimulationResponse>>(
    `/ml/simulate/${raceId}/result`,
  )

  return response.data.data
}
