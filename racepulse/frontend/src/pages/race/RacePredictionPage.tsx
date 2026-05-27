// =============================================================================
// RacePredictionPage.tsx — 경주 예측 결과 페이지
// 라우트: /races/:raceId/prediction
// =============================================================================

import { lazy, Suspense, useEffect, useState } from 'react' // React 화면 상태, 지연 로딩, 렌더 후 실행 로직을 사용합니다.
import { Link, useParams } from 'react-router-dom' // 페이지 이동 링크와 URL의 raceId 값을 읽기 위해 사용합니다.

import Layout from '../../components/layout/Layout' // 모든 페이지가 공유하는 헤더/본문 레이아웃입니다.
import DataStatusBadge from '../../components/DataStatusBadge' // 데이터 수집 상태를 배지로 보여 주는 컴포넌트입니다.
import LoadingAnimation from '../../components/dynamic/LoadingAnimation' // lazy 컴포넌트를 불러오는 동안 보여 줄 로딩 컴포넌트입니다.
import SimulationAnimation from '../../components/dynamic/SimulationAnimation' // Monte Carlo 계산 흐름을 시각적으로 보여 주는 컴포넌트입니다.
import { useRace } from '../../hooks/useRaces' // 경주 기본 정보를 서버에서 가져오는 React Query 훅입니다.
import { usePrediction, usePredictionSimulation } from '../../hooks/usePrediction' // 예측 결과와 시뮬레이션 결과를 서버에서 가져오는 React Query 훅입니다.
import type { PredictionItem } from '../../types/prediction' // 말별 예측 카드 데이터 타입입니다.

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부경경마공원',
  JJ: '제주경마공원',
}

const CONDITION_GRADE_STYLES: Record<PredictionItem['conditionGrade'], string> = {
  최하: 'bg-red-500 text-white',
  하: 'bg-orange-400 text-brand-navy-950',
  중: 'bg-yellow-400 text-brand-navy-950',
  상: 'bg-lime-400 text-brand-navy-950',
  최상: 'bg-green-500 text-white',
}

type PredictionTab = '기본예측' | '가상시나리오' | '몬테카를로상세'

// 탭 목록을 상수로 분리하면 화면에 탭을 추가하거나 이름을 바꿀 때 한 곳만 수정하면 됩니다.
const PREDICTION_TABS: Array<{ id: PredictionTab; label: string }> = [
  { id: '기본예측', label: '기본 예측' },
  { id: '가상시나리오', label: '가상 시나리오' },
  { id: '몬테카를로상세', label: '몬테카를로 상세' },
]

// Dynamic Import란?
//   사용자가 실제로 "가상 시나리오" 탭을 누를 때 CounterfactualUI 코드를 내려받는 방식입니다.
//   Monte Carlo UI와 Worker 연결 코드는 무겁기 때문에 기본 예측 탭 사용자에게는 늦게 보내는 편이 빠릅니다.
const CounterfactualUI = lazy(() => import('../../components/dynamic/CounterfactualUI'))

function PredictionCard({
  prediction,
  animateBars,
}: {
  prediction: PredictionItem
  animateBars: boolean
}) {
  // 막대 차트는 숫자만 보여줄 때보다 "확률 차이"를 한눈에 읽기 쉬워서 넣었습니다.
  // 처음부터 width가 꽉 차 있으면 움직임이 느껴지지 않으므로,
  // 페이지가 열린 뒤 animateBars=true가 되면 0% → 실제 퍼센트로 부드럽게 늘어납니다.
  const winBarWidth = `${animateBars ? (prediction.winProbability ?? 0) : 0}%`
  const placeBarWidth = `${animateBars ? (prediction.placeProbability ?? 0) : 0}%`

  return (
    <article className="rounded-[2rem] border border-white/10 bg-white/5 p-5 shadow-lg shadow-black/10">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-brand-gold-400 text-2xl font-heading text-brand-navy-950">
            {prediction.predictedRank}
          </div>

          <div className="space-y-2">
            <div>
              <p className="text-xs tracking-[0.18em] text-white/45">예측 순위</p>
              <h2 className="mt-1 font-heading text-2xl text-white">{prediction.horseName}</h2>
            </div>
            <p className="text-sm text-white/65">
              게이트 {prediction.gateNo ?? '-'}번
            </p>
          </div>
        </div>

        {/* 조건 등급은 색으로 빠르게 읽히는 정보라서 고정 규칙 색상을 사용합니다.
            같은 등급이 항상 같은 색으로 보여야 사용자가 페이지를 넘겨도 헷갈리지 않습니다. */}
        <span
          className={[
            'inline-flex w-fit rounded-full px-3 py-1 text-sm font-semibold',
            CONDITION_GRADE_STYLES[prediction.conditionGrade],
          ].join(' ')}
        >
          컨디션 {prediction.conditionGrade}
        </span>
      </div>

      <div className="mt-6 space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/60">우승 확률</span>
            <span className="font-semibold text-white">
              {prediction.winProbability != null ? `${prediction.winProbability.toFixed(1)}%` : '-'}
            </span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-brand-gold-400 transition-[width] duration-700 ease-out"
              style={{ width: winBarWidth }}
            />
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-white/60">복승권 확률</span>
            <span className="font-semibold text-white">
              {prediction.placeProbability != null ? `${prediction.placeProbability.toFixed(1)}%` : '-'}
            </span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-lime-400 transition-[width] duration-700 ease-out"
              style={{ width: placeBarWidth }}
            />
          </div>
        </div>
      </div>

      <div className="mt-6 grid gap-2 rounded-2xl border border-white/8 bg-brand-navy-950/40 p-4">
        <p className="text-xs tracking-[0.18em] text-brand-gold-400">핵심 근거</p>
        {prediction.keyFeatures.map((feature) => (
          <p key={feature} className="text-sm text-white/72">
            • {feature}
          </p>
        ))}
      </div>
    </article>
  )
}

function RacePredictionPage() {
  const { raceId } = useParams<{ raceId: string }>()
  const id = raceId ? Number(raceId) : undefined

  // 탭 state를 hooks보다 먼저 선언해야 usePredictionSimulation에서 조건부로 사용 가능합니다.
  const [animateBars, setAnimateBars] = useState(false)
  const [activeTab, setActiveTab] = useState<PredictionTab>('기본예측')

  const { data: race, isLoading: raceLoading, isError: raceError } = useRace(id)
  const { data: prediction, isLoading: predictionLoading, isError: predictionError } = usePrediction(id)
  // 몬테카를로 탭 진입 시에만 시뮬레이션 결과를 가져옵니다 (불필요한 API 호출 방지).
  const { data: simulation } = usePredictionSimulation(activeTab === '몬테카를로상세' ? id : undefined)

  useEffect(() => {
    if (!prediction?.predictions?.length) {
      return
    }

    // setTimeout을 아주 짧게 주면 카드가 먼저 그려진 뒤 막대가 자라서
    // "값이 들어왔다"는 변화가 눈에 더 자연스럽게 보입니다.
    const timer = window.setTimeout(() => {
      setAnimateBars(true)
    }, 120)

    return () => window.clearTimeout(timer)
  }, [prediction?.predictions])

  if (raceLoading || predictionLoading) {
    return (
      <Layout>
        <div className="grid gap-6 animate-pulse">
          <div className="h-44 rounded-[2rem] bg-white/5" />
          <div className="h-40 rounded-[2rem] bg-white/5" />
          <div className="h-56 rounded-[2rem] bg-white/5" />
        </div>
      </Layout>
    )
  }

  if (raceError || predictionError || !race || !prediction) {
    return (
      <Layout>
        <div className="rounded-[2rem] border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
          <p className="text-base text-red-400">예측 결과를 불러오지 못했습니다.</p>
          <p className="mt-2 text-sm text-white/55">
            예측 데이터가 아직 준비되지 않았거나, ML 서버 연결 상태를 확인해야 합니다.
          </p>
          <Link to={`/races/${id ?? ''}`} className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
            경주 상세로 돌아가기
          </Link>
        </div>
      </Layout>
    )
  }

  const meetLabel = MEET_LABELS[race.meetCode] ?? race.meetCode
  const sortedPredictions = [...prediction.predictions].sort((a, b) => a.predictedRank - b.predictedRank)

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">경주 목록</Link>
          <span>/</span>
          <Link to={`/races/${race.id}`} className="hover:text-white/70">{race.raceName}</Link>
          <span>/</span>
          <span className="text-white/70">예측 결과</span>
        </nav>

        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div className="space-y-4">
              <div>
                <p className="text-sm tracking-[0.2em] text-brand-gold-400">{meetLabel}</p>
                <h1 className="mt-2 font-heading text-4xl text-white">{prediction.raceName}</h1>
              </div>

              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs text-white/45">출발 시각</p>
                  <p className="mt-2 font-semibold text-white">{race.startTime ?? '미정'}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs text-white/45">거리</p>
                  <p className="mt-2 font-semibold text-white">{race.distance}m</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs text-white/45">트랙 상태</p>
                  <p className="mt-2 font-semibold text-white">{race.trackType ?? '미정'}</p>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs text-white/45">날씨</p>
                  <p className="mt-2 font-semibold text-white">{race.weather ?? '-'}</p>
                </div>
              </div>
            </div>

            {race.dataStatus && <DataStatusBadge status={race.dataStatus} />}
          </div>

          {/* 이 문구는 "예측은 참고 정보"라는 점을 분명히 알려서
              사용자가 실제 결과와 예측 순위를 같은 개념으로 오해하지 않도록 돕습니다. */}
          <div className="mt-6 rounded-2xl border border-brand-gold-400/20 bg-brand-gold-400/10 p-4 text-sm leading-7 text-white/82">
            본 예측은 참고 및 데이터 분석 목적입니다.
            실제 착순은 경주 전개, 컨디션, 출발 변수에 따라 달라질 수 있습니다.
          </div>
        </section>

        <section className="space-y-5">
          <div className="flex flex-wrap gap-2 rounded-[2rem] border border-white/10 bg-white/5 p-2">
            {PREDICTION_TABS.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={[
                  'rounded-full px-4 py-2 text-sm font-semibold transition',
                  activeTab === tab.id
                    ? 'bg-brand-gold-400 text-brand-navy-950'
                    : 'text-white/60 hover:bg-white/8 hover:text-white',
                ].join(' ')}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {activeTab === '기본예측' && (
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1.4fr)_minmax(18rem,0.6fr)]">
              <div className="space-y-4">
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className="text-sm tracking-[0.2em] text-brand-gold-400">예측 보드</p>
                    <h2 className="mt-2 font-heading text-3xl text-white">예측 순위 목록</h2>
                  </div>
                  <p className="text-sm text-white/45">{sortedPredictions.length}마리 분석</p>
                </div>

                {sortedPredictions.map((item) => (
                  <PredictionCard
                    key={item.horseId}
                    prediction={item}
                    animateBars={animateBars}
                  />
                ))}
              </div>

              <aside className="space-y-4">
                <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
                  <p className="text-sm tracking-[0.18em] text-brand-gold-400">모델 정보</p>
                  <h3 className="mt-2 font-heading text-2xl text-white">모델 정보</h3>
                  <div className="mt-5 space-y-4">
                    <div className="rounded-2xl border border-white/10 bg-brand-navy-950/45 p-4">
                      <p className="text-xs text-white/45">사용 모델 버전</p>
                      <p className="mt-2 font-semibold text-white">{prediction.modelVersion ?? '-'}</p>
                    </div>
                    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                      <div className="rounded-2xl border border-white/10 bg-brand-navy-950/45 p-4">
                        <p className="text-xs text-white/45">1순위 누적 정확도</p>
                        <p className="mt-2 font-heading text-3xl text-brand-gold-400">
                          {prediction.top1Accuracy != null ? `${prediction.top1Accuracy.toFixed(1)}%` : '-'}
                        </p>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-brand-navy-950/45 p-4">
                        <p className="text-xs text-white/45">3순위 누적 정확도</p>
                        <p className="mt-2 font-heading text-3xl text-white">
                          {prediction.top3Accuracy != null ? `${prediction.top3Accuracy.toFixed(1)}%` : '-'}
                        </p>
                      </div>
                    </div>
                  </div>
                </section>

                <section className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
                  <p className="text-sm tracking-[0.18em] text-brand-gold-400">읽는 법</p>
                  <h3 className="mt-2 font-heading text-2xl text-white">읽는 법</h3>
                  <div className="mt-4 space-y-3 text-sm leading-7 text-white/68">
                    <p>예측 순위는 모델이 상대적으로 강하다고 판단한 순서입니다.</p>
                    <p>실제 착순과 다를 수 있으므로 배당, 컨디션, 현장 변수와 함께 보시는 것이 좋습니다.</p>
                    <p>조건 등급 색상은 승률 구간을 5단계로 나눈 참고 지표입니다.</p>
                  </div>
                </section>
              </aside>
            </section>
          )}

          {activeTab === '가상시나리오' && (
            <Suspense fallback={<LoadingAnimation />}>
              <CounterfactualUI predictions={sortedPredictions} />
            </Suspense>
          )}

          {activeTab === '몬테카를로상세' && (
            <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.7fr)]">
              <div className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
                <p className="text-sm tracking-[0.18em] text-brand-gold-400">계산 흐름</p>
                <h2 className="mt-2 font-heading text-3xl text-white">몬테카를로 상세</h2>
                <p className="mt-3 text-sm leading-7 text-white/65">
                  여러 번의 가상 경주를 반복해 각 말의 우승 가능성과 예상 순위 흐름을 비교합니다.
                </p>

                {/* 시뮬레이션 결과 로딩 중 */}
                {!simulation && (
                  <div className="mt-5">
                    <SimulationAnimation running={true} />
                    <p className="mt-3 text-center text-xs text-white/40">시뮬레이션 계산 중...</p>
                  </div>
                )}

                {/* 시뮬레이션 결과: 말별 순위 분포 막대 */}
                {simulation?.horses && (
                  <div className="mt-5 space-y-4">
                    {[...simulation.horses]
                      .sort((a, b) => (a.expectedRank ?? 99) - (b.expectedRank ?? 99))
                      .map((horse, idx) => {
                        // 1위 확률을 막대 너비로 사용 (0~100%)
                        const win1Pct = horse.rankDistribution?.['1'] ?? 0
                        const win3Pct = (horse.rankDistribution?.['1'] ?? 0)
                          + (horse.rankDistribution?.['2'] ?? 0)
                          + (horse.rankDistribution?.['3'] ?? 0)
                        return (
                          <div key={horse.horseId ?? idx}>
                            <div className="mb-1 flex items-center justify-between text-sm">
                              <span className="font-semibold text-white">{horse.horseName}</span>
                              <span className="text-xs text-white/50">
                                평균 {horse.expectedRank?.toFixed(1)}위 · 1위 {win1Pct.toFixed(1)}% · Top3 {win3Pct.toFixed(1)}%
                              </span>
                            </div>
                            {/* 1위 확률 막대 */}
                            <div className="h-5 overflow-hidden rounded-full bg-white/10">
                              <div
                                className="flex h-full items-center justify-end rounded-full bg-brand-gold-400 pr-2 text-[10px] font-bold text-brand-navy-950 transition-[width] duration-700"
                                style={{ width: `${Math.max(win1Pct, 4)}%` }}
                              >
                                {win1Pct >= 6 ? `${win1Pct.toFixed(0)}%` : ''}
                              </div>
                            </div>
                          </div>
                        )
                      })}
                  </div>
                )}
              </div>

              <aside className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5">
                <p className="text-sm tracking-[0.18em] text-brand-gold-400">요약 지표</p>
                <div className="mt-5 grid gap-3">
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-white/45">분석 대상</p>
                    <p className="mt-2 font-heading text-3xl text-white">{simulation?.horses?.length ?? sortedPredictions.length}마리</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-white/45">시뮬레이션 횟수</p>
                    <p className="mt-2 font-semibold text-white">
                      {simulation?.nSimulations != null
                        ? `${simulation.nSimulations.toLocaleString()}회`
                        : '계산 중...'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-white/45">1위 유력 (시뮬레이션)</p>
                    <p className="mt-2 font-semibold text-brand-gold-400">
                      {simulation?.horses
                        ? [...simulation.horses].sort((a, b) => (a.expectedRank ?? 99) - (b.expectedRank ?? 99))[0]?.horseName ?? '-'
                        : '-'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-white/45">이변 지수</p>
                    <p className="mt-2 text-sm text-white/70">
                      {simulation?.upsetProbability != null
                        ? `${(simulation.upsetProbability * 100).toFixed(1)}%`
                        : '-'}
                    </p>
                  </div>
                </div>
              </aside>
            </section>
          )}
        </section>
      </div>
    </Layout>
  )
}

export default RacePredictionPage
