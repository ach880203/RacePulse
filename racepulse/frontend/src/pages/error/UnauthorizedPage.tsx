import { Link, useNavigate } from 'react-router-dom'
import Layout from '../../components/layout/Layout'

// 401(미인증) 또는 403(권한 없음) 응답을 받았을 때 보여주는 페이지입니다.
// props 로 variant를 받아 두 케이스를 하나의 컴포넌트로 처리합니다.
type Props = {
  variant?: 'unauthorized' | 'forbidden'
}

export default function UnauthorizedPage({ variant = 'unauthorized' }: Props) {
  const navigate = useNavigate()

  const isUnauthorized = variant === 'unauthorized'

  const code = isUnauthorized ? '401' : '403'
  const title = isUnauthorized ? '로그인이 필요합니다' : '접근 권한이 없습니다'
  const description = isUnauthorized
    ? '이 페이지를 보려면 먼저 로그인해야 합니다.'
    : '이 페이지에 접근할 수 있는 권한이 없습니다.'

  return (
    <Layout>
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">

        <p className="font-mono text-8xl font-bold tracking-widest text-brand-gold-400">
          {code}
        </p>

        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-3xl font-semibold text-white">
            {title}
          </h1>
          <p className="text-white/50">{description}</p>
        </div>

        <div className="h-px w-24 bg-brand-gold-500/40" />

        <div className="flex gap-3">
          {isUnauthorized && (
            <Link
              to="/login"
              className="rounded bg-brand-gold-500 px-6 py-2.5 text-sm font-medium text-brand-navy-950 transition hover:bg-brand-gold-400"
            >
              로그인하기
            </Link>
          )}
          <button
            onClick={() => navigate(-1)}
            className="rounded border border-white/20 px-6 py-2.5 text-sm font-medium text-white/70 transition hover:border-white/40 hover:text-white"
          >
            이전 페이지
          </button>
        </div>
      </div>
    </Layout>
  )
}
