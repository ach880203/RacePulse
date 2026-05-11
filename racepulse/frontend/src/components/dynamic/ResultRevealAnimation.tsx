import { useEffect, useState } from 'react'

interface ResultRevealAnimationProps {
  results: { rank: number; horseName: string }[]
}

function ResultRevealAnimation({ results }: ResultRevealAnimationProps) {
  const orderedResults = [...results].sort((a, b) => b.rank - a.rank)
  const [visibleCount, setVisibleCount] = useState(0)

  useEffect(() => {
    const timer = window.setInterval(() => {
      setVisibleCount((count) => Math.min(count + 1, orderedResults.length))
    }, 450)
    return () => window.clearInterval(timer)
  }, [orderedResults.length])

  return (
    <div className="space-y-2">
      {orderedResults.slice(0, visibleCount).map((result) => (
        <div key={result.rank} className="animate-[result-pop_0.35s_ease-out_both] rounded-lg border border-white/10 bg-white/5 p-3">
          <span className="mr-3 font-heading text-xl text-brand-gold-400">{result.rank}위</span>
          <span className="font-semibold text-white">{result.horseName}</span>
        </div>
      ))}
    </div>
  )
}

export default ResultRevealAnimation
