// =============================================================================
// OptimizedEChart.tsx — 필요한 ECharts 기능만 등록해서 쓰는 공통 차트 컴포넌트
// =============================================================================
// 번들(Bundle)이란?
//   브라우저가 내려받을 수 있도록 여러 TypeScript/React 파일을 하나 이상의 JS 파일로 묶은 결과물입니다.
//   너무 큰 번들은 첫 화면 로딩을 느리게 만들기 때문에 필요한 코드만 담는 것이 중요합니다.
//
// Tree Shaking이란?
//   나무에서 죽은 잎을 떨어뜨리듯, 실제로 쓰지 않는 코드를 빌드 결과에서 제거하는 최적화입니다.
//   ECharts도 core 방식으로 필요한 차트만 등록해야 Tree Shaking 효과가 커집니다.
// =============================================================================

import { BarChart, GaugeChart, LineChart, RadarChart } from 'echarts/charts' // 막대/게이지/선/레이더 차트 기능만 가져옵니다.
import {
  GridComponent,
  LegendComponent,
  MarkLineComponent,
  MarkPointComponent,
  PolarComponent,
  RadarComponent,
  TooltipComponent,
} from 'echarts/components' // 축, 범례, 툴팁, 레이더 좌표계처럼 차트 주변 부품만 가져옵니다.
import type { EChartsOption } from 'echarts' // 차트 설정 객체의 TypeScript 타입입니다.
import * as echarts from 'echarts/core' // ECharts 전체가 아니라 core 등록 시스템만 가져옵니다.
import { CanvasRenderer } from 'echarts/renderers' // Canvas 렌더러는 SVG보다 많은 데이터에서 안정적인 기본 렌더러입니다.
import ReactEChartsCore from 'echarts-for-react/lib/core' // React에서 ECharts 인스턴스를 안전하게 붙여 주는 얇은 연결 컴포넌트입니다.

// echarts.use(...)는 "이 프로젝트에서 사용할 차트 부품 목록"을 등록하는 단계입니다.
// 전체 ECharts를 import하지 않아도 되므로 대시보드/동적 컴포넌트 청크가 작아집니다.
echarts.use([
  BarChart,
  GaugeChart,
  GridComponent,
  LegendComponent,
  LineChart,
  MarkLineComponent,
  MarkPointComponent,
  PolarComponent,
  RadarComponent,
  RadarChart,
  TooltipComponent,
  CanvasRenderer,
])

interface OptimizedEChartProps {
  option: EChartsOption
  className?: string
  height?: number | string
}

function OptimizedEChart({ option, className, height = '100%' }: OptimizedEChartProps) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      notMerge
      lazyUpdate
      className={className}
      style={{ height, width: '100%' }}
    />
  )
}

export type { EChartsOption }
export default OptimizedEChart
