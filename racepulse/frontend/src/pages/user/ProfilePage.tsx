import { Link, useNavigate } from 'react-router-dom'

import Layout from '../../components/layout/Layout'
import { useFavorites, useLogout, useMe } from '../../hooks/useUser'

function ProfilePage() {
  const navigate = useNavigate()
  const meQuery = useMe()
  const favoritesQuery = useFavorites()
  const logoutMutation = useLogout()

  const handleLogout = () => {
    if (!window.confirm('로그아웃하시겠습니까?')) return
    logoutMutation.mutate(undefined, { onSuccess: () => navigate('/') })
  }

  return (
    <Layout>
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl text-white">마이페이지</h1>
        <section className="mt-6 rounded-lg border border-white/10 bg-white/[0.04] p-6">
          <p className="text-sm text-white/55">프로필</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{meQuery.data?.nickname ?? '사용자'}</h2>
          <p className="mt-1 text-white/65">{meQuery.data?.email}</p>
          <p className="mt-2 text-sm text-brand-gold-400">가입 방식 {meQuery.data?.authProvider ?? '-'}</p>
        </section>
        <section className="mt-5 grid gap-4 sm:grid-cols-2">
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <p className="text-sm text-white/55">활동 요약</p>
            <p className="mt-2 font-heading text-3xl text-brand-gold-400">{favoritesQuery.data?.length ?? 0}</p>
            <p className="text-white/65">즐겨찾기 항목</p>
          </div>
          <div className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
            <p className="text-sm text-white/55">최근 조회</p>
            <p className="mt-2 text-white/65">조회 이력은 다음 단계에서 연결됩니다.</p>
          </div>
        </section>
        <section className="mt-5 flex flex-wrap gap-3">
          <Link to="/settings" className="rounded-full bg-brand-gold-400 px-4 py-2 font-semibold text-brand-navy-950">알림 설정</Link>
          <Link to="/favorites" className="rounded-full bg-white/10 px-4 py-2 font-semibold text-white">즐겨찾기</Link>
          <button type="button" onClick={handleLogout} className="rounded-full border border-white/15 px-4 py-2 font-semibold text-white">로그아웃</button>
        </section>
      </main>
    </Layout>
  )
}

export default ProfilePage
