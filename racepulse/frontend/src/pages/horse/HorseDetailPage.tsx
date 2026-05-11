// =============================================================================
// HorseDetailPage.tsx — 경주마 상세 페이지
// 라우트: /horses/:horseId
// =============================================================================

import { Link, useParams } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import SparklineChart from '../../components/SparklineChart'
import { useHorse } from '../../hooks/useHorses'

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

function HorseDetailPage() {
  const { horseId } = useParams<{ horseId: string }>()
  const id = horseId ? Number(horseId) : undefined

  const { data: horse, isLoading, isError } = useHorse(id)

  if (isLoading) {
    return (
      <Layout>
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="h-8 w-48 rounded-full bg-white/10" />
          <div className="h-48 rounded-3xl bg-white/5" />
          <div className="h-64 rounded-3xl bg-white/5" />
        </div>
      </Layout>
    )
  }

  if (isError || !horse) {
    return (
      <Layout>
        <div className="rounded-3xl border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
          <p className="text-white/60">경주마 정보를 불러오지 못했습니다.</p>
          <Link to="/races" className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
            경주 목록으로
          </Link>
        </div>
      </Layout>
    )
  }

  // 레이팅 데이터를 스파크라인 차트 형식으로 변환합니다.
  // 실제 경주 이력이 없으므로 레이팅 값으로 트렌드를 표현합니다.
  // TODO: [Phase 2] 실제 경주 이력 API 연동 후 교체
  const sparkData = [horse.rating1, horse.rating2, horse.rating3, horse.rating4]
    .filter((r): r is number => r != null)
    .map((r) => ({ order: Math.round(r) }))

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 브레드크럼 */}
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">홈</Link>
          <span>/</span>
          <span className="text-white/70">{horse.name}</span>
        </nav>

        {/* 경주마 헤더 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">
                {MEET_LABELS[horse.meetCode] ?? horse.meetCode}
              </p>
              <h1 className="mt-2 font-heading text-4xl text-white">{horse.name}</h1>
              {horse.engName && (
                <p className="mt-1 text-lg text-white/50">{horse.engName}</p>
              )}
              {/* 활동 상태 */}
              <span
                className={[
                  'mt-3 inline-block rounded-full border px-3 py-1 text-xs font-medium',
                  horse.isActive
                    ? 'border-brand-gold-400/35 bg-brand-gold-400/10 text-brand-gold-400'
                    : 'border-white/15 bg-white/5 text-white/40',
                ].join(' ')}
              >
                {horse.isActive ? '현역' : '은퇴'}
              </span>
            </div>

            {/* 레이팅 스파크라인 */}
            {sparkData.length > 0 && (
              <div className="w-48">
                <p className="mb-2 text-xs text-white/45">레이팅 추이</p>
                <SparklineChart data={sparkData} height={56} />
              </div>
            )}
          </div>
        </section>

        {/* 기본 정보 */}
        <section className="space-y-3">
          <h2 className="font-heading text-2xl text-white">기본 정보</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: '성별',     value: horse.sex ?? '-' },
              { label: '출생연도', value: horse.birthYear ? `${horse.birthYear}년생` : '-' },
              { label: '털색',     value: horse.color ?? '-' },
              { label: '원산지',   value: horse.origin ?? '-' },
              { label: '아비',     value: horse.fatherName ?? '-' },
              { label: '어미',     value: horse.motherName ?? '-' },
              { label: '마주',     value: horse.owner ?? '-' },
              { label: '소속',     value: MEET_LABELS[horse.meetCode] ?? horse.meetCode },
            ].map(({ label, value }) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <p className="text-xs text-white/45">{label}</p>
                <p className="mt-2 text-sm font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </section>

        {/* 레이팅 정보 */}
        {(horse.rating1 ?? horse.rating2 ?? horse.rating3 ?? horse.rating4) && (
          <section className="space-y-3">
            <h2 className="font-heading text-2xl text-white">레이팅</h2>
            <div className="grid gap-4 sm:grid-cols-4">
              {[
                { label: '레이팅 1', value: horse.rating1 },
                { label: '레이팅 2', value: horse.rating2 },
                { label: '레이팅 3', value: horse.rating3 },
                { label: '레이팅 4', value: horse.rating4 },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4 text-center">
                  <p className="text-xs text-white/45">{label}</p>
                  <p className="mt-2 font-heading text-3xl text-brand-gold-400">
                    {value != null ? Number(value).toFixed(1) : '-'}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 경주 이력 — TODO */}
        <section className="rounded-[2rem] border border-dashed border-white/15 bg-white/4 px-6 py-10 text-center">
          <p className="text-white/50">경주 이력</p>
          <p className="mt-2 text-xs text-white/30">
            {/* TODO: [Phase 2] 경주 이력 API 연동 후 구현 */}
            경주 이력 API 연동 후 표시됩니다.
          </p>
        </section>
      </div>
    </Layout>
  )
}

export default HorseDetailPage
