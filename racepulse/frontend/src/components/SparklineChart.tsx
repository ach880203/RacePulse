// =============================================================================
// SparklineChart.tsx — 최근 경주 착순을 간단한 선 차트로 표시하는 컴포넌트
// =============================================================================
// Recharts란?
//   React에서 차트를 쉽게 그리는 라이브러리입니다.
//   ResponsiveContainer = 부모 크기에 맞게 자동으로 늘어나는 컨테이너
//   LineChart          = 선 그래프 컴포넌트
//   Line               = 실제 선을 그리는 컴포넌트
//   YAxis의 reversed   = 착순은 1위가 가장 좋으므로 Y축을 뒤집습니다 (1이 맨 위)
// =============================================================================

// Recharts 컴포넌트들
import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  YAxis,
} from 'recharts'

interface Props {
  // data = [{ order: 1 }, { order: 3 }, ...] 형식의 착순 기록 배열
  data: { order: number }[]
  // height = 차트 높이(픽셀), 기본값 64
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

  return (
    // ResponsiveContainer = width="100%"로 설정하면 부모 컨테이너 너비를 꽉 채웁니다.
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 4, right: 4, left: 4, bottom: 4 }}>
        {/* YAxis reversed = 착순이 낮을수록(1위) 위에 표시되도록 Y축을 뒤집습니다. */}
        <YAxis
          reversed
          domain={[1, 'dataMax']}
          hide  // 축 레이블은 숨깁니다. 스파크라인은 트렌드만 보여주면 충분합니다.
        />
        {/* Tooltip = 마우스를 올리면 해당 데이터 값을 보여주는 말풍선입니다. */}
        <Tooltip
          contentStyle={{
            background: '#0d1628',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '0.75rem',
            color: '#fff',
            fontSize: '0.75rem',
          }}
          formatter={(value: number) => [`${value}위`, '착순']}
          labelFormatter={() => ''}
        />
        {/* Line = 실제 꺾은선을 그립니다. dataKey="order"는 데이터에서 읽을 필드 이름입니다. */}
        <Line
          type="monotone"
          dataKey="order"
          stroke="#f5c842"   // brand-gold-400 색상
          strokeWidth={2}
          dot={{ r: 3, fill: '#f5c842', strokeWidth: 0 }}
          activeDot={{ r: 5, fill: '#f5c842' }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}

export default SparklineChart
