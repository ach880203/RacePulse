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
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/4 px-6 py-16 text-center">
            <p className="text-base text-white/60">조교사 정보를 불러오지 못했습니다.</p>
            <p className="mt-2 text-sm text-white/35">
              {/* TODO: [Phase 2] 조교사 상세 API 연동 후 실제 데이터 표시 */}
              조교사 상세 API는 Phase 2에서 연동될 예정입니다.
            </p>
          </div>
        </div>
      </Layout>
    )
  }

  const winPct = trainer.winRate != null ? (trainer.winRate * 100).toFixed(1) : null

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
          <p className="text-sm tracking-[0.2em] text-brand-gold-400">TRAINER</p>
          <h1 className="mt-2 font-heading text-4xl text-white">{trainer.name}</h1>
          <p className="mt-1 text-sm text-white/50">
            {MEET_LABELS[trainer.meetCode] ?? trainer.meetCode}
          </p>
        </section>

        {/* 성적 요약 */}
        <section className="grid gap-4 sm:grid-cols-4">
          {[
            { label: '총 출전',      value: trainer.totalRaces != null ? `${trainer.totalRaces}회` : '-' },
            { label: '총 우승',      value: trainer.totalWins != null ? `${trainer.totalWins}회` : '-' },
            { label: '승률',         value: winPct != null ? `${winPct}%` : '-' },
            { label: '관리 중인 말', value: trainer.horseCount != null ? `${trainer.horseCount}두` : '-' },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
              <p className="text-xs text-white/45">{label}</p>
              <p className="mt-2 font-heading text-3xl text-white">{value}</p>
            </div>
          ))}
        </section>

        {/* 관리 중인 경주마 목록 — TODO */}
        <section className="rounded-[2rem] border border-dashed border-white/15 bg-white/4 px-6 py-10 text-center">
          <p className="text-white/50">관리 중인 경주마 목록</p>
          <p className="mt-2 text-xs text-white/30">
            {/* TODO: [Phase 2] 조교사별 경주마 목록 API 연동 후 구현 */}
            조교사별 경주마 목록 API 연동 후 표시됩니다.
          </p>
        </section>
      </div>
    </Layout>
  )
}

export default TrainerDetailPage
