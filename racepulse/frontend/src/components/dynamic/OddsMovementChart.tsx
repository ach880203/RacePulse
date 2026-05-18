import OptimizedEChart from './OptimizedEChart' // ECharts를 React에서 쓰기 쉽게 감싼 공통 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // 차트 설정 타입입니다.

interface OddsMovementChartProps {
  // points = 시간별 배당 흐름입니다. 배당이 크게 내려가는 구간을 스마트 머니 후보로 표시합니다.
  points: {
    time: string
    odds: number
  }[]
  horseName: string
}

function OddsMovementChart({ points, horseName }: OddsMovementChartProps) {
  const openingOdds = points[0]?.odds ?? 0
  const latestOdds = points[points.length - 1]?.odds ?? openingOdds
  const dropRate = openingOdds > 0 ? (openingOdds - latestOdds) / openingOdds : 0
  const smartMoneyDetected = dropRate >= 0.15

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => `${Number(value).toFixed(2)}배`,
    },
    grid: { left: 38, right: 18, top: 24, bottom: 32 },
    xAxis: {
      type: 'category',
      data: points.map((point) => point.time),
      axisLabel: { color: 'rgba(255,255,255,0.58)' },
    },
    yAxis: {
      type: 'value',
      min: 'dataMin',
      max: 'dataMax',
      axisLabel: { color: 'rgba(255,255,255,0.58)' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: [
      {
        type: 'line',
        name: '배당',
        data: points.map((point) => point.odds),
        smooth: true,
        symbolSize: 6,
        lineStyle: { color: 'var(--color-brand-gold-400)', width: 3 },
        itemStyle: { color: 'var(--color-brand-gold-400)' },
        markPoint: smartMoneyDetected
          ? {
              data: [{ name: '스마트 머니', coord: [points.length - 1, latestOdds], value: latestOdds }],
              itemStyle: { color: 'var(--color-red-300)' },
            }
          : undefined,
      },
    ],
  }

  return (
    <div className="rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-white/55">배당률 변화</p>
          <h3 className="font-heading text-xl text-white">{horseName}</h3>
        </div>
        {smartMoneyDetected && (
          <span className="rounded-full border border-red-300/45 bg-red-300/12 px-3 py-1 text-sm font-semibold text-red-200">
            스마트 머니 감지
          </span>
        )}
      </div>

      <div className="h-56">
        <OptimizedEChart option={option} />
      </div>
    </div>
  )
}

export default OddsMovementChart
