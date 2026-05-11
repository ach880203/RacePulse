// =============================================================================
// CircularGauge.tsx — 정확도를 원형으로 표시하는 게이지 컴포넌트
// =============================================================================
// SVG(Scalable Vector Graphics)란?
//   수학적인 도형(원, 선 등)을 코드로 그리는 방식입니다.
//   이미지와 달리 어떤 크기에서도 선명하게 보입니다.
//
// 원형 게이지 원리:
//   SVG <circle>의 stroke-dasharray, stroke-dashoffset 속성을 이용합니다.
//   원의 둘레 = 2 × π × 반지름 ≈ 283px (반지름 45)
//   채워진 길이 = 둘레 × (정확도% / 100)
//   남은 길이 = 둘레 - 채워진 길이
//
// 카운트업 애니메이션:
//   useEffect + setInterval 로 0에서 실제값까지 증가시킵니다.
//   setInterval = "n밀리초마다 함수 실행"을 브라우저에 예약합니다.
// =============================================================================

// useEffect = 컴포넌트가 화면에 나타나거나 값이 바뀔 때 실행됩니다.
// useState = 현재 표시 중인 숫자 상태를 저장합니다.
import { useEffect, useState } from 'react'

interface Props {
  value: number        // 실제 정확도 값 (예: 42.5)
  label: string        // 게이지 아래 표시할 레이블 (예: "Top-1 적중률")
  size?: number        // SVG 크기(px), 기본값 140
  strokeWidth?: number // 원 테두리 두께(px), 기본값 10
}

/**
 * 정확도 값에 따라 색상을 결정합니다.
 * 70% 이상 → 골드(brand-gold), 60% 미만 → 빨간색, 그 사이 → 하얀색
 */
function getColor(value: number): string {
  if (value >= 70) return '#f5c842'   // brand-gold-400
  if (value < 60)  return '#f87171'   // red-400
  return '#e2e8f0'                     // white/85
}

function CircularGauge({ value, label, size = 140, strokeWidth = 10 }: Props) {
  // 카운트업 애니메이션용 현재 표시 값 상태
  const [displayed, setDisplayed] = useState(0)

  useEffect(() => {
    // value가 바뀔 때마다 카운트업 애니메이션을 다시 시작합니다.
    // 총 1.5초 동안 0에서 target까지 증가합니다.
    const target     = value
    const duration   = 1500  // ms
    const steps      = 60    // 총 단계 수 (60fps 기준)
    const stepTime   = duration / steps   // 한 단계당 ms
    const increment  = target / steps     // 한 단계당 증가량

    let current = 0
    const timer = setInterval(() => {
      current += increment
      if (current >= target) {
        // 목표에 도달하면 정확한 값으로 고정하고 타이머를 종료합니다.
        setDisplayed(target)
        clearInterval(timer)
      } else {
        setDisplayed(parseFloat(current.toFixed(1)))
      }
    }, stepTime)

    // 컴포넌트가 사라지면 타이머를 멈춥니다 (메모리 누수 방지)
    return () => clearInterval(timer)
  }, [value])

  // =============================================================================
  // SVG 원형 게이지 계산
  // =============================================================================
  const radius      = (size - strokeWidth) / 2          // 원의 반지름
  const center      = size / 2                           // SVG 중심 좌표
  const circumference = 2 * Math.PI * radius            // 원 전체 둘레
  // 채워진 비율에 해당하는 둘레 길이
  const filled      = (displayed / 100) * circumference
  // dashoffset = 채워진 길이만큼 앞에서부터 그립니다.
  const dashOffset  = circumference - filled

  const color = getColor(value)

  return (
    <div className="flex flex-col items-center gap-3">
      {/* SVG 원형 게이지 */}
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          // -90도 회전: SVG 기본 시작점이 3시 방향이므로 12시 방향(맨 위)으로 돌립니다.
          style={{ transform: 'rotate(-90deg)' }}
        >
          {/* 배경 원 (회색 트랙) */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="rgba(255,255,255,0.1)"
            strokeWidth={strokeWidth}
          />
          {/* 채워진 원 (정확도 비율만큼) */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"    // 끝부분을 둥글게
            strokeDasharray={circumference}
            strokeDashoffset={dashOffset}
            // CSS transition으로 부드럽게 애니메이션합니다.
            style={{ transition: 'stroke-dashoffset 0.05s ease' }}
          />
        </svg>

        {/* SVG 위에 숫자 텍스트 (absolute로 중앙 배치) */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span
            className="font-heading text-3xl font-bold tabular-nums"
            style={{ color }}
          >
            {displayed.toFixed(1)}
          </span>
          <span className="text-xs text-white/45">%</span>
        </div>
      </div>

      {/* 레이블 */}
      <p className="text-center text-sm text-white/60">{label}</p>
    </div>
  )
}

export default CircularGauge
