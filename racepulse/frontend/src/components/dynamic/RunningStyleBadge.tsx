interface RunningStyleBadgeProps {
  // style = 말이 경주를 풀어가는 대표 주행 유형입니다.
  style: 'LEADER' | 'STALKER' | 'CLOSER' | 'PRESSER' | 'UNKNOWN'
  // confidence = 0~1 사이 신뢰도입니다. 낮으면 물음표를 붙여 분석 불확실성을 보여 줍니다.
  confidence: number
  // size = 같은 배지를 표/카드/상세 화면에서 다르게 쓰기 위한 크기 옵션입니다.
  size?: 'sm' | 'md' | 'lg'
}

const styleViewMap = {
  LEADER: { label: '선행', icon: '선', className: 'border-brand-gold-400/45 bg-brand-gold-400/15 text-brand-gold-400' },
  STALKER: { label: '추적', icon: '추', className: 'border-sky-300/45 bg-sky-300/12 text-sky-200' },
  CLOSER: { label: '추입', icon: '입', className: 'border-fuchsia-300/45 bg-fuchsia-300/12 text-fuchsia-200' },
  PRESSER: { label: '압박', icon: '압', className: 'border-emerald-300/45 bg-emerald-300/12 text-emerald-200' },
  UNKNOWN: { label: '분석중', icon: '?', className: 'border-slate-300/30 bg-slate-300/10 text-slate-200' },
}

const sizeClassMap = {
  sm: 'px-2 py-1 text-xs',
  md: 'px-3 py-1.5 text-sm',
  lg: 'px-4 py-2 text-base',
}

function RunningStyleBadge({ style, confidence, size = 'md' }: RunningStyleBadgeProps) {
  const view = styleViewMap[style]
  const isLowConfidence = confidence < 0.5

  return (
    <span className={`inline-flex items-center gap-2 rounded-full border font-semibold ${view.className} ${sizeClassMap[size]}`}>
      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white/10 font-mono text-[0.7em]">{isLowConfidence ? '?' : view.icon}</span>
      <span>{view.label}{isLowConfidence ? '?' : ''}</span>
    </span>
  )
}

export default RunningStyleBadge
