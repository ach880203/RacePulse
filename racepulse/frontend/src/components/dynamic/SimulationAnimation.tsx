interface SimulationAnimationProps {
  running?: boolean
}

function SimulationAnimation({ running = true }: SimulationAnimationProps) {
  const horses = ['1', '2', '3', '4', '5']

  return (
    <div className="space-y-2 rounded-lg border border-white/10 bg-white/5 p-4">
      {horses.map((horse, index) => (
        <div key={horse} className="h-7 overflow-hidden rounded-full bg-white/10">
          <div
            className={`flex h-full w-12 items-center justify-center rounded-full bg-brand-gold-400 text-xs font-bold text-brand-navy-950 ${running ? 'animate-[race-run_1.6s_ease-in-out_infinite]' : ''}`}
            style={{ animationDelay: `${index * 0.12}s` }}
          >
            {horse}
          </div>
        </div>
      ))}
    </div>
  )
}

export default SimulationAnimation
