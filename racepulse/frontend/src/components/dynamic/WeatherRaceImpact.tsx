interface WeatherRaceImpactProps {
  // weather = 경주 당일 날씨입니다. 한글 문구로 변환해서 사용자에게 보여 줍니다.
  weather: 'CLEAR' | 'CLOUDY' | 'RAIN' | 'HEAVY_RAIN' | 'UNKNOWN'
  // weatherUncertaintySigma = Monte Carlo에서 날씨 때문에 추가된 예측 불확실성입니다.
  weatherUncertaintySigma: number
}

const weatherViewMap = {
  CLEAR: { label: '맑음', icon: '맑', impact: '예측 변동성이 낮습니다.' },
  CLOUDY: { label: '흐림', icon: '흐', impact: '중간 수준의 변동성을 반영합니다.' },
  RAIN: { label: '비', icon: '비', impact: '오늘은 예측 변동성이 높습니다.' },
  HEAVY_RAIN: { label: '강한 비', icon: '강', impact: '트랙 적합 말 확인이 필요합니다.' },
  UNKNOWN: { label: '정보 없음', icon: '?', impact: '기본 불확실성으로 계산합니다.' },
}

function WeatherRaceImpact({ weather, weatherUncertaintySigma }: WeatherRaceImpactProps) {
  const view = weatherViewMap[weather]
  const sigmaPercent = Math.max(0, weatherUncertaintySigma * 100)
  const isRainy = weather === 'RAIN' || weather === 'HEAVY_RAIN'

  return (
    <div className={`rounded-lg border p-5 ${isRainy ? 'border-brand-gold-400/35 bg-brand-gold-400/10' : 'border-white/10 bg-brand-navy-900/70'}`}>
      <div className="flex items-center gap-4">
        <span className="flex h-14 w-14 items-center justify-center rounded-lg bg-white/10 font-heading text-lg text-brand-gold-400">{view.icon}</span>
        <div>
          <p className="text-sm text-white/55">날씨 영향</p>
          <h3 className="font-heading text-2xl text-white">{view.label}</h3>
        </div>
      </div>
      <p className="mt-4 text-sm leading-6 text-white/72">{view.impact}</p>
      <div className="mt-4">
        <div className="mb-2 flex justify-between text-sm">
          <span className="text-white/60">날씨 불확실성</span>
          <span className="font-mono text-brand-gold-400">{sigmaPercent.toFixed(1)}%</span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-white/10">
          <div className="h-full rounded-full bg-brand-gold-400 transition-[width] duration-700" style={{ width: `${Math.min(100, sigmaPercent * 12)}%` }} />
        </div>
      </div>
    </div>
  )
}

export default WeatherRaceImpact
