import { useEffect, useState } from 'react'

interface AccuracyCircleGaugeProps {
  accuracy: number
}

function AccuracyCircleGauge({ accuracy }: AccuracyCircleGaugeProps) {
  const [value, setValue] = useState(0)
  const safeAccuracy = Math.max(0, Math.min(100, accuracy))
  const strokeDasharray = `${(value / 100) * 283} 283`

  useEffect(() => {
    let frame = 0
    const timer = window.setInterval(() => {
      frame += 1
      setValue(Math.min(safeAccuracy, Math.round((safeAccuracy / 24) * frame)))
      if (frame >= 24) window.clearInterval(timer)
    }, 24)
    return () => window.clearInterval(timer)
  }, [safeAccuracy])

  return (
    <div className="relative h-36 w-36">
      <svg viewBox="0 0 100 100" className="-rotate-90">
        <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.12)" strokeWidth="8" />
        <circle cx="50" cy="50" r="45" fill="none" stroke={safeAccuracy >= 70 ? 'var(--color-brand-gold-400)' : 'rgb(148 163 184)'} strokeWidth="8" strokeLinecap="round" strokeDasharray={strokeDasharray} />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-heading text-3xl text-white">{value}%</div>
    </div>
  )
}

export default AccuracyCircleGauge
