// =============================================================================
// CountdownTimer.tsx — 경주 시작까지 남은 시간을 실시간으로 표시하는 컴포넌트
// =============================================================================
// setInterval이란?
//   "n밀리초마다 이 함수를 반복 실행해줘"를 브라우저에 부탁하는 도구입니다.
//   예: setInterval(fn, 1000) → 1초마다 fn 함수 실행
//
// useEffect + setInterval 패턴:
//   컴포넌트가 화면에 나타날 때 타이머를 시작하고,
//   화면에서 사라질 때(return 함수) 타이머를 멈춥니다.
//   멈추지 않으면 컴포넌트가 사라진 뒤에도 메모리에서 계속 돌아가는 문제가 생깁니다.
// =============================================================================

// useEffect = 컴포넌트가 화면에 나타났을 때 실행할 코드를 등록합니다.
// useState = 남은 시간 상태를 저장합니다.
import { useEffect, useState } from 'react'

interface Props {
  // targetTime = 경주 출발 시각 ("HH:MM" 형식)
  // rcDate = 경주 날짜 ("YYYY-MM-DD" 형식)
  targetTime: string | null
  rcDate: string | null
}

/**
 * "HH:MM" 형식의 시각과 "YYYY-MM-DD" 날짜를 합쳐서 Date 객체로 변환합니다.
 */
function buildTargetDate(rcDate: string, targetTime: string): Date {
  // "2026-05-11" + "T" + "11:00" + ":00" → new Date("2026-05-11T11:00:00")
  return new Date(`${rcDate}T${targetTime}:00`)
}

/**
 * 남은 초를 "HH:MM:SS" 형식 문자열로 변환합니다.
 * 예: 3750초 → "01:02:30"
 */
function formatRemaining(seconds: number): string {
  if (seconds <= 0) return '출발!'

  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60

  // padStart(2, '0') = "9" → "09" 처럼 두 자리를 유지합니다.
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}

function CountdownTimer({ targetTime, rcDate }: Props) {
  // 남은 초를 상태로 관리합니다.
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null)

  useEffect(() => {
    // targetTime 또는 rcDate가 없으면 타이머를 실행하지 않습니다.
    if (!targetTime || !rcDate) return

    const target = buildTargetDate(rcDate, targetTime)

    // 타이머 함수: 목표 시각과 현재 시각의 차이(초)를 계산합니다.
    function tick() {
      const diff = Math.floor((target.getTime() - Date.now()) / 1000)
      setRemainingSeconds(diff)
    }

    // 컴포넌트가 처음 나타날 때 즉시 한 번 실행합니다.
    tick()

    // 이후 1초(1000ms)마다 tick을 반복 실행합니다.
    const timerId = setInterval(tick, 1000)

    // return 함수 = 컴포넌트가 화면에서 사라질 때 자동으로 실행됩니다.
    // clearInterval로 타이머를 멈추지 않으면 메모리 누수가 생깁니다.
    return () => clearInterval(timerId)
  }, [targetTime, rcDate]) // targetTime, rcDate가 바뀌면 타이머를 재시작합니다.

  if (remainingSeconds === null) return null

  const isStarted = remainingSeconds <= 0
  const label = isStarted ? '경주 시작!' : '경주 시작까지'

  return (
    <div className="flex flex-col items-center gap-2 rounded-3xl border border-white/10 bg-white/5 px-6 py-5 text-center">
      <p className="text-sm text-white/55">{label}</p>
      <p
        className={[
          'font-heading text-4xl tabular-nums',
          isStarted ? 'animate-pulse text-brand-gold-400' : 'text-white',
        ].join(' ')}
      >
        {formatRemaining(remainingSeconds)}
      </p>
    </div>
  )
}

export default CountdownTimer
