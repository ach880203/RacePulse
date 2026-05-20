// =============================================================================
// SparklineChart.tsx — 최근 경주 착순을 간단한 선 차트로 표시하는 컴포넌트
// =============================================================================
// ECharts core 버전을 쓰는 이유:
//   전체 차트 라이브러리를 한 번에 넣지 않고 필요한 선 차트 기능만 빌드에 포함하기 위해서입니다.
//   이 방식은 번들 크기를 줄이는 Tree Shaking에 유리합니다.
// =============================================================================

import OptimizedEChart from './dynamic/OptimizedEChart' // 필요한 ECharts 기능만 등록한 공통 차트 컴포넌트입니다.
import type { EChartsOption } from './dynamic/OptimizedEChart' // 차트 설정 객체 타입입니다.

interface Props {
  // data = [{ order: 1 }, { order: 3 }, ...] 형식의 착순 기록 배열입니다.
  data: { order: number }[]
  // height = 차트 높이(픽셀), 기본값 64입니다.
  height?: number
}

function SparklineChart({ data, height = 64 }: Props) {
  if (data.length === 0) {
    return (
      <div className="flex h-16 items-center justify-center rounded-2xl border border-dashed border-white/15">
        <p className="text-xs text-white/40">경주 이력 없음</p>
      </div>
    )
  }

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const firstParam = Array.isArray(params) ? params[0] : params
        return `${firstParam.value}위`
      },
    },
    grid: { left: 4, right: 4, top: 4, bottom: 4 },
    xAxis: {
      type: 'category',
      data: data.map((_, index) => `${index + 1}`),
      show: false,
    },
    yAxis: {
      type: 'value',
      inverse: true,
      minInterval: 1,
      show: false,
    },
    series: [
      {
        type: 'line',
        data: data.map((item) => item.order),
        smooth: true,
        symbolSize: 5,
        lineStyle: { color: 'var(--color-brand-gold-400)', width: 2 },
        itemStyle: { color: 'var(--color-brand-gold-400)' },
      },
    ],
  }

  return <OptimizedEChart option={option} height={height} />
}

export default SparklineChart
