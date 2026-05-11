// =============================================================================
// prediction.ts — 예측 결과 페이지 전용 TypeScript 타입 정의
// =============================================================================
// 백엔드 DTO와 프런트 타입을 맞춰두면,
// API 응답 형식이 바뀌었을 때 화면 코드에서 즉시 타입 오류로 확인할 수 있습니다.
// =============================================================================

/** 말 1마리의 예측 카드 데이터 */
export interface PredictionItem {
  horseId: number
  horseName: string
  gateNo: number | null
  predictedRank: number
  winProbability: number | null
  placeProbability: number | null
  conditionGrade: '최하' | '하' | '중' | '상' | '최상'
  keyFeatures: string[]
}

/** 경주 예측 결과 전체 응답 */
export interface PredictionResponse {
  raceId: number
  raceName: string
  modelVersion: string | null
  top1Accuracy: number | null
  top3Accuracy: number | null
  predictions: PredictionItem[]
}

export interface SimulationHorse {
  horseId: number
  horseName: string
  rankDistribution: Record<string, number>
  expectedRank: number
}

export interface SimulationResponse {
  raceId: number
  nSimulations: number
  horses: SimulationHorse[]
  upsetProbability: number
  computedAt: string
}
