// =============================================================================
// axiosInstance.ts — Axios 기본 설정 및 JWT 인터셉터
// =============================================================================
// axios란?
//   브라우저에서 서버(Spring Boot)로 HTTP 요청을 보내는 라이브러리입니다.
//   fetch보다 설정이 편리하고 인터셉터 기능을 제공합니다.
//
// 인터셉터(Interceptor)란?
//   "모든 요청/응답을 중간에서 가로채 공통 처리를 추가하는 관문"입니다.
//   요청 인터셉터 = 요청을 보내기 전에 JWT 토큰을 자동으로 헤더에 붙입니다.
//   응답 인터셉터 = 응답이 돌아올 때 401(인증 실패)이면 토큰 재발급을 시도합니다.
// =============================================================================

// axios = HTTP 요청을 보내는 라이브러리입니다.
import axios from 'axios'

// Spring Boot 서버 주소
// 개발 환경: localhost:8080, 운영 환경: 실제 도메인으로 변경합니다.
const BASE_URL = 'http://localhost:8080/api/v1'

// Access Token을 localStorage에 저장할 때 사용하는 키 이름입니다.
// 한 곳에서 관리하면 이름을 바꿀 때 실수를 방지합니다.
const ACCESS_TOKEN_KEY = 'access_token'

// -----------------------------------------------------------------------------
// Access Token 유틸리티
// -----------------------------------------------------------------------------

/** localStorage에서 JWT Access Token을 가져옵니다. */
export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY)
}

/** JWT Access Token을 localStorage에 저장합니다. */
export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token)
}

/** localStorage에서 JWT Access Token을 삭제합니다. (로그아웃 시) */
export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
}

// -----------------------------------------------------------------------------
// Axios 인스턴스 생성
// -----------------------------------------------------------------------------

// axiosInstance = 기본 설정이 담긴 axios 객체입니다.
// 모든 API 호출 파일에서 이 인스턴스를 사용합니다.
const axiosInstance = axios.create({
  // baseURL = 이 뒤에 붙는 경로로 모든 요청이 전송됩니다.
  // 예: axiosInstance.get('/races') → http://localhost:8080/api/v1/races
  baseURL: BASE_URL,

  // 타임아웃: 10초 이내에 응답이 없으면 오류 처리합니다.
  timeout: 10_000,

  // withCredentials = HttpOnly 쿠키(Refresh Token)를 자동으로 요청에 포함합니다.
  // CORS 환경에서 쿠키를 주고받으려면 반드시 true여야 합니다.
  withCredentials: true,

  headers: {
    'Content-Type': 'application/json',
  },
})

// -----------------------------------------------------------------------------
// 요청 인터셉터 — JWT Access Token 자동 첨부
// -----------------------------------------------------------------------------
// 모든 API 요청을 보내기 전에 이 함수가 먼저 실행됩니다.
// localStorage에서 Access Token을 꺼내 Authorization 헤더에 붙여줍니다.
axiosInstance.interceptors.request.use(
  (config) => {
    const token = getAccessToken()
    if (token) {
      // Bearer = JWT 토큰 앞에 붙이는 표준 접두사입니다.
      // 서버가 "Bearer 토큰" 형식으로 받아서 처리합니다.
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// -----------------------------------------------------------------------------
// 응답 인터셉터 — 401 시 Refresh Token으로 Access Token 재발급
// -----------------------------------------------------------------------------
// 모든 API 응답이 돌아올 때 이 함수가 실행됩니다.
// 401(인증 만료) 응답이 오면 Refresh Token으로 새 Access Token을 발급받고
// 실패했던 요청을 다시 자동으로 보냅니다.

// 토큰 재발급이 진행 중인지 추적하는 플래그입니다.
// 여러 요청이 동시에 401을 받았을 때 재발급을 딱 한 번만 시도합니다.
let isRefreshing = false

// 토큰 재발급을 기다리는 요청들을 줄 세워두는 대기열입니다.
// 재발급이 완료되면 한꺼번에 다시 시도합니다.
type RefreshCallback = (token: string) => void
let waitingQueue: RefreshCallback[] = []

function processQueue(newToken: string): void {
  waitingQueue.forEach((cb) => cb(newToken))
  waitingQueue = []
}

axiosInstance.interceptors.response.use(
  // 성공 응답은 그대로 반환합니다.
  (response) => response,

  // 오류 응답 처리
  async (error) => {
    const originalRequest = error.config

    // 401(인증 실패) 이고, 이미 재시도한 요청이 아닐 때만 토큰 재발급을 시도합니다.
    // _retry 플래그는 무한 루프(401 → 재발급 → 또 401 → ...)를 방지합니다.
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // 이미 다른 요청이 재발급 중이면 대기열에 추가합니다.
      if (isRefreshing) {
        return new Promise((resolve) => {
          waitingQueue.push((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            resolve(axiosInstance(originalRequest))
          })
        })
      }

      isRefreshing = true

      try {
        // POST /auth/refresh → HttpOnly 쿠키의 Refresh Token을 자동으로 사용합니다.
        const response = await axiosInstance.post('/auth/refresh')
        const newAccessToken: string = response.data.data.accessToken

        // 새 토큰 저장 후 대기 중인 요청들에게도 전달합니다.
        setAccessToken(newAccessToken)
        processQueue(newAccessToken)

        // 실패했던 원래 요청을 새 토큰으로 다시 시도합니다.
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return axiosInstance(originalRequest)

      } catch {
        // 재발급도 실패하면 로그인 페이지로 이동합니다.
        clearAccessToken()
        window.location.href = '/login'
        return Promise.reject(error)
      } finally {
        isRefreshing = false
      }
    }

    return Promise.reject(error)
  },
)

export default axiosInstance
