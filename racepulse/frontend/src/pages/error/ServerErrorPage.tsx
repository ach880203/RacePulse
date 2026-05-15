import { useNavigate } from 'react-router-dom'
import Layout from '../../components/layout/Layout'

// 500 서버 오류 응답을 받았을 때 보여주는 페이지입니다.
// 스택트레이스 등 민감한 정보는 절대 노출하지 않습니다.
export default function ServerErrorPage() {
  const navigate = useNavigate()

  return (
    <Layout>
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">

        <p className="font-mono text-8xl font-bold tracking-widest text-brand-gold-400">
          500
        </p>

        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-3xl font-semibold text-white">
            서버 오류가 발생했습니다
          </h1>
          <p className="text-white/50">
            일시적인 문제가 발생했습니다. 잠시 후 다시 시도해주세요.
          </p>
        </div>

        <div className="h-px w-24 bg-brand-gold-500/40" />

        <div className="flex gap-3">
          <button
            onClick={() => navigate(0)}
            className="rounded bg-brand-gold-500 px-6 py-2.5 text-sm font-medium text-brand-navy-950 transition hover:bg-brand-gold-400"
          >
            새로고침
          </button>
          <button
            onClick={() => navigate('/')}
            className="rounded border border-white/20 px-6 py-2.5 text-sm font-medium text-white/70 transition hover:border-white/40 hover:text-white"
          >
            홈으로
          </button>
        </div>
      </div>
    </Layout>
  )
}
