import OptimizedEChart from './OptimizedEChart' // 필요한 ECharts 기능만 등록한 공통 차트 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // 차트 설정 객체의 타입입니다.

interface PaceLineChartProps {
  // horses = 말별 구간 기록입니다. sections 배열의 각 숫자가 1구간, 2구간 값을 뜻합니다.
  horses: { name: string; sections: number[] }[]
}

function PaceLineChart({ horses }: PaceLineChartProps) {
  const maxSectionCount = Math.max(...horses.map((horse) => horse.sections.length), 0)
  const sectionLabels = Array.from({ length: maxSectionCount }, (_, sectionIndex) => `${sectionIndex + 1}구간`)

  const option: EChartsOption = {
    tooltip: { trigger: 'axis' },
    grid: { left: 36, right: 18, top: 24, bottom: 32 },
    xAxis: {
      type: 'category',
      data: sectionLabels,
      axisLabel: { color: 'rgba(255,255,255,0.55)' },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: 'rgba(255,255,255,0.55)' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: horses.map((horse, index) => ({
      type: 'line',
      name: horse.name,
      data: horse.sections,
      smooth: true,
      symbolSize: 6,
      lineStyle: {
        width: 2,
        color: index === 0 ? 'var(--color-brand-gold-400)' : 'rgba(255,255,255,0.65)',
      },
      itemStyle: {
        color: index === 0 ? 'var(--color-brand-gold-400)' : 'rgba(255,255,255,0.65)',
      },
    })),
  }

  return (
    <div className="h-72 rounded-lg border border-white/10 bg-white/5 p-4">
      <OptimizedEChart option={option} />
    </div>
  )
}

export default PaceLineChart
