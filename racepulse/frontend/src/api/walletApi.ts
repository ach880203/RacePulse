// =============================================================================
// walletApi.ts — 편자(Horseshoe) 지갑 관련 API 호출 함수
// =============================================================================
// 이 파일의 역할:
//   컴포넌트가 서버에 직접 요청을 보내는 대신,
//   이 파일의 함수들을 통해 요청을 보내도록 합니다.
//   → 규칙 9: API 호출 코드는 src/api/ 폴더에 분리합니다.
// =============================================================================

// axiosInstance = JWT 토큰을 자동으로 붙여서 요청을 보내는 설정된 axios입니다.
import axiosInstance from './axiosInstance'

// 지갑 관련 타입들을 가져옵니다.
import type {
  WalletResponse,
  SpendResponse,
  Transaction,
  PageResponse,
  ContentType,
  AdDuration,
} from '../types/wallet'

// ApiResponse = 서버가 항상 { success, data, message } 형태로 응답하는 공통 포장지입니다.
// (규칙 5: API 응답 형식 통일)
import type { ApiResponse } from '../types/race'

// -----------------------------------------------------------------------------
// fetchWallet — 내 편자 지갑 잔액 조회
// -----------------------------------------------------------------------------
// async/await란?
//   서버 응답을 기다려야 하는 비동기 작업을 "마치 동기처럼" 읽기 쉽게 쓰는 방법입니다.
//   await 앞에서 기다린 후 결과를 받아옵니다.
export const fetchWallet = async (): Promise<WalletResponse> => {
  // GET /api/v1/wallet → 내 지갑 잔액을 조회합니다.
  const response = await axiosInstance.get<ApiResponse<WalletResponse>>('/wallet')
  // response.data = axios가 받은 JSON 전체
  // response.data.data = 규칙 5의 포장지 안에 든 실제 데이터
  return response.data.data
}

// -----------------------------------------------------------------------------
// earnAttendance — 출석 체크로 편자 획득
// -----------------------------------------------------------------------------
// 하루 한 번 출석 체크를 하면 편자를 줍니다.
export const earnAttendance = async (): Promise<WalletResponse> => {
  // POST /api/v1/wallet/earn/attendance → 오늘 출석 처리 후 갱신된 지갑을 반환합니다.
  const response = await axiosInstance.post<ApiResponse<WalletResponse>>(
    '/wallet/earn/attendance',
  )
  return response.data.data
}

// -----------------------------------------------------------------------------
// earnAd — 광고 시청으로 편자/건초 획득
// -----------------------------------------------------------------------------
// duration = 광고 시청 시간(초). 15초 / 30초 / 60초만 허용합니다.
// AdDuration 타입 덕분에 다른 값을 넣으면 TypeScript가 에러를 냅니다.
export const earnAd = async (duration: AdDuration): Promise<WalletResponse> => {
  // POST /api/v1/wallet/earn/ad?duration=30 → 광고 시청 완료를 서버에 알립니다.
  const response = await axiosInstance.post<ApiResponse<WalletResponse>>(
    '/wallet/earn/ad',
    null,
    { params: { duration } }, // query parameter로 duration을 전달합니다.
  )
  return response.data.data
}

// -----------------------------------------------------------------------------
// earnQuiz — 퀴즈 정답으로 편자 획득
// -----------------------------------------------------------------------------
export const earnQuiz = async (): Promise<WalletResponse> => {
  // POST /api/v1/wallet/earn/quiz → 퀴즈 완료 후 지갑 잔액을 반환합니다.
  const response = await axiosInstance.post<ApiResponse<WalletResponse>>(
    '/wallet/earn/quiz',
  )
  return response.data.data
}

// -----------------------------------------------------------------------------
// spendHorseshoe — 편자를 소비하여 콘텐츠 잠금 해제
// -----------------------------------------------------------------------------
// params.contentType = 열려는 콘텐츠 종류 (예: 'TOP_1')
// params.raceId      = 경주 ID (선택). 경주별 콘텐츠라면 필요합니다.
export const spendHorseshoe = async (params: {
  contentType: ContentType
  raceId?: number
}): Promise<SpendResponse> => {
  // POST /api/v1/wallet/spend → 편자를 차감하고 잠금 해제를 처리합니다.
  const response = await axiosInstance.post<ApiResponse<SpendResponse>>(
    '/wallet/spend',
    params, // request body로 보냅니다.
  )
  return response.data.data
}

// -----------------------------------------------------------------------------
// fetchTransactions — 편자 거래 내역 조회 (페이지네이션)
// -----------------------------------------------------------------------------
// page = 페이지 번호 (0부터 시작). 스크롤을 내릴수록 다음 페이지를 요청합니다.
export const fetchTransactions = async (page: number): Promise<PageResponse<Transaction>> => {
  // GET /api/v1/wallet/transactions?page=0 → 거래 내역을 페이지 단위로 가져옵니다.
  const response = await axiosInstance.get<ApiResponse<PageResponse<Transaction>>>(
    '/wallet/transactions',
    { params: { page } },
  )
  return response.data.data
}
