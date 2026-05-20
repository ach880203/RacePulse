// =============================================================================
// MaintenancePage.tsx — 정기 점검 중 전체 화면 (매주 화요일 02:00~06:00 KST)
// =============================================================================
// 이 페이지는 App.tsx에서 isMaintenanceTime() 이 true 일 때 전체 화면을 대체합니다.
// 라우터 바깥에서 렌더링되므로 어느 URL로 접속해도 이 화면이 보입니다.
// =============================================================================

import { useEffect, useState } from 'react'

// ---------------------------------------------------------------------------
// 화요일 02:00~06:00 KST 판별
// ---------------------------------------------------------------------------
// getDay() 반환값: 0=일요일, 1=월요일, 2=화요일, 3=수요일, 4=목요일, 5=금요일, 6=토요일
// KST = UTC + 9시간 (9 * 60 * 60 * 1000 밀리초)
export function isMaintenanceTime(): boolean {
  const now = new Date()
  // UTC 기준 now에 9시간을 더해 KST 시각을 구합니다.
  // 예: UTC 17:30 → KST 02:30
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  return kst.getDay() === 2 && kst.getHours() >= 2 && kst.getHours() < 6
}

// 오전 6:00 KST까지 남은 시간을 밀리초로 계산합니다.
function getRemainingMs(): number {
  const now = new Date()
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  // 오늘(KST 기준) 06:00:00 시각 생성
  const end = new Date(kst)
  end.setHours(6, 0, 0, 0)
  return Math.max(0, end.getTime() - kst.getTime())
}

// 밀리초를 HH:MM:SS 형식으로 변환합니다.
// String.padStart(2, '0') = "9" → "09" 처럼 한 자리 숫자 앞에 0을 붙입니다.
function formatCountdown(ms: number): string {
  const h = Math.floor(ms / 3_600_000)
  const m = Math.floor((ms % 3_600_000) / 60_000)
  const s = Math.floor((ms % 60_000) / 1_000)
  return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
}

// ---------------------------------------------------------------------------
// 컴포넌트
// ---------------------------------------------------------------------------
export default function MaintenancePage() {
  // 초기값: 현재 남은 시간을 계산해서 설정합니다.
  const [remaining, setRemaining] = useState(() => getRemainingMs())

  useEffect(() => {
    // 1초마다 남은 시간을 다시 계산해 카운트다운이 실시간으로 줄어들게 합니다.
    const timer = setInterval(() => setRemaining(getRemainingMs()), 1_000)
    // 컴포넌트가 화면에서 사라질 때 타이머를 정리합니다. (메모리 누수 방지)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-8 bg-brand-navy-950 px-6 text-center">

      {/* 로고 — 골드 글로우 효과 */}
      <div className="flex flex-col items-center gap-3">
        <span
          className="font-heading text-4xl font-bold tracking-wide text-brand-gold-400"
          style={{ textShadow: '0 0 24px rgba(212,168,67,0.55)' }}
        >
          RacePulse
        </span>
        {/* 로고 아래 얇은 골드 구분선 */}
        <div className="h-px w-32 bg-gradient-to-r from-transparent via-brand-gold-500/60 to-transparent" />
      </div>

      {/* 점검 아이콘 — animate-pulse 로 점검 중 느낌을 줍니다 */}
      <div className="animate-pulse text-6xl" aria-hidden="true">🔧</div>

      {/* 메인 안내 문구 */}
      <div className="flex flex-col gap-3">
        <h1 className="font-heading text-3xl font-semibold text-white">
          정기 점검 중입니다
        </h1>
        <p className="leading-relaxed text-white/55">
          매주 화요일 02:00 ~ 06:00
          <br />
          서비스를 더 잘 만들기 위해 잠시 점검 중입니다.
        </p>
      </div>

      {/* 카운트다운 타이머 */}
      <div className="flex flex-col items-center gap-1.5">
        <p className="text-xs text-white/40">완료 예정까지</p>
        {/* JetBrains Mono(font-mono)로 숫자가 고정폭이 되어 떨림 없이 표시됩니다 */}
        <span
          className="font-mono text-5xl font-bold tabular-nums text-brand-gold-400"
          style={{ textShadow: '0 0 12px rgba(212,168,67,0.35)' }}
        >
          {formatCountdown(remaining)}
        </span>
        <p className="text-xs text-white/30">오전 6:00 완료 예정 (KST)</p>
      </div>

      <div className="h-px w-24 bg-brand-gold-500/25" />

      {/* 이전 경주 결과 보기 링크 */}
      <a
        href="/races?status=COMPLETED"
        className="rounded border border-brand-gold-500/50 px-6 py-2.5 text-sm font-medium text-brand-gold-400 transition hover:bg-brand-gold-500/10"
      >
        이전 경주 결과 보기 →
      </a>

    </div>
  )
}
