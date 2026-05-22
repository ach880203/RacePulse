// =============================================================================
// maintenanceTime.ts — 점검 시간 판별 유틸리티
// =============================================================================
// MaintenancePage.tsx와 MaintenanceBanner.tsx에서 함께 사용하는 함수들입니다.
// React Fast Refresh 규칙상 컴포넌트 파일에서 함수를 export하면 경고가 발생하므로
// 별도 유틸 파일로 분리합니다.
// =============================================================================

/**
 * 매주 화요일 02:00~06:00 KST 인지 판별합니다.
 * 이 시간이면 MaintenancePage가 전체 화면을 대체합니다.
 *
 * getDay() 반환값: 0=일, 1=월, 2=화, 3=수, 4=목, 5=금, 6=토
 * KST = UTC + 9시간 (9 * 60 * 60 * 1000 밀리초)
 */
export function isMaintenanceTime(): boolean {
  const now = new Date()
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  return kst.getDay() === 2 && kst.getHours() >= 2 && kst.getHours() < 6
}

/**
 * 매주 월요일 14:00~23:59 KST 인지 판별합니다.
 * 이 시간이면 MaintenanceBanner가 헤더 위에 표시됩니다.
 */
export function isMaintenanceWarningTime(): boolean {
  const now = new Date()
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  return kst.getDay() === 1 && kst.getHours() >= 14
}
