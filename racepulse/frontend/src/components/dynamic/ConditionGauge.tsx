import { useEffect, useState } from 'react'

type ConditionGrade = '최하' | '하' | '중' | '상' | '최상'

interface ConditionGaugeProps {
  grade: ConditionGrade
  orientation?: 'horizontal' | 'vertical'
}

const gradePercentMap: Record<ConditionGrade, number> = {
  최하: 20,
  하: 40,
  중: 60,
  상: 80,
  최상: 100,
}

const gradeColorMap: Record<ConditionGrade, string> = {
  최하: 'bg-red-400',
  하: 'bg-orange-400',
  중: 'bg-yellow-300',
  상: 'bg-lime-300',
  최상: 'bg-green-400',
}

function ConditionGauge({ grade, orientation = 'horizontal' }: ConditionGaugeProps) {
  const [value, setValue] = useState(0)
  const targetValue = gradePercentMap[grade]

  useEffect(() => {
    const timer = window.setTimeout(() => setValue(targetValue), 80)
    return () => window.clearTimeout(timer)
  }, [targetValue])

  if (orientation === 'vertical') {
    return (
      <div className="flex h-40 w-16 flex-col items-center justify-end gap-2 rounded-lg border border-white/10 bg-white/5 p-3">
        <div className="flex h-full w-4 items-end overflow-hidden rounded-full bg-white/10">
          <div className={`w-full rounded-full transition-[height] duration-700 ${gradeColorMap[grade]}`} style={{ height: `${value}%` }} />
        </div>
        <span className="text-xs font-semibold text-white">{grade}</span>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-white/10 bg-white/5 p-4">
      <div className="mb-3 flex items-center justify-between text-sm">
        <span className="text-white/65">컨디션 게이지</span>
        <span className="font-semibold text-white">{grade}</span>
      </div>
      <div className="h-4 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full transition-[width] duration-700 ${gradeColorMap[grade]}`} style={{ width: `${value}%` }} />
      </div>
    </div>
  )
}

export default ConditionGauge
