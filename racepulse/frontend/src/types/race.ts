// =============================================================================
// race.ts — 경주 관련 TypeScript 타입 정의
// =============================================================================
// TypeScript interface란?
//   "이 데이터는 반드시 이런 모양이어야 한다"를 미리 약속하는 설계도입니다.
//   예: Race 타입을 쓰면 id, meetCode, rcDate... 가 반드시 있어야 합니다.
//   잘못된 구조의 데이터를 쓰면 코드 작성 중에 즉시 오류를 알려줍니다.
// =============================================================================

/** 경주 상태 */
export type RaceStatus = 'SCHEDULED' | 'COMPLETED' | 'CANCELLED'

/** 데이터 수집 상태 (백엔드 data_status 컬럼) */
export type DataStatus = 'READY' | 'UPDATING' | 'COLLECTED' | 'JOCKEY_CHANGED'

/** 경마장 코드 */
export type MeetCode = 'SC' | 'BU' | 'JJ'

/** 경주 1건 */
export interface Race {
  id: number
  meetCode: MeetCode
  rcDate: string          // "2026-05-07" 형식 날짜
  raceNo: number
  raceName: string
  distance: number        // 단위: 미터
  trackType: string | null
  prizeMoney: number | null // 단위: 원
  weather: string | null
  startTime: string | null // "11:00" 형식
  status: RaceStatus
  raceClass: string | null
  dataStatus?: DataStatus
}

/** 페이지네이션 응답 래퍼
 *  Spring Boot의 Page<T> 응답 구조와 맞춥니다.
 */
export interface PageResponse<T> {
  content: T[]
  totalElements: number
  totalPages: number
  number: number    // 현재 페이지 번호 (0부터 시작)
  size: number      // 한 페이지 크기
  first: boolean
  last: boolean
}

/** 공통 API 응답 래퍼 (Spring Boot ApiResponse<T> 와 대응) */
export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
}

/** 경주 목록 조회 파라미터 */
export interface RaceListParams {
  meetCode?: MeetCode | 'ALL'
  rcDate?: string
  status?: RaceStatus
  page?: number
  size?: number
}
