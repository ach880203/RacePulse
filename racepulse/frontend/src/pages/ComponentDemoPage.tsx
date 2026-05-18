import { useState, type ReactNode } from 'react'

import Layout from '../components/layout/Layout'
import {
  AccuracyCircleGauge,
  CollectionCountdown,
  ConfidenceScoreMeter,
  ConditionColorBadge,
  ConditionGauge,
  FormTrendLine,
  GateBiasIndicator,
  HorseCardHover,
  HorseCardSlideIn,
  LoadingAnimation,
  MonteCarloHeatmap,
  OddsMovementChart,
  PaceLineChart,
  PredictionVsActualGauge,
  RaceStartCountdown,
  RankDistributionBar,
  RatingRadarChart,
  ResultRevealAnimation,
  RivalH2HCard,
  RunningStyleBadge,
  SimulationAnimation,
  SparklineChart,
  StyleMatchMatrix,
  TypingAnimation,
  WeatherRaceImpact,
  WinProbabilityBar,
} from '../components/dynamic'

const sampleRatings = [
  { label: '순발력', value: 82 },
  { label: '지구력', value: 76 },
  { label: '게이트', value: 68 },
  { label: '최근 폼', value: 88 },
  { label: '기수', value: 72 },
]

const sampleStyleHorses = [
  { horseName: '천하제일', style: 'LEADER' as const, confidence: 0.86 },
  { horseName: '바람질주', style: 'LEADER' as const, confidence: 0.72 },
  { horseName: '금빛태풍', style: 'STALKER' as const, confidence: 0.67 },
  { horseName: '새벽질주', style: 'CLOSER' as const, confidence: 0.81 },
  { horseName: '라스트스퍼트', style: 'CLOSER' as const, confidence: 0.44 },
]

const sampleHeatmapHorses = [
  { horseName: '천하제일', ranks: [31.2, 24.4, 18.1, 11.6, 6.8] },
  { horseName: '바람질주', ranks: [22.1, 23.8, 17.4, 14.2, 8.5] },
  { horseName: '금빛태풍', ranks: [18.5, 20.1, 21.8, 15.5, 9.2] },
]

const sampleOddsPoints = [
  { time: '09:00', odds: 6.2 },
  { time: '10:00', odds: 5.8 },
  { time: '11:00', odds: 5.1 },
  { time: '12:00', odds: 4.7 },
  { time: '13:00', odds: 4.4 },
]

const sampleFormRaces = [
  { raceName: '1전', rank: 7 },
  { raceName: '2전', rank: 6 },
  { raceName: '3전', rank: 5 },
  { raceName: '4전', rank: 5 },
  { raceName: '5전', rank: 4 },
  { raceName: '6전', rank: 3 },
  { raceName: '7전', rank: 4 },
  { raceName: '8전', rank: 2 },
  { raceName: '9전', rank: 2 },
  { raceName: '10전', rank: 1 },
]

const sampleRankDistribution = [
  { horseName: '천하제일', distribution: { first: 29, second: 24, third: 18, fourthPlus: 29 } },
  { horseName: '바람질주', distribution: { first: 22, second: 21, third: 18, fourthPlus: 39 } },
  { horseName: '금빛태풍', distribution: { first: 18, second: 22, third: 24, fourthPlus: 36 } },
]

function DemoPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-lg border border-white/10 bg-white/[0.04] p-5">
      <h2 className="mb-4 font-heading text-xl text-brand-gold-400">{title}</h2>
      {children}
    </section>
  )
}

function ComponentDemoPage() {
  const [futureTime] = useState(() => new Date(Date.now() + 42 * 60 * 1000).toISOString())

  return (
    <Layout>
      <main className="mx-auto max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
        <div className="mb-8">
          <p className="text-sm font-semibold text-brand-gold-400">개발 확인용</p>
          <h1 className="mt-2 font-heading text-4xl text-white">동적 UI 컴포넌트 데모</h1>
        </div>

        <section>
          <h2 className="mb-5 font-heading text-2xl text-white">Phase 1 동적 UI</h2>
          <div className="grid gap-5 lg:grid-cols-2">
            <DemoPanel title="컨디션 게이지">
              <ConditionGauge grade="상" />
            </DemoPanel>
            <DemoPanel title="승률 바">
              <WinProbabilityBar probability={36.8} />
            </DemoPanel>
            <DemoPanel title="말 카드 호버">
              <HorseCardHover name="천하제일" jockeyName="김기수" odds="4.8배" recentRanks={[5, 3, 2, 2, 1]} />
            </DemoPanel>
            <DemoPanel title="컨디션 배지">
              <div className="flex flex-wrap gap-2">
                {(['최하', '하', '중', '상', '최상'] as const).map((grade) => (
                  <ConditionColorBadge key={grade} grade={grade} />
                ))}
              </div>
            </DemoPanel>
            <DemoPanel title="레이더 차트">
              <RatingRadarChart ratings={sampleRatings} />
            </DemoPanel>
            <DemoPanel title="슬라이드 카드">
              <div className="space-y-3">
                {['1번마', '2번마', '3번마'].map((name, index) => (
                  <HorseCardSlideIn key={name} index={index}>
                    <div className="rounded-lg bg-white/8 p-4 text-white">{name}</div>
                  </HorseCardSlideIn>
                ))}
              </div>
            </DemoPanel>
            <DemoPanel title="시뮬레이션 애니메이션">
              <SimulationAnimation />
            </DemoPanel>
            <DemoPanel title="스파크라인">
              <SparklineChart ranks={[4, 3, 2, 2, 1]} />
            </DemoPanel>
            <DemoPanel title="결과 공개">
              <ResultRevealAnimation results={[{ rank: 1, horseName: '천하제일' }, { rank: 2, horseName: '바람질주' }, { rank: 3, horseName: '금빛태풍' }]} />
            </DemoPanel>
            <DemoPanel title="페이스 라인">
              <PaceLineChart horses={[{ name: '천하제일', sections: [13.1, 12.8, 12.4, 12.2] }, { name: '바람질주', sections: [13.4, 12.9, 12.6, 12.5] }]} />
            </DemoPanel>
            <DemoPanel title="예측과 실제 비교">
              <PredictionVsActualGauge predictedRank={1} actualRank={1} />
            </DemoPanel>
            <DemoPanel title="정확도 원형 게이지">
              <AccuracyCircleGauge accuracy={74} />
            </DemoPanel>
            <DemoPanel title="수집 카운트다운">
              <CollectionCountdown nextUpdateAt={futureTime} dataStatus="READY" />
            </DemoPanel>
            <DemoPanel title="경주 시작 카운트다운">
              <RaceStartCountdown startTime={futureTime} />
            </DemoPanel>
            <DemoPanel title="타이핑 애니메이션">
              <TypingAnimation text="AI가 경주 흐름과 최근 성적을 바탕으로 핵심 변수를 정리하고 있습니다." />
            </DemoPanel>
            <DemoPanel title="로딩 애니메이션">
              <LoadingAnimation />
            </DemoPanel>
          </div>
        </section>

        <section className="mt-12">
          <h2 className="mb-5 font-heading text-2xl text-white">Phase 2 동적 UI</h2>
          <div className="grid gap-5 lg:grid-cols-2">
            <DemoPanel title="라이벌 맞대결 카드">
              <RivalH2HCard horseAId={1} horseBId={7} horseAName="천하제일" horseBName="바람질주" />
            </DemoPanel>
            <DemoPanel title="주행 스타일 배지">
              <div className="flex flex-wrap gap-2">
                <RunningStyleBadge style="LEADER" confidence={0.86} />
                <RunningStyleBadge style="STALKER" confidence={0.71} />
                <RunningStyleBadge style="CLOSER" confidence={0.83} />
                <RunningStyleBadge style="UNKNOWN" confidence={0.32} />
              </div>
            </DemoPanel>
            <DemoPanel title="주행 스타일 매트릭스">
              <StyleMatchMatrix horses={sampleStyleHorses} />
            </DemoPanel>
            <DemoPanel title="Monte Carlo 히트맵">
              <MonteCarloHeatmap horses={sampleHeatmapHorses} />
            </DemoPanel>
            <DemoPanel title="배당률 변화 차트">
              <OddsMovementChart horseName="천하제일" points={sampleOddsPoints} />
            </DemoPanel>
            <DemoPanel title="게이트 영향 지표">
              <GateBiasIndicator gates={[{ gateNo: 1, bias: 8 }, { gateNo: 8, bias: 2 }, { gateNo: 12, bias: -3 }]} />
            </DemoPanel>
            <DemoPanel title="Monte Carlo 신뢰도 미터">
              <ConfidenceScoreMeter score={78} />
            </DemoPanel>
            <DemoPanel title="최근 10경주 폼 트렌드">
              <FormTrendLine races={sampleFormRaces} />
            </DemoPanel>
            <DemoPanel title="날씨와 경주 영향">
              <WeatherRaceImpact weather="RAIN" weatherUncertaintySigma={0.05} />
            </DemoPanel>
            <DemoPanel title="순위 분포 막대">
              <RankDistributionBar horses={sampleRankDistribution} />
            </DemoPanel>
          </div>
        </section>
      </main>
    </Layout>
  )
}

export default ComponentDemoPage
