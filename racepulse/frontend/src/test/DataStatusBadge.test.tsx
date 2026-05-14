// =============================================================================
// DataStatusBadge.test.tsx — 데이터 상태 뱃지 컴포넌트 테스트
// =============================================================================
// 테스트 라이브러리:
//   - Vitest   : 테스트 실행기 (describe, it, expect)
//   - @testing-library/react : React 컴포넌트를 실제 DOM에 렌더링
//   - @testing-library/jest-dom : toBeInTheDocument 등 DOM 전용 Matcher
//
// 핵심 원칙: "사용자가 보는 것"을 테스트합니다.
//   구현 세부사항(className, CSS) 보다 텍스트/역할 기반으로 검증합니다.
// =============================================================================

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import DataStatusBadge from '../components/DataStatusBadge'

describe('DataStatusBadge', () => {

  // =========================================================================
  // 정상 렌더링 — 각 status 값에 맞는 텍스트가 표시되는지
  // =========================================================================

  it('READY → "준비중" 텍스트 표시', () => {
    render(<DataStatusBadge status="READY" />)
    // screen.getByText = DOM에서 해당 텍스트를 가진 요소를 찾습니다.
    // 없으면 테스트가 즉시 실패합니다.
    expect(screen.getByText('준비중')).toBeInTheDocument()
  })

  it('UPDATING → "업데이트 예정" 텍스트 표시', () => {
    render(<DataStatusBadge status="UPDATING" />)
    expect(screen.getByText('업데이트 예정')).toBeInTheDocument()
  })

  it('COLLECTED → "데이터 수집 중" 텍스트 표시', () => {
    render(<DataStatusBadge status="COLLECTED" />)
    expect(screen.getByText('데이터 수집 중')).toBeInTheDocument()
  })

  it('JOCKEY_CHANGED → "기수변경" 텍스트 표시', () => {
    render(<DataStatusBadge status="JOCKEY_CHANGED" />)
    expect(screen.getByText('기수변경')).toBeInTheDocument()
  })

  // =========================================================================
  // 엣지 케이스 — 잘못된 입력 시 아무것도 렌더링하지 않아야 함
  // =========================================================================

  it('status=undefined → 아무것도 렌더링하지 않음', () => {
    const { container } = render(<DataStatusBadge status={undefined} />)
    // container.firstChild = 렌더링된 최상위 DOM 노드
    // null 이면 아무것도 렌더링되지 않은 것입니다.
    expect(container.firstChild).toBeNull()
  })

  // =========================================================================
  // 스타일 계약 — FE-BE 간 약속된 색상/애니메이션 확인
  // =========================================================================

  it('COLLECTED → animate-pulse 클래스 적용 (깜빡임 효과)', () => {
    render(<DataStatusBadge status="COLLECTED" />)
    const badge = screen.getByText('데이터 수집 중')
    // 데이터 수집 중 상태는 유저가 "지금 뭔가 진행 중"임을 알 수 있어야 합니다.
    expect(badge.className).toContain('animate-pulse')
  })

  it('READY → animate-pulse 클래스 없음 (깜빡임 없음)', () => {
    render(<DataStatusBadge status="READY" />)
    const badge = screen.getByText('준비중')
    expect(badge.className).not.toContain('animate-pulse')
  })

  it('JOCKEY_CHANGED → 빨간색 클래스 적용', () => {
    render(<DataStatusBadge status="JOCKEY_CHANGED" />)
    const badge = screen.getByText('기수변경')
    // 기수변경은 유저에게 위험 신호이므로 빨간색이어야 합니다.
    expect(badge.className).toContain('red')
  })

  // =========================================================================
  // 접근성 — span 태그로 렌더링되는지
  // =========================================================================

  it('span 태그로 렌더링됨', () => {
    render(<DataStatusBadge status="READY" />)
    const badge = screen.getByText('준비중')
    expect(badge.tagName).toBe('SPAN')
  })
})
