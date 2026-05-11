// =============================================================================
// weather.ts — 날씨 관련 TypeScript 타입 정의
// =============================================================================

/** 날씨 예보 1건 (ML 서버 /weather/{meetCode}/{date} 응답) */
export interface WeatherForecast {
  meetCode: string
  forecastDate: string
  tempMin: number | null
  tempMax: number | null
  precipitationProb: number | null  // 강수확률 (%)
  windSpeed: number | null          // 풍속 (m/s)
  condition: string | null          // 맑음/비/눈 등
  source: string
  updatedAt: string
}
