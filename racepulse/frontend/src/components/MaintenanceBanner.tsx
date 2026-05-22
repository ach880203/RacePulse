// =============================================================================
// MaintenanceBanner.tsx — 월요일 오후 점검 사전 공지 배너
// =============================================================================
// 표시 조건: 매주 월요일 14:00~23:59 KST
// 위치: App.tsx 에서 Header 위에 조건부 렌더링합니다.
// 닫기: sessionStorage에 저장 → 새 탭을 열면 다시 표시 (localStorage는 영구라 쓰지 않음)
// =============================================================================

import { useState } from 'react'

// isMaintenanceWarningTime은 src/utils/maintenanceTime.ts 에서 export합니다.
// App.tsx는 해당 유틸 파일에서 직접 import합니다.

// sessionStorage에 "배너 닫음" 상태를 저장할 때 사용하는 키
// sessionStorage = 브라우저 탭을 닫으면 삭제됨. 새 탭/새 창에서는 초기 상태로 돌아옴.
const DISMISSED_KEY = 'maintenance_banner_dismissed'

// ---------------------------------------------------------------------------
// 컴포넌트
// ---------------------------------------------------------------------------
export default function MaintenanceBanner() {
  // sessionStorage에서 닫기 상태를 읽어 초기값으로 사용합니다.
  const [dismissed, setDismissed] = useState(() => {
    try {
      return sessionStorage.getItem(DISMISSED_KEY) === 'true'
    } catch {
      // 시크릿 모드 등 sessionStorage를 사용할 수 없는 환경에서는 항상 표시합니다.
      return false
    }
  })

  // 이미 닫혔으면 아무것도 렌더링하지 않습니다.
  if (dismissed) return null

  function handleDismiss() {
    try {
      sessionStorage.setItem(DISMISSED_KEY, 'true')
    } catch {
      // sessionStorage 쓰기 실패해도 상태는 false→true로 바꿔 화면에서 숨깁니다.
    }
    setDismissed(true)
  }

  return (
    <div
      role="alert"
      aria-live="polite"
      className="flex items-center gap-3 px-4 py-2.5 text-sm text-amber-200"
      style={{
        // 어두운 앰버 배경 + 골드 좌측 라인으로 "경고성 안내" 느낌을 줍니다.
        background: '#1a1200',
        borderLeft: '4px solid #b48a1c',
      }}
    >
      <span aria-hidden="true">⚠️</span>

      <span className="flex-1">
        <strong className="font-semibold text-amber-300">점검 예정 안내</strong>
        &nbsp;— 내일 새벽 2시 ~ 6시 정기 점검이 예정되어 있습니다.
      </span>

      {/* 닫기 버튼 */}
      <button
        type="button"
        onClick={handleDismiss}
        className="ml-2 rounded p-0.5 text-amber-400/60 transition hover:text-amber-400"
        aria-label="배너 닫기"
      >
        ✕
      </button>
    </div>
  )
}
