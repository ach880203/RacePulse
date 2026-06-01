// =============================================================================
// commentaryApi.ts — AI 해설 API 호출 함수
// =============================================================================
// 프론트엔드는 FastAPI를 직접 호출하지 않고 Spring Boot의 /api/v1/commentary만 호출합니다.
// 이렇게 해야 인증, CORS, 서버 주소 변경을 axiosInstance 한 곳에서 관리할 수 있습니다.
// =============================================================================

import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { CommentaryResponse } from '../types/commentary'

type FastApiCommentaryWrapper = {
  success?: boolean
  data?: CommentaryResponse
  message?: string
}

function unwrapCommentary(rawData: CommentaryResponse | FastApiCommentaryWrapper): CommentaryResponse {
  // Spring Boot가 FastAPI 응답 전체를 data에 담아 전달할 수 있어 한 번 더 풀어줍니다.
  // 이 처리가 없으면 화면이 content 대신 중첩된 data 객체를 보게 되어 해설 본문을 찾지 못합니다.
  if ('data' in rawData && rawData.data) {
    return rawData.data
  }

  return rawData
}

/** 특정 경주의 사전 해설을 조회합니다. */
export async function fetchPreRaceCommentary(raceId: number): Promise<CommentaryResponse> {
  const response = await axiosInstance.get<ApiResponse<CommentaryResponse | FastApiCommentaryWrapper>>(
    `/commentary/${raceId}/pre`,
  )
  return unwrapCommentary(response.data.data)
}

/** 특정 경주의 결과 해설을 조회합니다. */
export async function fetchPostRaceCommentary(raceId: number): Promise<CommentaryResponse> {
  const response = await axiosInstance.get<ApiResponse<CommentaryResponse | FastApiCommentaryWrapper>>(
    `/commentary/${raceId}/post`,
  )
  return unwrapCommentary(response.data.data)
}
