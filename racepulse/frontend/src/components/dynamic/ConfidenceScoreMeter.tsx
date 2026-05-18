import { useEffect, useState } from 'react'

interface ConfidenceScoreMeterProps {
  // score = Monte Carlo 결과의 신뢰도 점수입니다. 0~100 사이로 보정해서 표시합니다.
  score: number
}

// meterTrackColor = SVG stroke에는 Tailwind className 대신 CSS 토큰 문자열을 넘겨야 합니다.
const meterTrackColor = 'color-mix(in srgb, var(--color-white) 12%, transparent)'

function ConfidenceScoreMeter({ score }: ConfidenceScoreMeterProps) {
  const safeScore = Math.max(0, Math.min(100, score))
  const [animatedScore, setAnimatedScore] = useState(0)
  const status = safeScore <= 40 ? '데이터 부족' : safeScore <= 70 ? '보통' : '신뢰 가능'
  const statusClassName = safeScore <= 40 ? 'text-red-200' : safeScore <= 70 ? 'text-sky-200' : 'text-brand-gold-400'
  const circumference = 157
  const strokeDashoffset = circumference - (circumference * animatedScore) / 100

  useEffect(() => {
    // useEffect = 처음에는 0점에서 시작하고 실제 점수까지 움직여 변화량을 눈으로 확인하게 합니다.
    const timer = window.setTimeout(() => setAnimatedScore(safeScore), 80)
    return () => window.clearTimeout(timer)
  }, [safeScore])

  return (
    <div className="rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      <p className="text-sm text-white/55">Monte Carlo 신뢰도</p>
      <div className="mt-4 flex items-center gap-5">
        <div className="relative h-36 w-36">
          <svg viewBox="0 0 120 70" className="h-full w-full">
            <path d="M 15 60 A 45 45 0 0 1 105 60" fill="none" stroke={meterTrackColor} strokeWidth="10" strokeLinecap="round" />
            <path
              d="M 15 60 A 45 45 0 0 1 105 60"
              fill="none"
              stroke={safeScore <= 40 ? 'var(--color-red-300)' : safeScore <= 70 ? 'var(--color-sky-300)' : 'var(--color-brand-gold-400)'}
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
              className="transition-[stroke-dashoffset] duration-500 ease-out"
            />
          </svg>
          <div className="absolute inset-x-0 bottom-4 text-center">
            <p className="font-mono text-3xl font-bold text-white">{Math.round(animatedScore)}</p>
            <p className={`text-sm font-semibold ${statusClassName}`}>{status}</p>
          </div>
        </div>
        <p className="text-sm leading-6 text-white/70">
          수렴 여부, 반복 횟수, 게이트·날씨·배당 데이터 반영 여부를 합산한 점수입니다.
        </p>
      </div>
    </div>
  )
}

export default ConfidenceScoreMeter
