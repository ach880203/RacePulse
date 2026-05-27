// =============================================================================
// person.ts — 기수 / 조교사 TypeScript 타입 정의
// =============================================================================

import type { MeetCode } from './race'

/** 기수 1건 */
export interface Jockey {
  id: number
  licenseNo: string | null
  name: string
  engName: string | null
  birthYear: number | null
  debutYear: number | null
  meetCode: string
  affiliation: string | null
  photoUrl: string | null
  isActive: boolean
  winRateTotal: number | null    // 통산 승률 (0~1)
  winRateRecent: number | null   // 최근 승률 (0~1)
  placeRateTotal: number | null  // 통산 연대율 (0~1)
}

/** 기수 목록 조회 파라미터 */
export interface JockeyListParams {
  meetCode?: string
  name?: string
  page?: number
  size?: number
}

/** 조교사 1건 */
export interface Trainer {
  id: number
  name: string
  meetCode: MeetCode
  winRate: number | null
  totalRaces: number | null
  totalWins: number | null
  horseCount: number | null // 관리 중인 말 수
}

/** 기수/조교사 최근 성적 */
export interface RecentRecord {
  date: string
  raceName: string
  finishOrder: number | null
  horseName: string
}
