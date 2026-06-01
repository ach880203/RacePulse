import { AxiosError } from 'axios'
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import axiosInstance from '../../api/axiosInstance'
import Toast, { type ToastType } from '../../components/Toast'
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

type LocationState = {
  toast?: string
  toastType?: ToastType
}

function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  // 서버가 내려준 한글 메시지를 우선 사용해 사용자가 실패 이유를 바로 이해할 수 있게 합니다.
  if (error instanceof AxiosError) {
    const responseData = error.response?.data as Partial<ApiResponse<unknown>> | undefined
    return responseData?.message ?? fallbackMessage
  }

  return fallbackMessage
}

function LoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const locationState = location.state as LocationState | null
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(() => (
    locationState?.toast
      ? { message: locationState.toast, type: locationState.toastType ?? 'success' }
      : null
  ))

  useEffect(() => {
    // 다른 화면에서 넘어온 안내 문구를 Toast로 보여주고, 새로고침 때 반복되지 않도록 현재 기록을 정리합니다.
    if (!locationState?.toast) return
    navigate(location.pathname, { replace: true, state: null })
  }, [location.pathname, locationState, navigate])

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')
    setIsSubmitting(true)

    try {
      // 이메일 로그인 API를 호출하고, 성공하면 Access Token을 공통 저장소에 저장해 PrivateRoute가 즉시 반응하게 합니다.
      const response = await axiosInstance.post<ApiResponse<AuthResponse>>('/auth/login', {
        email,
        password,
        rememberMe: false,
      })
      saveLoginToken(response.data.data.accessToken)
      navigate('/')
    } catch (error) {
      // 인증 실패는 입력값 아래에 바로 보여줘 사용자가 이메일과 비밀번호를 다시 확인할 수 있게 합니다.
      setErrorMessage(getApiErrorMessage(error, '이메일 또는 비밀번호를 확인해 주세요.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKakaoLogin = () => {
    // 카카오 로그인은 브라우저가 Spring Boot 엔드포인트로 이동해야 최종 카카오 페이지 리다이렉트가 정상 동작합니다.
    window.location.href = axiosInstance.getUri({ url: '/auth/kakao' })
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-brand-navy-950 px-4 py-10 font-body text-white">
      {toast && (
        <div className="fixed right-4 top-4 z-50">
          <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
        </div>
      )}

      <section className="w-full max-w-md rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 shadow-2xl shadow-black/30 lg:p-8">
        <div className="text-center">
          <Link to="/" className="font-heading text-4xl text-brand-gold-400">
            레이스펄스
          </Link>
          <h1 className="mt-6 text-2xl font-semibold text-white">경마를 데이터로 분석하다</h1>
          <p className="mt-2 text-sm text-white/60">AI 기반 경주 예측 플랫폼</p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm text-white/70">이메일</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white outline-none transition-colors focus:border-brand-gold-400"
              autoComplete="email"
              required
            />
          </label>

          <label className="block">
            <span className="text-sm text-white/70">비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white outline-none transition-colors focus:border-brand-gold-400"
              autoComplete="current-password"
              required
            />
          </label>

          {errorMessage && <p className="text-sm text-red-400">{errorMessage}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-brand-gold-400 px-6 py-3 text-sm font-semibold text-brand-navy-950 transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          >
            {isSubmitting ? '로그인 중...' : '로그인'}
          </button>
        </form>

        <div className="my-6 flex items-center gap-3 text-sm text-white/45">
          <span className="h-px flex-1 bg-white/10" />
          <span>또는</span>
          <span className="h-px flex-1 bg-white/10" />
        </div>

        <button
          type="button"
          onClick={handleKakaoLogin}
          disabled={isSubmitting}
          className="w-full rounded-full bg-[#FEE500] px-6 py-3 text-sm font-semibold text-[#191919] transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
        >
          카카오로 로그인
        </button>

        <p className="mt-6 text-center text-sm text-white/60">
          회원이 아니신가요?{' '}
          <Link to="/register" className="text-brand-gold-400 hover:underline">
            회원가입
          </Link>
        </p>
      </section>
    </main>
  )
}

export default LoginPage
