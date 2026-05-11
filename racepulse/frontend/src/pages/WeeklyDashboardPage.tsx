// =============================================================================
// WeeklyDashboardPage.tsx — 주간 분석 페이지
// 라우트: /dashboard/weekly
// =============================================================================

import { Link } from 'react-router-dom'
import Layout from '../components/layout/Layout'
import CircularGauge from '../components/CircularGauge'
import { useAccuracyStats } from '../hooks/useDashboard'
import { useUpcomingRaces } from '../hooks/useRaces'

function WeeklyDashboardPage() {
  const { data: stats, isLoading } = useAccuracyStats()
  // 이번 주 예정 경주 수 계산에 사용합니다.
  const { data: upcomingRaces } = useUpcomingRaces()

  // 이번 주 요약 (데모 — TODO: 주간 전용 API 연동)
  const thisWeek = {
    totalRaces:      upcomingRaces?.length ?? 0,
    totalPredictions: 0,  // TODO: [Phase 3] 실제 예측 수 연동
  }

  return (
    <Layout>
      <div className="flex flex-col gap-10">
        {/* 헤더 */}
        <section className="space-y-3">
          <nav className="flex items-center gap-2 text-sm text-white/45">
            <Link to="/dashboard" className="hover:text-white/70">대시보드</Link>
            <span>/</span>
            <span className="text-white/70">주간 분석</span>
          </nav>
          <p className="text-sm tracking-[0.2em] text-brand-gold-400">WEEKLY REPORT</p>
          <h1 className="font-heading text-4xl text-white">이번 주 분석</h1>
        </section>

        {/* 이번 주 요약 카드 */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            {
              label: '이번 주 예정 경주',
              value: `${thisWeek.totalRaces}경주`,
              sub:   '오늘 기준',
            },
            {
              label: '이번 주 예측 수',
              value: thisWeek.totalPredictions > 0
                ? `${thisWeek.totalPredictions}건`
                : '준비 중',
              sub: 'ML 모델 예측',
            },
            {
              label: '누적 Top-1 정확도',
              value: stats ? `${stats.top1Accuracy}%` : '...',
              sub:   '전체 기간',
            },
            {
              label: '누적 Top-3 정확도',
              value: stats ? `${stats.top3Accuracy}%` : '...',
              sub:   '전체 기간',
            },
          ].map(({ label, value, sub }) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-5">
              <p className="text-xs text-white/45">{label}</p>
              <p className="mt-3 font-heading text-3xl text-white">{value}</p>
              <p className="mt-1 text-xs text-white/35">{sub}</p>
            </div>
          ))}
        </section>

        {/* 이번 주 예측 정확도 게이지 */}
        {stats && (
          <section className="space-y-4">
            <h2 className="font-heading text-2xl text-white">
              최근 30일 정확도
            </h2>
            <div className="flex flex-wrap justify-around gap-8 rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-8">
              <CircularGauge
                value={stats.last30DaysTop1}
                label="최근 30일 Top-1"
                size={160}
                strokeWidth={12}
              />
              <CircularGauge
                value={stats.top3Accuracy}
                label="누적 Top-3"
                size={160}
                strokeWidth={12}
              />
            </div>
          </section>
        )}

        {/* 로딩 중 */}
        {isLoading && (
          <div className="flex justify-around animate-pulse">
            <div className="h-40 w-40 rounded-full bg-white/10" />
            <div className="h-40 w-40 rounded-full bg-white/10" />
          </div>
        )}

        {/* 주목할 경주 하이라이트 */}
        <section className="space-y-4">
          <h2 className="font-heading text-2xl text-white">이번 주 예정 경주</h2>
          {upcomingRaces && upcomingRaces.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {upcomingRaces.slice(0, 4).map((race) => (
                <Link
                  key={race.id}
                  to={`/races/${race.id}`}
                  className="rounded-2xl border border-white/10 bg-white/5 p-4 transition-colors hover:border-brand-gold-400/30"
                >
                  <p className="text-xs text-white/45">{race.meetCode} · {race.rcDate}</p>
                  <p className="mt-1 font-semibold text-white">{race.raceName}</p>
                  <p className="mt-1 text-xs text-white/40">
                    {race.distance}m · 출발 {race.startTime ?? '미정'}
                  </p>
                </Link>
              ))}
            </div>
          ) : (
            <div className="rounded-[2rem] border border-dashed border-white/15 bg-white/4 px-6 py-10 text-center">
              <p className="text-white/50">이번 주 예정 경주가 없습니다.</p>
            </div>
          )}
        </section>

        {/* 다음 주 예고 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6">
          <h2 className="font-heading text-xl text-white">다음 주 예고</h2>
          <p className="mt-2 text-sm text-white/50">
            {/* TODO: [Phase 3] 다음 주 경주 예정 수 API 연동 */}
            다음 주 경주 일정은 목요일 출전표 수집 후 확정됩니다.
          </p>
          <Link
            to="/races"
            className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline"
          >
            경주 목록 전체 보기 →
          </Link>
        </section>
      </div>
    </Layout>
  )
}

export default WeeklyDashboardPage
