import { Link } from 'react-router-dom'
import Layout from '../../components/layout/Layout'

// 존재하지 않는 URL로 접근했을 때 보여주는 404 페이지입니다.
// App.tsx 의 catch-all route ( path="*" ) 에서 렌더링됩니다.
export default function NotFoundPage() {
  return (
    <Layout>
      <div className="flex flex-1 flex-col items-center justify-center gap-6 py-24 text-center">

        {/* 에러 코드 — JetBrains Mono로 숫자 데이터 느낌을 강조합니다 */}
        <p className="font-mono text-8xl font-bold tracking-widest text-brand-gold-400">
          404
        </p>

        <div className="flex flex-col gap-2">
          <h1 className="font-heading text-3xl font-semibold text-white">
            페이지를 찾을 수 없습니다
          </h1>
          <p className="text-white/50">
            요청하신 페이지가 존재하지 않거나 이동되었습니다.
          </p>
        </div>

        {/* 구분선 */}
        <div className="h-px w-24 bg-brand-gold-500/40" />

        <Link
          to="/"
          className="rounded border border-brand-gold-500/60 px-6 py-2.5 text-sm font-medium text-brand-gold-400 transition hover:bg-brand-gold-500/10"
        >
          홈으로 돌아가기
        </Link>
      </div>
    </Layout>
  )
}
