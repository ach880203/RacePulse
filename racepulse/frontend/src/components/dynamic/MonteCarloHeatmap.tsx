interface MonteCarloHeatmapProps {
  // horses = Monte Carlo 결과의 말별 순위 확률입니다. 1~5위 확률을 색 농도로 보여 줍니다.
  horses: {
    horseName: string
    ranks: number[]
  }[]
}

function probabilityCellClass(probability: number) {
  if (probability >= 30) return 'bg-brand-gold-500 text-brand-navy-950'
  if (probability >= 20) return 'bg-brand-gold-400/80 text-brand-navy-950'
  if (probability >= 10) return 'bg-brand-gold-400/35 text-white'
  if (probability > 0) return 'bg-brand-navy-800 text-white/80'
  return 'bg-brand-navy-950 text-white/45'
}

function MonteCarloHeatmap({ horses }: MonteCarloHeatmapProps) {
  const rankLabels = ['1위', '2위', '3위', '4위', '5위']

  return (
    <div className="overflow-x-auto rounded-lg border border-white/10 bg-brand-navy-900/70 p-4">
      <div className="min-w-[560px]">
        <div className="grid grid-cols-[9rem_repeat(5,1fr)] gap-2 text-xs text-white/55">
          <span>말 이름</span>
          {rankLabels.map((label) => (
            <span key={label} className="text-center">{label}</span>
          ))}
        </div>
        <div className="mt-3 space-y-2">
          {horses.map((horse) => (
            <div key={horse.horseName} className="grid grid-cols-[9rem_repeat(5,1fr)] gap-2">
              <span className="truncate rounded bg-white/5 px-3 py-2 text-sm text-white">{horse.horseName}</span>
              {rankLabels.map((label, index) => {
                const probability = Math.max(0, Math.min(100, horse.ranks[index] ?? 0))
                return (
                  <span
                    key={`${horse.horseName}-${label}`}
                    className={`rounded px-2 py-2 text-center font-mono text-sm transition hover:ring-2 hover:ring-brand-gold-400/45 ${probabilityCellClass(probability)}`}
                    title={`${horse.horseName} ${label} 확률 ${probability.toFixed(1)}%`}
                  >
                    {probability.toFixed(1)}%
                  </span>
                )
              })}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default MonteCarloHeatmap
