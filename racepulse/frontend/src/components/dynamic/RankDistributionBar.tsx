interface RankDistributionBarProps {
  // horses = Monte Carlo 결과의 순위 분포입니다. 1위만 보지 않고 전체 분포를 한 줄로 비교합니다.
  horses: {
    horseName: string
    distribution: {
      first: number
      second: number
      third: number
      fourthPlus: number
    }
  }[]
}

function RankDistributionBar({ horses }: RankDistributionBarProps) {
  return (
    <div className="space-y-4 rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      {horses.map((horse) => {
        const total = Math.max(1, horse.distribution.first + horse.distribution.second + horse.distribution.third + horse.distribution.fourthPlus)
        const firstWidth = (horse.distribution.first / total) * 100
        const secondWidth = (horse.distribution.second / total) * 100
        const thirdWidth = (horse.distribution.third / total) * 100
        const fourthWidth = (horse.distribution.fourthPlus / total) * 100

        return (
          <div key={horse.horseName}>
            <div className="mb-2 flex flex-wrap items-center justify-between gap-2 text-sm">
              <span className="font-semibold text-white">{horse.horseName}</span>
              <span className="font-mono text-white/62">
                1위 {horse.distribution.first}% 2위 {horse.distribution.second}% 3위 {horse.distribution.third}% 4위+ {horse.distribution.fourthPlus}%
              </span>
            </div>
            <div className="flex h-5 overflow-hidden rounded-full bg-white/10">
              <div className="bg-brand-gold-500" style={{ width: `${firstWidth}%` }} title="1위 확률" />
              <div className="bg-brand-gold-400" style={{ width: `${secondWidth}%` }} title="2위 확률" />
              <div className="bg-brand-navy-800" style={{ width: `${thirdWidth}%` }} title="3위 확률" />
              <div className="bg-brand-navy-950" style={{ width: `${fourthWidth}%` }} title="4위 이하 확률" />
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default RankDistributionBar
