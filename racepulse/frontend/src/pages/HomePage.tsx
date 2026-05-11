// Link = 버튼처럼 보이는 요소를 눌렀을 때 앱 내부 경로로 이동시키는 라우터 링크입니다.
import { Link } from 'react-router-dom'

// Layout = Header와 Footer를 자동으로 감싸 주는 공통 레이아웃 컴포넌트입니다.
import Layout from '../components/layout/Layout'

// useUpcomingRaces = 오늘 예정된 경주를 서버에서 가져오는 React Query 훅입니다.
import { useUpcomingRaces } from '../hooks/useRaces'

// useRacecourses = 경마장 목록을 서버에서 가져오는 React Query 훅입니다.
import { useRacecourses } from '../hooks/useRacecourses'

// DataStatusBadge = 데이터 수집 상태를 색상 뱃지로 표시하는 컴포넌트입니다.
import DataStatusBadge from '../components/DataStatusBadge'

// Race 타입: TypeScript가 데이터 모양을 검증할 수 있게 해줍니다.
import type { Race } from '../types/race'

// =============================================================================
// 경마장 코드 → 한글 이름 변환 유틸리티
// =============================================================================
const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

// TODO: [Phase 2] 실제 정확도 데이터 연동 후 교체
const accuracyMetrics = [
  { label: 'Top-1 적중률', value: 42 },
  { label: 'Top-3 적중률', value: 68 },
]

// =============================================================================
// 로딩 스켈레톤 컴포넌트
// =============================================================================
// 스켈레톤 UI = 데이터가 오기 전에 카드 모양의 회색 플레이스홀더를 보여줍니다.
// "로딩 중..." 텍스트보다 시각적으로 자연스럽습니다.
function RaceCardSkeleton() {
  return (
    <div className="animate-pulse rounded-3xl border border-white/10 bg-white/5 p-5">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-2">
          <div className="h-3 w-24 rounded-full bg-white/10" />
          <div className="h-6 w-32 rounded-full bg-white/15" />
        </div>
        <div className="h-6 w-16 rounded-full bg-white/10" />
      </div>
      <div className="mt-6 flex items-center justify-between">
        <div className="h-3 w-16 rounded-full bg-white/10" />
        <div className="h-3 w-12 rounded-full bg-white/15" />
      </div>
    </div>
  )
}

// =============================================================================
// 경주 카드 컴포넌트
// =============================================================================
function RaceCard({ race }: { race: Race }) {
  return (
    <Link to={`/races/${race.id}`}>
      <article className="rounded-3xl border border-white/10 bg-white/5 p-5 shadow-lg shadow-black/10 transition-transform hover:-translate-y-1 hover:border-brand-gold-400/40">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-white/55">
              {MEET_LABELS[race.meetCode] ?? race.meetCode}
            </p>
            <h3 className="mt-2 font-heading text-2xl text-white">{race.raceName}</h3>
          </div>
          {/* 데이터 수집 상태 뱃지 — DataStatusBadge가 없으면 기본 뱃지 표시 */}
          {race.dataStatus
            ? <DataStatusBadge status={race.dataStatus} />
            : (
              <span className="rounded-full border border-brand-gold-400/35 bg-brand-gold-400/10 px-3 py-1 text-xs font-medium text-brand-gold-400">
                예정
              </span>
            )
          }
        </div>
        <div className="mt-6 flex items-center justify-between text-sm text-white/70">
          <span>출발 시간</span>
          <span className="font-semibold text-white">{race.startTime ?? '미정'}</span>
        </div>
      </article>
    </Link>
  )
}

// =============================================================================
// HomePage 컴포넌트
// =============================================================================
function HomePage() {
  // useUpcomingRaces = 오늘 예정된 경주를 서버에서 가져옵니다.
  // isLoading = API 요청 중인지, isError = 오류가 났는지, data = 응답 데이터입니다.
  const { data: upcomingRaces, isLoading: racesLoading, isError: racesError } = useUpcomingRaces()

  // useRacecourses = 경마장 수를 통계 카드에 표시하기 위해 사용합니다.
  const { data: racecourses } = useRacecourses()

  // 오늘 첫 경주 출발 시간 계산
  const firstRaceTime = upcomingRaces?.[0]?.startTime ?? '-'
  const totalRaces = upcomingRaces?.length ?? 0

  return (
    <Layout>
      <div className="flex flex-col gap-12">
        {/* --------------------------------------------------------------------
            히어로 섹션
            -------------------------------------------------------------------- */}
        <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-gradient-to-br from-brand-navy-900 via-brand-navy-950 to-brand-navy-800 px-6 py-10 shadow-2xl sm:px-8 sm:py-14 lg:px-12">
          <div className="absolute inset-y-6 right-[-4rem] hidden w-48 rounded-full bg-brand-gold-400/10 blur-3xl sm:block" />
          <div className="relative grid gap-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(18rem,0.8fr)] lg:items-center">
            <div className="flex flex-col gap-5">
              <span className="w-fit rounded-full border border-brand-gold-400/30 bg-brand-gold-400/10 px-4 py-2 text-xs font-semibold tracking-[0.22em] text-brand-gold-400">
                AI RACE INTELLIGENCE
              </span>
              <div className="space-y-3">
                <h1 className="font-heading text-4xl leading-tight text-white sm:text-5xl">
                  경마를 데이터로
                  <br />
                  분석하다
                </h1>
                <p className="max-w-2xl text-base leading-7 text-white/72 sm:text-lg">
                  AI 기반 경주 예측 플랫폼으로 오늘의 경주 흐름과 핵심 지표를 더 빠르게 읽어보세요.
                </p>
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Link
                  to="/races"
                  className="rounded-full bg-brand-gold-400 px-6 py-3 text-sm font-semibold text-brand-navy-950 transition-transform hover:-translate-y-0.5"
                >
                  경주 목록 보기
                </Link>
              </div>
            </div>

            {/* 실시간 통계 카드 */}
            <div className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-3xl border border-white/10 bg-white/6 p-5">
                <p className="text-sm text-white/55">오늘 예정 경주</p>
                <p className="mt-3 font-heading text-4xl text-brand-gold-400">
                  {racesLoading ? '…' : totalRaces}
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/6 p-5">
                <p className="text-sm text-white/55">등록 경마장</p>
                <p className="mt-3 font-heading text-4xl text-white">
                  {racecourses?.length ?? 3}
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/6 p-5">
                <p className="text-sm text-white/55">오늘 첫 출발</p>
                <p className="mt-3 font-heading text-4xl text-white">
                  {racesLoading ? '…' : firstRaceTime}
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* --------------------------------------------------------------------
            오늘의 경주 섹션 — 실제 API 데이터
            -------------------------------------------------------------------- */}
        <section className="space-y-5">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">TODAY RACES</p>
              <h2 className="mt-2 font-heading text-3xl text-white">오늘의 경주</h2>
            </div>
            <Link
              to="/races"
              className="text-sm font-medium text-white/65 transition-colors hover:text-brand-gold-400"
            >
              전체 보기
            </Link>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {/* 로딩 중 → 스켈레톤 카드 3개 표시 */}
            {racesLoading && (
              <>
                <RaceCardSkeleton />
                <RaceCardSkeleton />
                <RaceCardSkeleton />
              </>
            )}

            {/* 오류 발생 시 */}
            {racesError && (
              <div className="col-span-full rounded-3xl border border-red-400/20 bg-red-400/5 px-5 py-8 text-center">
                <p className="text-sm text-red-400">
                  데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
                </p>
              </div>
            )}

            {/* 데이터 없음 */}
            {!racesLoading && !racesError && upcomingRaces?.length === 0 && (
              <div className="col-span-full rounded-3xl border border-dashed border-white/15 bg-white/4 px-5 py-10 text-center">
                <p className="text-base text-white/72">오늘 예정된 경주가 없습니다.</p>
              </div>
            )}

            {/* 실제 경주 카드 */}
            {!racesLoading && upcomingRaces?.map((race) => (
              <RaceCard key={race.id} race={race} />
            ))}
          </div>
        </section>

        {/* --------------------------------------------------------------------
            정확도 섹션
            -------------------------------------------------------------------- */}
        <section className="grid gap-6 rounded-[2rem] border border-white/10 bg-brand-navy-900/55 p-6 lg:grid-cols-[0.8fr_1.2fr] lg:p-8">
          <div className="space-y-3">
            <p className="text-sm tracking-[0.2em] text-brand-gold-400">PREDICTION SCORE</p>
            <h2 className="font-heading text-3xl text-white">누적 예측 정확도</h2>
            <p className="max-w-xl text-sm leading-7 text-white/65">
              모델 고도화 전 단계라 현재 수치는 데모용 지표입니다.
            </p>
          </div>

          <div className="space-y-5">
            {accuracyMetrics.map((metric) => (
              <div key={metric.label} className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-white/70">{metric.label}</span>
                  <span className="font-semibold text-brand-gold-400">{metric.value}%</span>
                </div>
                <div className="h-3 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-brand-gold-400"
                    style={{ width: `${metric.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Layout>
  )
}

export default HomePage
