import { AxiosError } from 'axios'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import axiosInstance from '../../api/axiosInstance'
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
  // 중복 이메일처럼 서버 검증에서만 알 수 있는 이유는 응답 메시지를 그대로 보여주는 편이 가장 정확합니다.
  if (error instanceof AxiosError) {
    const responseData = error.response?.data as Partial<ApiResponse<unknown>> | undefined
    return responseData?.message ?? fallbackMessage
  }

  return fallbackMessage
}

function RegisterPage() {
  const navigate = useNavigate()
  const [nickname, setNickname] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirm, setPasswordConfirm] = useState('')
  const [termsAgreed, setTermsAgreed] = useState(false)
  const [errorMessage, setErrorMessage] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setErrorMessage('')

    if (password !== passwordConfirm) {
      setErrorMessage('비밀번호와 비밀번호 확인이 일치하지 않습니다.')
      return
    }

    if (!termsAgreed) {
      setErrorMessage('이용약관 동의는 필수입니다.')
      return
    }

    setIsSubmitting(true)

    try {
      // 회원가입 API는 약관 동의 값을 함께 요구하므로 필수 동의 여부를 서버에도 전달합니다.
      await axiosInstance.post<ApiResponse<AuthResponse>>('/auth/register', {
        nickname,
        email,
        password,
        termsAgreed,
        marketingAgreed: false,
      })
      navigate('/login', {
        state: {
          toast: '회원가입이 완료되었습니다',
          toastType: 'success',
        },
      })
    } catch (error) {
      // 중복 이메일과 입력 검증 실패는 같은 위치에 표시해 가입 양식을 다시 고치기 쉽게 합니다.
      setErrorMessage(getApiErrorMessage(error, '회원가입에 실패했습니다. 입력값을 확인해 주세요.'))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-brand-navy-950 px-4 py-10 font-body text-white">
      <section className="w-full max-w-md rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 shadow-2xl shadow-black/30 lg:p-8">
        <div className="text-center">
          <Link to="/" className="font-heading text-4xl text-brand-gold-400">
            레이스펄스
          </Link>
          <h1 className="mt-6 text-2xl font-semibold text-white">회원가입</h1>
          <p className="mt-2 text-sm text-white/60">AI 기반 경주 예측을 시작해 보세요</p>
        </div>

        <form className="mt-8 space-y-4" onSubmit={handleSubmit}>
          <label className="block">
            <span className="text-sm text-white/70">닉네임</span>
            <input
              type="text"
              value={nickname}
              onChange={(event) => setNickname(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white outline-none transition-colors focus:border-brand-gold-400"
              autoComplete="nickname"
              minLength={2}
              required
            />
          </label>

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
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          <label className="block">
            <span className="text-sm text-white/70">비밀번호 확인</span>
            <input
              type="password"
              value={passwordConfirm}
              onChange={(event) => setPasswordConfirm(event.target.value)}
              className="mt-2 w-full rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white outline-none transition-colors focus:border-brand-gold-400"
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          <label className="flex items-start gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-sm text-white/70">
            <input
              type="checkbox"
              checked={termsAgreed}
              onChange={(event) => setTermsAgreed(event.target.checked)}
              className="mt-1 h-4 w-4 rounded border-white/20 accent-brand-gold-400"
              required
            />
            <span>이용약관과 개인정보 처리방침에 동의합니다.</span>
          </label>

          {errorMessage && <p className="text-sm text-red-400">{errorMessage}</p>}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-full bg-brand-gold-400 px-6 py-3 text-sm font-semibold text-brand-navy-950 transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
          >
            {isSubmitting ? '가입 중...' : '회원가입'}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-white/60">
          이미 회원이신가요?{' '}
          <Link to="/login" className="text-brand-gold-400 hover:underline">
            로그인
          </Link>
        </p>
      </section>
    </main>
  )
}

export default RegisterPage
