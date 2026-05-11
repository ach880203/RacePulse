import { useEffect, useState } from 'react'

interface RaceStartCountdownProps {
  startTime: string
}

function RaceStartCountdown({ startTime }: RaceStartCountdownProps) {
  const [remain, setRemain] = useState(() => Date.parse(startTime) - Date.now())
  const isSoon = remain > 0 && remain <= 60 * 60 * 1000

  useEffect(() => {
    const timer = window.setInterval(() => setRemain(Date.parse(startTime) - Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [startTime])

  const totalSeconds = Math.max(0, Math.floor(remain / 1000))
  const days = Math.floor(totalSeconds / 86400)
  const hours = Math.floor((totalSeconds % 86400) / 3600).toString().padStart(2, '0')
  const minutes = Math.floor((totalSeconds % 3600) / 60).toString().padStart(2, '0')
  const seconds = (totalSeconds % 60).toString().padStart(2, '0')

  return (
    <div className={`rounded-lg border p-4 ${isSoon ? 'border-brand-gold-400/50 bg-brand-gold-400/10' : 'border-white/10 bg-white/5'}`}>
      <p className="text-sm text-white/60">경주 시작까지</p>
      <p className="mt-2 font-heading text-3xl text-white">{days > 0 ? `D-${days}` : `${hours}:${minutes}:${seconds}`}</p>
    </div>
  )
}

export default RaceStartCountdown
