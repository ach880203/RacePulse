interface ConditionColorBadgeProps {
  grade: string
}

const gradeClassMap: Record<string, string> = {
  최하: 'bg-red-500/18 text-red-200 ring-red-400/40',
  하: 'bg-orange-500/18 text-orange-200 ring-orange-400/40',
  중: 'bg-yellow-500/18 text-yellow-100 ring-yellow-300/40',
  상: 'bg-lime-500/18 text-lime-100 ring-lime-300/40',
  최상: 'bg-green-500/18 text-green-100 ring-green-300/40',
}

function ConditionColorBadge({ grade }: ConditionColorBadgeProps) {
  const badgeClass = gradeClassMap[grade] ?? gradeClassMap.중

  return (
    <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ring-1 ${badgeClass}`}>
      {grade}
    </span>
  )
}

export default ConditionColorBadge
