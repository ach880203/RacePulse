import { AxiosError } from 'axios'
import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import axiosInstance from '../../api/axiosInstance'
import { saveLoginToken } from '../../store/authStore'
import type { ApiResponse } from '../../types/race'

type AuthResponse = {
  accessToken: string
  tokenType: string
  expiresIn: number
  userId: string
  email: string
  nickname: string
  role: string
  tier: string
}

function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  // 카카오 콜백 실패는 로그인 화면 Toast로 전달해야 하므로 서버 메시지를 문자열로 정리합니다.
  if (error instanceof AxiosError) {
    const responseData = error.response?.data as Partial<ApiResponse<unknown>> | undefined
    return responseData?.message ?? fallbackMessage
  }

  return fallbackMessage
}

function KakaoCallbackPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const didRequestRef = useRef(false)

  useEffect(() => {
    const code = searchParams.get('code')

    const processKakaoLogin = async () => {
      if (!code) {
        navigate('/login', {
          replace: true,
          state: { toast: '카카오 인증 코드가 없습니다.', toastType: 'error' },
        })
        return
      }

      if (didRequestRef.current) return
      didRequestRef.current = true

      try {
        // 카카오가 전달한 code를 백엔드에 보내고, 성공 시 받은 Access Token을 앱 인증 상태에 반영합니다.
        const response = await axiosInstance.get<ApiResponse<AuthResponse>>('/auth/kakao/callback', {
          params: { code },
        })
        saveLoginToken(response.data.data.accessToken)
        navigate('/', { replace: true })
      } catch (error) {
        // OAuth 실패는 입력 화면이 따로 없으므로 로그인 화면으로 돌려보내고 Toast로 이유를 안내합니다.
        navigate('/login', {
          replace: true,
          state: {
            toast: getApiErrorMessage(error, '카카오 로그인에 실패했습니다.'),
            toastType: 'error',
          },
        })
      }
    }

    void processKakaoLogin()
  }, [navigate, searchParams])

  return (
    <main className="flex min-h-screen items-center justify-center bg-brand-navy-950 px-4 font-body text-white">
      <section className="flex w-full max-w-sm flex-col items-center rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-8 text-center shadow-2xl shadow-black/30">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-white/10 border-t-brand-gold-400" />
        <h1 className="mt-6 text-xl font-semibold text-white">카카오 로그인 처리 중...</h1>
        <p className="mt-2 text-sm text-white/60">잠시만 기다려 주세요</p>
      </section>
    </main>
  )
}

export default KakaoCallbackPage
