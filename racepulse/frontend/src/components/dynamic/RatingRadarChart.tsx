import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts'

interface RatingRadarChartProps {
  ratings: { label: string; value: number }[]
}

function RatingRadarChart({ ratings }: RatingRadarChartProps) {
  return (
    <div className="h-64 rounded-lg border border-white/10 bg-white/5 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart data={ratings}>
          <PolarGrid stroke="rgba(255,255,255,0.18)" />
          <PolarAngleAxis dataKey="label" tick={{ fill: 'rgba(255,255,255,0.72)', fontSize: 12 }} />
          <Tooltip />
          <Radar dataKey="value" stroke="var(--color-brand-gold-400)" fill="var(--color-brand-gold-400)" fillOpacity={0.28} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  )
}

export default RatingRadarChart
