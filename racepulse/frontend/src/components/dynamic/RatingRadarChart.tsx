import OptimizedEChart from './OptimizedEChart' // ECharts core 방식으로 가볍게 등록된 차트 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // ECharts option 객체의 타입입니다.

interface RatingRadarChartProps {
  // ratings = 스피드/체력/컨디션처럼 레이더 차트 축에 표시할 지표입니다.
  ratings: { label: string; value: number }[]
}

function RatingRadarChart({ ratings }: RatingRadarChartProps) {
  const option: EChartsOption = {
    tooltip: {},
    radar: {
      indicator: ratings.map((rating) => ({ name: rating.label, max: 100 })),
      axisName: { color: 'rgba(255,255,255,0.72)' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.16)' } },
      splitArea: { areaStyle: { color: ['rgba(255,255,255,0.03)', 'rgba(255,255,255,0.06)'] } },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.16)' } },
    },
    series: [
      {
        type: 'radar',
        data: [{ value: ratings.map((rating) => rating.value), name: '능력치' }],
        areaStyle: { color: 'rgba(245, 200, 66, 0.28)' },
        lineStyle: { color: 'var(--color-brand-gold-400)', width: 2 },
        itemStyle: { color: 'var(--color-brand-gold-400)' },
      },
    ],
  }

  return (
    <div className="h-64 rounded-lg border border-white/10 bg-white/5 p-4">
      <OptimizedEChart option={option} />
    </div>
  )
}

export default RatingRadarChart
