interface GateBiasIndicatorProps {
  // gates = 게이트별 유불리 수치입니다. 양수는 유리, 음수는 불리를 뜻합니다.
  gates: {
    gateNo: number
    bias: number
  }[]
}

function GateBiasIndicator({ gates }: GateBiasIndicatorProps) {
  return (
    <div className="rounded-lg border border-white/10 bg-brand-navy-900/70 p-5">
      <div className="mb-4">
        <p className="text-sm text-white/55">게이트 영향</p>
        <h3 className="font-heading text-2xl text-brand-gold-400">출발 위치 유불리</h3>
      </div>
      <div className="space-y-3">
        {gates.map((gate) => {
          const width = Math.min(100, Math.abs(gate.bias) * 10)
          const isPositive = gate.bias >= 0
          return (
            <div key={gate.gateNo} className="grid grid-cols-[5rem_1fr_4rem] items-center gap-3 text-sm">
              <span className="text-white/70">게이트 {gate.gateNo}</span>
              <div className="h-3 overflow-hidden rounded-full bg-white/10">
                <div
                  className={`h-full rounded-full transition-[width] duration-700 ${isPositive ? 'bg-brand-gold-400' : 'bg-slate-500'}`}
                  style={{ width: `${width}%` }}
                />
              </div>
              <span className={isPositive ? 'text-brand-gold-400' : 'text-slate-300'}>{isPositive ? '+' : ''}{gate.bias.toFixed(1)}%</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default GateBiasIndicator
