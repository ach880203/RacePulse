import { useEffect, useState } from 'react'

// Toast의 종류 — 색상과 아이콘을 결정합니다.
export type ToastType = 'success' | 'error' | 'warning' | 'info'

export type ToastProps = {
  message: string
  type?: ToastType
  // 자동으로 사라지기까지 걸리는 시간 (ms), 0이면 자동 닫힘 없음
  duration?: number
  onClose: () => void
}

// type별 스타일 매핑
const STYLES: Record<ToastType, { bar: string; icon: string; label: string }> = {
  success: { bar: 'bg-emerald-500',      icon: '✓', label: '성공' },
  error:   { bar: 'bg-red-500',          icon: '✕', label: '오류' },
  warning: { bar: 'bg-brand-gold-500',   icon: '!', label: '경고' },
  info:    { bar: 'bg-blue-500',         icon: 'i', label: '안내' },
}

export default function Toast({ message, type = 'info', duration = 3000, onClose }: ToastProps) {
  const [visible, setVisible] = useState(false)

  // 마운트 직후 애니메이션 시작, duration 후 페이드 아웃
  useEffect(() => {
    const showTimer = setTimeout(() => setVisible(true), 10)
    if (duration === 0) return () => clearTimeout(showTimer)

    const hideTimer = setTimeout(() => {
      setVisible(false)
      // 페이드 아웃(300ms) 후 실제 제거
      setTimeout(onClose, 300)
    }, duration)

    return () => {
      clearTimeout(showTimer)
      clearTimeout(hideTimer)
    }
  }, [duration, onClose])

  const { bar, icon } = STYLES[type]

  return (
    <div
      className={`flex w-80 items-start gap-3 overflow-hidden rounded bg-brand-navy-900 shadow-xl ring-1 ring-white/10 transition-all duration-300 ${
        visible ? 'translate-y-0 opacity-100' : 'translate-y-2 opacity-0'
      }`}
    >
      {/* 왼쪽 컬러 바 — type을 시각적으로 구분합니다 */}
      <div className={`w-1 self-stretch ${bar}`} />

      <div className="flex flex-1 items-start gap-2 py-3 pr-3">
        {/* 아이콘 */}
        <span className={`mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white ${bar}`}>
          {icon}
        </span>

        {/* 메시지 */}
        <p className="text-sm leading-snug text-white/90">{message}</p>
      </div>

      {/* 닫기 버튼 */}
      <button
        onClick={() => { setVisible(false); setTimeout(onClose, 300) }}
        className="py-3 pr-3 text-white/30 transition hover:text-white/70"
        aria-label="닫기"
      >
        ✕
      </button>
    </div>
  )
}
