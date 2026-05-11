import { useState } from 'react'

import Layout from '../components/layout/Layout'
import {
  AccuracyCircleGauge,
  CollectionCountdown,
  ConditionColorBadge,
  ConditionGauge,
  HorseCardHover,
  HorseCardSlideIn,
  LoadingAnimation,
  PaceLineChart,
  PredictionVsActualGauge,
  RaceStartCountdown,
  RatingRadarChart,
  ResultRevealAnimation,
  SimulationAnimation,
  SparklineChart,
  TypingAnimation,
  WinProbabilityBar,
} from '../components/dynamic'

const sampleRatings = [
  { label: '순발력', value: 82 },
  { label: '지구력', value: 76 },
  { label: '게이트', value: 68 },
  { label: '최근폼', value: 88 },
  { label: '기수', value: 72 },
]

function DemoPanel({ title, children }: { title: string; children: React.ReactNode }) {
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
            <ResultRevealAnimation results={[{ rank: 1, horseName: '천하제일' }, { rank: 2, horseName: '바람질주' }, { rank: 3, horseName: '금빛돌풍' }]} />
          </DemoPanel>
          <DemoPanel title="페이스 라인">
            <PaceLineChart horses={[{ name: '천하제일', sections: [13.1, 12.8, 12.4, 12.2] }, { name: '바람질주', sections: [13.4, 12.9, 12.6, 12.5] }]} />
          </DemoPanel>
          <DemoPanel title="예측/실제 비교">
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
      </main>
    </Layout>
  )
}

export default ComponentDemoPage
