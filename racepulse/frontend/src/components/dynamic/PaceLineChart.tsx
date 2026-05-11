import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

interface PaceLineChartProps {
  horses: { name: string; sections: number[] }[]
}

function PaceLineChart({ horses }: PaceLineChartProps) {
  const maxSectionCount = Math.max(...horses.map((horse) => horse.sections.length), 0)
  const data = Array.from({ length: maxSectionCount }, (_, sectionIndex) => {
    const row: Record<string, number | string> = { section: `${sectionIndex + 1}구간` }
    horses.forEach((horse) => {
      row[horse.name] = horse.sections[sectionIndex] ?? 0
    })
    return row
  })

  return (
    <div className="h-72 rounded-lg border border-white/10 bg-white/5 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <XAxis dataKey="section" stroke="rgba(255,255,255,0.55)" />
          <YAxis stroke="rgba(255,255,255,0.55)" />
          <Tooltip />
          {horses.map((horse, index) => (
            <Line key={horse.name} type="monotone" dataKey={horse.name} stroke={index === 0 ? 'var(--color-brand-gold-400)' : 'rgba(255,255,255,0.65)'} strokeWidth={2} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default PaceLineChart
