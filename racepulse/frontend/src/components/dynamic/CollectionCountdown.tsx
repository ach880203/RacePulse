import { useEffect, useState } from 'react'

interface CollectionCountdownProps {
  nextUpdateAt: string
  dataStatus?: string
}

function formatRemain(milliseconds: number) {
  const seconds = Math.max(0, Math.floor(milliseconds / 1000))
  const hours = Math.floor(seconds / 3600).toString().padStart(2, '0')
  const minutes = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0')
  const remainSeconds = (seconds % 60).toString().padStart(2, '0')
  return `${hours}:${minutes}:${remainSeconds}`
}

function CollectionCountdown({ nextUpdateAt, dataStatus = 'READY' }: CollectionCountdownProps) {
  const [remain, setRemain] = useState(() => Date.parse(nextUpdateAt) - Date.now())

  useEffect(() => {
    const timer = window.setInterval(() => setRemain(Date.parse(nextUpdateAt) - Date.now()), 1000)
    return () => window.clearInterval(timer)
  }, [nextUpdateAt])

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <p className="text-sm text-white/60">다음 수집까지</p>
      <p className="mt-2 font-heading text-3xl text-brand-gold-400">{formatRemain(remain)}</p>
      <span className="mt-3 inline-flex rounded-full bg-white/10 px-3 py-1 text-xs text-white/70">상태 {dataStatus}</span>
    </div>
  )
}

export default CollectionCountdown
