// =============================================================================
// person.ts — 기수 / 조교사 TypeScript 타입 정의
// =============================================================================

import type { MeetCode } from './race'

/** 기수 1건 */
export interface Jockey {
  id: number
  name: string
  meetCode: MeetCode
  winRate: number | null    // 승률 (0~1)
  placeRate: number | null  // 연대율 (0~1)
  totalRaces: number | null
  totalWins: number | null
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
