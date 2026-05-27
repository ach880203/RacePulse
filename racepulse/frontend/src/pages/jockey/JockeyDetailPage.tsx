// =============================================================================
// JockeyDetailPage.tsx — 기수 상세 페이지
// 라우트: /jockeys/:jockeyId
// =============================================================================

import { Link, useParams } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import { useJockey } from '../../hooks/usePersons'

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

function JockeyDetailPage() {
  const { jockeyId } = useParams<{ jockeyId: string }>()
  const id = jockeyId ? Number(jockeyId) : undefined

  const { data: jockey, isLoading, isError } = useJockey(id)

  if (isLoading) {
    return (
      <Layout>
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="h-8 w-48 rounded-full bg-white/10" />
          <div className="h-48 rounded-3xl bg-white/5" />
          <div className="h-32 rounded-3xl bg-white/5" />
        </div>
      </Layout>
    )
  }

  if (isError || !jockey) {
    return (
      <Layout>
        <div className="flex flex-col gap-6">
          <nav className="flex items-center gap-2 text-sm text-white/45">
            <Link to="/jockeys" className="hover:text-white/70">기수 목록</Link>
            <span>/</span>
            <span className="text-white/70">기수 #{jockeyId}</span>
          </nav>
          <div className="rounded-3xl border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
            <p className="text-base text-white/60">기수 정보를 불러오지 못했습니다.</p>
            <Link to="/jockeys" className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
              기수 목록으로
            </Link>
          </div>
        </div>
      </Layout>
    )
  }

  const winPct    = jockey.winRateTotal   != null ? (jockey.winRateTotal   * 100).toFixed(1) : null
  const recentPct = jockey.winRateRecent  != null ? (jockey.winRateRecent  * 100).toFixed(1) : null
  const placePct  = jockey.placeRateTotal != null ? (jockey.placeRateTotal * 100).toFixed(1) : null

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/jockeys" className="hover:text-white/70">기수 목록</Link>
          <span>/</span>
          <span className="text-white/70">{jockey.name}</span>
        </nav>

        {/* 헤더 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">
                {MEET_LABELS[jockey.meetCode] ?? jockey.meetCode}
              </p>
              <h1 className="mt-2 font-heading text-4xl text-white">{jockey.name}</h1>
              {jockey.engName && (
                <p className="mt-1 text-lg text-white/50">{jockey.engName}</p>
              )}
              <span
                className={[
                  'mt-3 inline-block rounded-full border px-3 py-1 text-xs font-medium',
                  jockey.isActive
                    ? 'border-brand-gold-400/35 bg-brand-gold-400/10 text-brand-gold-400'
                    : 'border-white/15 bg-white/5 text-white/40',
                ].join(' ')}
              >
                {jockey.isActive ? '현역' : '은퇴'}
              </span>
            </div>
          </div>
        </section>

        {/* 성적 요약 */}
        <section className="grid gap-4 sm:grid-cols-3">
          {[
            { label: '통산 승률',  value: winPct    != null ? `${winPct}%`    : '-', highlight: false },
            { label: '최근 승률',  value: recentPct != null ? `${recentPct}%` : '-', highlight: true  },
            { label: '통산 연대율', value: placePct  != null ? `${placePct}%`  : '-', highlight: false },
          ].map(({ label, value, highlight }) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-5 text-center">
              <p className="text-xs text-white/45">{label}</p>
              <p className={[
                'mt-2 font-heading text-4xl',
                highlight ? 'text-brand-gold-400' : 'text-white',
              ].join(' ')}>
                {value}
              </p>
            </div>
          ))}
        </section>

        {/* 기본 정보 */}
        <section className="space-y-3">
          <h2 className="font-heading text-2xl text-white">기본 정보</h2>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: '소속 경마장', value: MEET_LABELS[jockey.meetCode] ?? jockey.meetCode },
              { label: '출생연도',    value: jockey.birthYear ? `${jockey.birthYear}년생` : '-' },
              { label: '데뷔연도',    value: jockey.debutYear ? `${jockey.debutYear}년` : '-' },
              { label: '면허번호',    value: jockey.licenseNo ?? '-' },
              { label: '소속',        value: jockey.affiliation ? (MEET_LABELS[jockey.affiliation] ?? jockey.affiliation) : '-' },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs text-white/45">{label}</p>
                <p className="mt-2 text-sm font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 경주 이력 — Phase 4+ 구현 예정 */}
        <section className="rounded-[2rem] border border-dashed border-white/15 bg-white/4 px-6 py-10 text-center">
          <p className="text-white/50">최근 출전 경주 이력</p>
          <p className="mt-2 text-xs text-white/30">경주 이력 API 연동 후 표시됩니다.</p>
        </section>
      </div>
    </Layout>
  )
}

export default JockeyDetailPage
