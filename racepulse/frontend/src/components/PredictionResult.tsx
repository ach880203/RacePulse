// =============================================================================
// PredictionResult.tsx — 예측 순위 vs 실제 순위 비교 컴포넌트
// =============================================================================
// 적중 = 예측 1위가 실제 1위 (Top-1) 또는 3위 이내 (Top-3)
// 미적중 = 예측과 실제 결과가 다름
// =============================================================================

interface Props {
  raceName:      string          // 경주명
  predictedRank: number          // 예측 착순 (보통 1위)
  actualRank:    number | null   // 실제 착순
  horseName:     string          // 말 이름
  meetCode:      string          // 경마장 코드
}

const MEET_LABELS: Record<string, string> = {
  SC: '서울', BU: '부산', JJ: '제주',
}

function PredictionResult({
  raceName, predictedRank, actualRank, horseName, meetCode,
}: Props) {
  // Top-1 적중: 예측 1위가 실제 1위
  const isTop1Hit = actualRank === 1
  // Top-3 적중: 예측 1위가 실제 3위 이내
  const isTop3Hit = actualRank !== null && actualRank <= 3

  return (
    <div className="flex items-center justify-between gap-4 rounded-2xl border border-white/8 bg-white/4 px-4 py-3">
      {/* 경주 정보 */}
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-white">{raceName}</p>
        <p className="text-xs text-white/45">{MEET_LABELS[meetCode] ?? meetCode} · {horseName}</p>
      </div>

      {/* 예측 vs 실제 비교 */}
      <div className="flex items-center gap-3 text-sm">
        {/* 예측 착순 */}
        <div className="text-center">
          <p className="text-xs text-white/40">예측</p>
          <p className="font-heading text-lg text-white">{predictedRank}위</p>
        </div>

        {/* 화살표 */}
        <span className="text-white/25">→</span>

        {/* 실제 착순 */}
        <div className="text-center">
          <p className="text-xs text-white/40">실제</p>
          <p
            className={[
              'font-heading text-lg',
              isTop1Hit
                ? 'text-brand-gold-400'  // 1위 적중: 골드
                : isTop3Hit
                  ? 'text-green-400'     // Top-3 적중: 초록
                  : 'text-red-400',      // 미적중: 빨강
            ].join(' ')}
          >
            {actualRank != null ? `${actualRank}위` : '?'}
          </p>
        </div>

        {/* 적중 아이콘 */}
        <div className="w-6 text-center">
          {isTop1Hit ? (
            // 1위 적중 — 골드 체크
            <span className="text-lg text-brand-gold-400" title="1순위 적중">✓</span>
          ) : isTop3Hit ? (
            // Top-3 적중 — 초록 체크
            <span className="text-lg text-green-400" title="3순위권 적중">✓</span>
          ) : (
            // 미적중 — 빨간 X
            <span className="text-lg text-red-400" title="미적중">✗</span>
          )}
        </div>
      </div>
    </div>
  )
}

export default PredictionResult
