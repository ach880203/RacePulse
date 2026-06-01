// =============================================================================
// TrainerDetailPage.tsx — 조교사 상세 페이지
// 라우트: /trainers/:trainerId
// =============================================================================

import { Link, useParams } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import { useTrainer } from '../../hooks/usePersons'

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

function TrainerDetailPage() {
  const { trainerId } = useParams<{ trainerId: string }>()
  const id = trainerId ? Number(trainerId) : undefined

  const { data: trainer, isLoading, isError } = useTrainer(id)

  if (isLoading) {
    return (
      <Layout>
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="h-8 w-48 rounded-full bg-white/10" />
          <div className="h-48 rounded-3xl bg-white/5" />
        </div>
      </Layout>
    )
  }

  if (isError || !trainer) {
    return (
      <Layout>
        <div className="flex flex-col gap-6">
          <nav className="flex items-center gap-2 text-sm text-white/45">
            <Link to="/races" className="hover:text-white/70">홈</Link>
            <span>/</span>
            <span className="text-white/70">조교사 #{trainerId}</span>
          </nav>
          <div className="rounded-3xl border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
            <p className="text-base text-white/60">조교사 정보를 불러오지 못했습니다.</p>
          </div>
        </div>
      </Layout>
    )
  }

  const winTotalPct   = trainer.winRateTotal  != null ? (trainer.winRateTotal  * 100).toFixed(1) : null
  const winRecentPct  = trainer.winRateRecent != null ? (trainer.winRateRecent * 100).toFixed(1) : null

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">홈</Link>
          <span>/</span>
          <span className="text-white/70">조교사 {trainer.name}</span>
        </nav>

        {/* 조교사 헤더 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">
                {MEET_LABELS[trainer.meetCode] ?? trainer.meetCode}
              </p>
              <h1 className="mt-2 font-heading text-4xl text-white">{trainer.name}</h1>
              {trainer.engName && (
                <p className="mt-1 text-lg text-white/50">{trainer.engName}</p>
              )}
              <span
                className={[
                  'mt-3 inline-block rounded-full border px-3 py-1 text-xs font-medium',
                  trainer.isActive
                    ? 'border-brand-gold-400/35 bg-brand-gold-400/10 text-brand-gold-400'
                    : 'border-white/15 bg-white/5 text-white/40',
                ].join(' ')}
              >
                {trainer.isActive ? '현역' : '은퇴'}
              </span>
            </div>
          </div>
        </section>

        {/* 기본 정보 */}
        <section className="space-y-3">
          <h2 className="font-heading text-2xl text-white">기본 정보</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: '소속',       value: MEET_LABELS[trainer.meetCode] ?? trainer.meetCode },
              { label: '면허번호',   value: trainer.licenseNo ?? '-' },
              { label: '데뷔연도',   value: trainer.debutYear ? `${trainer.debutYear}년` : '-' },
              { label: '소속 구분',  value: trainer.affiliation ?? '-' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs text-white/45">{label}</p>
                <p className="mt-2 text-sm font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 성적 요약 */}
        <section className="space-y-3">
          <h2 className="font-heading text-2xl text-white">성적 요약</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
              <p className="text-xs text-white/45">통산 승률</p>
              <p className="mt-2 font-heading text-3xl text-brand-gold-400">
                {winTotalPct != null ? `${winTotalPct}%` : '-'}
              </p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
              <p className="text-xs text-white/45">최근 승률</p>
              <p className="mt-2 font-heading text-3xl text-white">
                {winRecentPct != null ? `${winRecentPct}%` : '-'}
              </p>
            </div>
          </div>
        </section>

        {/* 관리 중인 경주마 목록 — TODO */}
        <section className="rounded-[2rem] border border-dashed border-white/15 bg-white/4 px-6 py-10 text-center">
          <p className="text-white/50">관리 중인 경주마 목록</p>
          <p className="mt-2 text-xs text-white/30">추후 연동 예정입니다.</p>
        </section>
      </div>
    </Layout>
  )
}

export default TrainerDetailPage
