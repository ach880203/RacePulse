// =============================================================================
// setup.ts — Vitest 전역 설정
// =============================================================================
// 모든 테스트 파일 실행 전에 한 번 실행됩니다.
// @testing-library/jest-dom 의 커스텀 Matcher를 등록합니다.
//
// 커스텀 Matcher 예시:
//   expect(element).toBeInTheDocument()  — DOM에 존재하는지
//   expect(element).toHaveTextContent()  — 텍스트 내용 확인
//   expect(element).toBeVisible()        — 화면에 보이는지
// =============================================================================
import '@testing-library/jest-dom'
