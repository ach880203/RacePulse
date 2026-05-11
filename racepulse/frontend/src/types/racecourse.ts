// =============================================================================
// racecourse.ts — 경마장 관련 TypeScript 타입 정의
// =============================================================================

import type { MeetCode } from './race'

/** 경마장 1건 */
export interface Racecourse {
  id: number
  meetCode: MeetCode
  name: string          // 예: "서울경마공원"
  location: string      // 예: "경기도 과천시"
  trackTypes: string[]  // 예: ["잔디", "모래"]
}
