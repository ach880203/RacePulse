// =============================================================================
// dashboard.ts — 대시보드 관련 TypeScript 타입 정의
// =============================================================================

/** 경마장별 정확도 */
export interface MeetAccuracy {
  top1: number   // Top-1 정확도 (%)
  top3: number   // Top-3 정확도 (%)
}

/** 월별 추이 데이터 1건 */
export interface MonthlyTrend {
  month: string  // "2026-01" 형식
  top1: number
  top3: number
}

/** 전체 정확도 통계 응답 */
export interface AccuracyStats {
  totalPredictions: number
  top1Accuracy: number
  top3Accuracy: number
  last30DaysTop1: number
  byMeetCode: {
    SC: MeetAccuracy
    BU: MeetAccuracy
    JJ: MeetAccuracy
  }
  monthlyTrend: MonthlyTrend[]
}
