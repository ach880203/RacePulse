import OptimizedEChart from './OptimizedEChart' // ECharts core 등록 방식으로 만든 가벼운 차트 컴포넌트입니다.
import RunningStyleBadge from './RunningStyleBadge' // 말별 주행 스타일을 배지로 표시하는 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // 차트 설정 타입입니다.

interface StyleMatchMatrixProps {
  // horses = 이번 경주 출전마의 주행 스타일 목록입니다. 상위 페이지에서 API 결과를 넘겨 줍니다.
  horses: {
    horseName: string
    style: 'LEADER' | 'STALKER' | 'CLOSER' | 'PRESSER' | 'UNKNOWN'
    confidence: number
  }[]
}

const styleLabels = {
  LEADER: '선행',
  STALKER: '추적',
  CLOSER: '추입',
  PRESSER: '압박',
  UNKNOWN: '분석중',
}

function StyleMatchMatrix({ horses }: StyleMatchMatrixProps) {
  const styles = ['LEADER', 'STALKER', 'CLOSER', 'PRESSER', 'UNKNOWN'] as const
  const chartData = styles.map((style) => ({
    name: styleLabels[style],
    count: horses.filter((horse) => horse.style === style).length,
  }))
  const leaderCount = chartData[0].count
  const closerCount = chartData[2].count
  const analysisText = leaderCount >= 3 ? '선행 경합 경주' : closerCount >= 2 ? '추입 유리 경주' : '균형형 경주'

  const option: EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 34, right: 16, top: 20, bottom: 30 },
    xAxis: {
      type: 'category',
      data: chartData.map((item) => item.name),
      axisLabel: { color: 'rgba(255,255,255,0.58)' },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: 'rgba(255,255,255,0.58)' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: [
      {
        type: 'bar',
        name: '마리 수',
        data: chartData.map((item) => item.count),
        itemStyle: { color: 'var(--color-brand-gold-400)', borderRadius: [6, 6, 0, 0] },
      },
    ],
  }

  return (
    <div className="rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-white/55">주행 스타일 충돌 분석</p>
          <h3 className="mt-1 font-heading text-2xl text-brand-gold-400">{analysisText}</h3>
        </div>
        <p className="rounded-full border border-white/10 px-3 py-1 text-sm text-white/70">출전 {horses.length}두</p>
      </div>

      <div className="mt-5 h-56">
        <OptimizedEChart option={option} />
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {horses.map((horse) => (
          <div key={horse.horseName} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
            <span className="truncate text-sm text-white">{horse.horseName}</span>
            <RunningStyleBadge style={horse.style} confidence={horse.confidence} size="sm" />
          </div>
        ))}
      </div>
    </div>
  )
}

export default StyleMatchMatrix
