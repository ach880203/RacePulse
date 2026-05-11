import { useEffect, useState } from 'react'

interface WinProbabilityBarProps {
  probability: number
  label?: string
}

function WinProbabilityBar({ probability, label = '승리 확률' }: WinProbabilityBarProps) {
  const [animatedValue, setAnimatedValue] = useState(0)
  const safeProbability = Math.max(0, Math.min(100, probability))

  useEffect(() => {
    const timer = window.setTimeout(() => setAnimatedValue(safeProbability), 80)
    return () => window.clearTimeout(timer)
  }, [safeProbability])

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <span className="text-white/65">{label}</span>
        <span className="font-semibold text-brand-gold-400">{safeProbability.toFixed(1)}%</span>
      </div>
      <div className="h-3 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-brand-gold-400 transition-[width] duration-700 ease-out"
          style={{ width: `${animatedValue}%` }}
        />
      </div>
    </div>
  )
}

export default WinProbabilityBar
