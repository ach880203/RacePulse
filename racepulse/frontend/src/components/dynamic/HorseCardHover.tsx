import SparklineChart from './SparklineChart'

interface HorseCardHoverProps {
  name: string
  jockeyName: string
  odds: string
  recentRanks: number[]
}

function HorseCardHover({ name, jockeyName, odds, recentRanks }: HorseCardHoverProps) {
  return (
    <div className="group relative rounded-lg border border-white/10 bg-white/5 p-4 transition hover:-translate-y-1 hover:border-brand-gold-400/60">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-semibold text-white">{name}</p>
          <p className="mt-1 text-sm text-white/60">기수 {jockeyName}</p>
        </div>
        <span className="rounded-full bg-brand-gold-400/15 px-3 py-1 text-sm font-semibold text-brand-gold-400">{odds}</span>
      </div>
      <div className="pointer-events-none absolute left-4 right-4 top-full z-10 mt-3 translate-y-2 rounded-lg border border-white/10 bg-brand-navy-900 p-4 opacity-0 shadow-2xl transition group-hover:pointer-events-auto group-hover:translate-y-0 group-hover:opacity-100">
        <p className="text-sm font-semibold text-white">최근 5경주 착순</p>
        <SparklineChart ranks={recentRanks} />
      </div>
    </div>
  )
}

export default HorseCardHover
