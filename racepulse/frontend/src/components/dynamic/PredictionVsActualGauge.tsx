interface PredictionVsActualGaugeProps {
  predictedRank: number
  actualRank: number
}

function PredictionVsActualGauge({ predictedRank, actualRank }: PredictionVsActualGaugeProps) {
  const isMatched = predictedRank === actualRank

  return (
    <div className={`rounded-lg border p-4 ${isMatched ? 'border-brand-gold-400/50 bg-brand-gold-400/10' : 'border-gray-400/25 bg-white/5'}`}>
      <p className="text-sm text-white/60">예측 vs 실제</p>
      <div className="mt-3 flex items-center justify-between text-center">
        <div>
          <p className="text-xs text-white/55">예측</p>
          <p className="font-heading text-3xl text-brand-gold-400">{predictedRank}위</p>
        </div>
        <span className="text-white/35">→</span>
        <div>
          <p className="text-xs text-white/55">실제</p>
          <p className="font-heading text-3xl text-white">{actualRank}위</p>
        </div>
      </div>
      <p className="mt-3 text-sm font-semibold text-white">{isMatched ? '예측 일치' : '예측 불일치'}</p>
    </div>
  )
}

export default PredictionVsActualGauge
