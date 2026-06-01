// =============================================================================
// commentary.ts — AI 해설 API 응답 타입
// =============================================================================
// 백엔드가 Spring Boot → FastAPI 순서로 해설을 프록시하므로,
// 실제 응답은 정상 해설과 "준비 중" 메시지 두 형태가 모두 올 수 있습니다.
// =============================================================================

export type CommentaryType = 'PRE' | 'POST'

/** AI 해설 1건 */
export interface CommentaryResponse {
  raceId?: number
  type?: CommentaryType
  content?: string
  message?: string
  modelUsed?: string
  generatedAt?: string
  source?: string
  qualityScore?: number | string | null
}
