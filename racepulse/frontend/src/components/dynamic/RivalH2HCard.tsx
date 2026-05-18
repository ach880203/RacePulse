import { useEffect, useState } from 'react'

interface RivalH2HCardProps {
  // horseAId, horseBId = API 연동 시 어떤 두 말을 비교할지 식별하는 값입니다.
  horseAId: number
  horseBId: number
  // horseAName, horseBName = 화면에 보여 줄 말 이름입니다.
  horseAName: string
  horseBName: string
  // record = 상위 페이지가 GET /ml/rivals/{horseIdA}/{horseIdB} 결과를 넣어 줄 수 있는 직접 맞대결 전적입니다.
  record?: {
    horseAWins: number
    horseBWins: number
    draws?: number
    lastRaceDate?: string
    lastWinnerName?: string
  }
}

function RivalH2HCard({ horseAId, horseBId, horseAName, horseBName, record }: RivalH2HCardProps) {
  const [flipped, setFlipped] = useState(false)
  const [animatedTotal, setAnimatedTotal] = useState(0)
  const safeRecord = record ?? { horseAWins: 3, horseBWins: 2, draws: 0, lastRaceDate: '최근 맞대결 없음', lastWinnerName: horseAName }
  const totalMatches = safeRecord.horseAWins + safeRecord.horseBWins + (safeRecord.draws ?? 0)
  const leaderName = safeRecord.horseAWins >= safeRecord.horseBWins ? horseAName : horseBName

  useEffect(() => {
    // useEffect = 컴포넌트가 화면에 보인 뒤 숫자 카운트업을 시작해 정적인 카드보다 집중도를 높입니다.
    const timer = window.setTimeout(() => setAnimatedTotal(totalMatches), 90)
    return () => window.clearTimeout(timer)
  }, [totalMatches])

  return (
    <button
      type="button"
      onClick={() => setFlipped((current) => !current)}
      className="group block w-full text-left [perspective:900px]"
      aria-label={`${horseAName}와 ${horseBName} 맞대결 카드 뒤집기`}
    >
      <div className={`relative min-h-52 transition-transform duration-700 [transform-style:preserve-3d] ${flipped ? '[transform:rotateY(180deg)]' : ''}`}>
        <div className="absolute inset-0 rounded-lg border border-brand-gold-400/25 bg-brand-navy-900/85 p-5 shadow-xl shadow-black/20 [backface-visibility:hidden]">
          <div className="flex items-center justify-between text-xs text-white/55">
            <span>맞대결 비교</span>
            <span>번호 {horseAId} · {horseBId}</span>
          </div>
          <div className="mt-7 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
            <p className="truncate font-heading text-2xl text-white">{horseAName}</p>
            <span className="rounded-full border border-brand-gold-400/35 px-3 py-1 font-mono text-sm text-brand-gold-400">대</span>
            <p className="truncate text-right font-heading text-2xl text-white">{horseBName}</p>
          </div>
          <p className="mt-6 text-center text-sm text-white/70">카드를 누르면 과거 전적을 확인합니다.</p>
          <p className="mt-3 text-center font-mono text-3xl text-brand-gold-400">{animatedTotal}전</p>
        </div>

        <div className="absolute inset-0 rounded-lg border border-brand-gold-400/35 bg-brand-navy-900 p-5 shadow-xl shadow-black/25 [backface-visibility:hidden] [transform:rotateY(180deg)]">
          <p className="text-xs text-white/55">직접 맞대결 전적</p>
          <p className="mt-4 font-heading text-2xl text-white">
            {horseAName} {safeRecord.horseAWins}승 · {horseBName} {safeRecord.horseBWins}승
          </p>
          <p className="mt-3 text-sm text-brand-gold-400">우세: {leaderName}</p>
          <div className="mt-5 rounded-lg bg-white/5 p-3 text-sm text-white/72">
            <p>마지막 대결: {safeRecord.lastRaceDate ?? '정보 없음'}</p>
            <p className="mt-1">마지막 승자: {safeRecord.lastWinnerName ?? '정보 없음'}</p>
          </div>
        </div>
      </div>
    </button>
  )
}

export default RivalH2HCard
