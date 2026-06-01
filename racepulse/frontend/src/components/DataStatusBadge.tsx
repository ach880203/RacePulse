// =============================================================================
// DataStatusBadge.tsx — 데이터 수집 상태를 뱃지로 표시하는 컴포넌트
// =============================================================================
// data_status 값에 따라 다른 색상과 텍스트의 뱃지를 보여줍니다.
// 운영자가 데이터 수집 현황을 화면에서 바로 파악할 수 있게 해줍니다.
// =============================================================================

import type { DataStatus } from '../types/race'

interface Props {
  status: DataStatus | undefined
}

// 상태별 뱃지 설정을 객체로 미리 정의합니다.
// 규칙 10: Tailwind 브랜드 토큰만 사용합니다.
// 상태별 뱃지 표시 설정
// COLLECTED = 백엔드에서 "수집 완료"를 의미하는 값.
// 과거에 "데이터 수집 중"으로 잘못 표기돼 완료된 경주에 깜빡이는 뱃지가 남던 버그 수정.
const STATUS_CONFIG: Record<DataStatus, { label: string; className: string; blink?: boolean }> = {
  READY: {
    label: '준비중',
    className: 'border-white/20 bg-white/8 text-white/60',
  },
  UPDATING: {
    label: '업데이트 예정',
    className: 'border-blue-400/30 bg-blue-400/10 text-blue-400',
    blink: true, // 갱신 예정 상태만 주의 환기를 위해 깜빡임
  },
  COLLECTED: {
    label: '수집 완료',
    // 완료 상태 → 초록 계열, 깜빡임 없음
    className: 'border-green-400/35 bg-green-400/10 text-green-400',
  },
  JOCKEY_CHANGED: {
    label: '기수변경',
    className: 'border-red-400/35 bg-red-400/10 text-red-400',
  },
}

function DataStatusBadge({ status }: Props) {
  // status 가 없거나 알 수 없는 값이면 아무것도 렌더링하지 않습니다.
  if (!status || !(status in STATUS_CONFIG)) return null

  const config = STATUS_CONFIG[status]

  return (
    <span
      className={[
        'rounded-full border px-3 py-1 text-xs font-medium',
        config.className,
        // 깜빡임 효과: animate-pulse = Tailwind 내장 애니메이션입니다.
        config.blink ? 'animate-pulse' : '',
      ].join(' ')}
    >
      {config.label}
    </span>
  )
}

export default DataStatusBadge
