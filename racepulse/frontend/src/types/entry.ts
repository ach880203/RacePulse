// =============================================================================
// entry.ts — 출전 명단 관련 TypeScript 타입 정의
// =============================================================================

import type { DataStatus } from './race'

/** 출전마 1건 (race_entries 테이블 기반) */
export interface RaceEntry {
  id: number
  raceId: number
  horseId: number
  horseName: string
  horseEngName: string | null
  gateNo: number          // 마번(게이트 번호)
  jockeyId: number | null
  jockeyName: string | null
  trainerId: number | null
  trainerName: string | null
  weight: number | null   // 마체중 (kg)
  burden: number | null   // 부담중량 (kg)
  odds: number | null     // 배당률
  dataStatus: DataStatus | null
}

/** 경주 결과 1건 */
export interface RaceResult {
  id: number
  raceId: number
  horseId: number
  horseName: string
  gateNo: number
  finalOdds: number | null
  finishOrder: number | null  // 착순 (1위, 2위 ...)
  finishTime: string | null   // "1:12.5" 형식
  margin?: string | null       // 1위와의 차이, 백엔드 데이터가 없으면 화면에서 '-'로 보정합니다.
  jockeyName: string | null
}
