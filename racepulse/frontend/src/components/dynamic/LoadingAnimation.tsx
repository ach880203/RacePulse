function LoadingAnimation() {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-4 rounded-lg border border-white/10 bg-white/5">
      <div className="relative h-16 w-64 overflow-hidden rounded-full bg-white/10">
        <div className="absolute left-0 top-3 flex h-10 w-10 animate-[race-run_1.25s_ease-in-out_infinite] items-center justify-center rounded-full bg-brand-gold-400 text-sm font-bold text-brand-navy-950">
          말
        </div>
      </div>
      <p className="text-sm text-white/65">데이터를 불러오는 중입니다</p>
      <div className="h-2 w-40 overflow-hidden rounded-full bg-white/10">
        <div className="h-full w-1/2 animate-[loading-grow_1.2s_ease-in-out_infinite] rounded-full bg-brand-gold-400" />
      </div>
    </div>
  )
}

export default LoadingAnimation
