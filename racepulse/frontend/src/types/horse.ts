// =============================================================================
// horse.ts — 경주마 관련 TypeScript 타입 정의
// =============================================================================

import type { MeetCode } from './race'

/** 경주마 1건 */
export interface Horse {
  id: number
  name: string          // 한글 마명
  engName: string | null
  birthYear: number | null
  sex: string | null    // 수말/암말/거세마
  color: string | null
  origin: string | null // 국산/외산
  fatherName: string | null
  motherName: string | null
  owner: string | null
  meetCode: MeetCode
  rating1: number | null
  rating2: number | null
  rating3: number | null
  rating4: number | null
  isActive: boolean
  thumbnailUrl: string | null
  photoUrl: string | null

/** 경주마 목록 조회 파라미터 */
export interface HorseListParams {
  meetCode?: MeetCode
  name?: string
  page?: number
  size?: number
}
