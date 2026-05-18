import OptimizedEChart from './OptimizedEChart' // Recharts 대신 필요한 ECharts 기능만 쓰는 공통 컴포넌트입니다.
import type { EChartsOption } from './OptimizedEChart' // 차트 설정 객체 타입입니다.

interface FormTrendLineProps {
  // races = 최근 10경주의 착순입니다. 낮은 착순 숫자가 좋은 성적입니다.
  races: {
    raceName: string
    rank: number
    href?: string
  }[]
}

function FormTrendLine({ races }: FormTrendLineProps) {
  const firstRank = races[0]?.rank ?? 0
  const lastRank = races[races.length - 1]?.rank ?? firstRank
  const trendText = lastRank < firstRank ? '상승세' : lastRank > firstRank ? '하락세' : '안정'
  const averageRank = races.length > 0 ? races.reduce((sum, race) => sum + race.rank, 0) / races.length : 0

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      valueFormatter: (value) => `${value}위`,
    },
    grid: { left: 38, right: 18, top: 24, bottom: 32 },
    xAxis: {
      type: 'category',
      data: races.map((race) => race.raceName),
      axisLabel: { color: 'rgba(255,255,255,0.58)' },
    },
    yAxis: {
      type: 'value',
      inverse: true,
      minInterval: 1,
      axisLabel: { color: 'rgba(255,255,255,0.58)', formatter: '{value}위' },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.08)' } },
    },
    series: [
      {
        type: 'line',
        name: '착순',
        data: races.map((race) => race.rank),
        smooth: true,
        symbolSize: 7,
        lineStyle: { color: 'var(--color-brand-gold-400)', width: 3 },
        itemStyle: { color: 'var(--color-brand-gold-400)' },
        markLine: {
          symbol: 'none',
          lineStyle: { color: 'rgba(255,255,255,0.35)', type: 'dashed' },
          data: [{ yAxis: averageRank, name: '평균' }],
        },
      },
    ],
  }

  return (
    <div className="rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm text-white/55">최근 10경주 폼 트렌드</p>
          <h3 className="font-heading text-2xl text-brand-gold-400">{trendText}</h3>
        </div>
        <p className="text-sm text-white/65">평균 {averageRank.toFixed(1)}위</p>
      </div>
      <div className="h-56">
        <OptimizedEChart option={option} />
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {races.map((race) => (
          <a key={race.raceName} href={race.href ?? '#'} className="rounded border border-white/10 px-3 py-1 text-xs text-white/70 transition hover:border-brand-gold-400/50 hover:text-brand-gold-400">
            {race.raceName}
          </a>
        ))}
      </div>
    </div>
  )
}

export default FormTrendLine
