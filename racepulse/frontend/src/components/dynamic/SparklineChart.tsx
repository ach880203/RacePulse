import OptimizedEChart from './OptimizedEChart' // 필요한 ECharts 기능만 등록한 공통 차트 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // 차트 설정 객체 타입입니다.

interface SparklineChartProps {
  // ranks = 최근 착순 배열입니다. 숫자가 낮을수록 좋은 순위입니다.
  ranks: number[]
}

function SparklineChart({ ranks }: SparklineChartProps) {
  const isImproving = ranks.length > 1 ? ranks[ranks.length - 1] <= ranks[0] : true

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const firstParam = Array.isArray(params) ? params[0] : params
        return `${firstParam.value}위`
      },
    },
    grid: { top: 8, right: 8, bottom: 8, left: 8 },
    xAxis: {
      type: 'category',
      data: ranks.map((_, index) => `${index + 1}전`),
      show: false,
    },
    yAxis: {
      type: 'value',
      inverse: true,
      show: false,
      minInterval: 1,
    },
    series: [
      {
        type: 'line',
        data: ranks,
        smooth: true,
        symbol: 'none',
        lineStyle: {
          width: 2,
          color: isImproving ? 'var(--color-brand-gold-400)' : 'rgb(248 113 113)',
        },
      },
    ],
  }

  return (
    <div className="h-20 w-full">
      <OptimizedEChart option={option} />
    </div>
  )
}

export default SparklineChart
