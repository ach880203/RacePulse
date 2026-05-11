import { Line, LineChart, ResponsiveContainer, Tooltip, YAxis } from 'recharts'

interface SparklineChartProps {
  ranks: number[]
}

function SparklineChart({ ranks }: SparklineChartProps) {
  const data = ranks.map((rank, index) => ({ name: `${index + 1}전`, rank }))
  const isImproving = ranks.length > 1 ? ranks[ranks.length - 1] <= ranks[0] : true

  return (
    <div className="h-20 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
          <YAxis reversed hide domain={[1, 'dataMax']} />
          <Tooltip formatter={(value) => [`${value}위`, '착순']} labelStyle={{ color: 'var(--color-brand-navy-950)' }} />
          <Line type="monotone" dataKey="rank" stroke={isImproving ? 'var(--color-brand-gold-400)' : 'rgb(248 113 113)'} strokeWidth={2} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default SparklineChart
