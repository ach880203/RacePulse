// =============================================================================
// DashboardPage.tsx — ML 예측 정확도 대시보드 페이지
// 라우트: /dashboard
// =============================================================================
// Recharts 컴포넌트 설명:
//   ResponsiveContainer = 부모 너비에 맞춰 자동으로 크기 조절
//   LineChart           = 꺾은선 그래프 (추이 분석에 사용)
//   BarChart            = 막대 그래프 (비교 분석에 사용)
//   Line/Bar            = 실제 데이터를 시각화하는 요소
//   XAxis/YAxis         = X축, Y축 설정
//   Tooltip             = 마우스 오버 시 데이터 말풍선
//   Legend              = 범례 (어떤 색이 무엇인지)
//   CartesianGrid       = 배경 격자선 (가독성 향상)
// =============================================================================

import Layout from '../components/layout/Layout'
import CircularGauge from '../components/CircularGauge'
import PredictionResult from '../components/PredictionResult'
import { useAccuracyStats } from '../hooks/useDashboard'

import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis,
  CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'

// 경마장 코드 → 한글 이름
const MEET_LABELS: Record<string, string> = {
  SC: '서울', BU: '부산', JJ: '제주',
}

// Recharts 공통 툴팁 스타일
const tooltipStyle = {
  contentStyle: {
    background: '#0d1628',
    border: '1px solid rgba(255,255,255,0.1)',
    borderRadius: '0.75rem',
    color: '#fff',
    fontSize: '0.75rem',
  },
}

// 데모 예측 목록 (predictions API가 아직 없으므로 정적 데이터 사용)
// TODO: [Phase 3] predictions API 연동 후 실제 데이터로 교체
const DEMO_PREDICTIONS = [
  { raceName: '서울 3경주', predictedRank: 1, actualRank: 1, horseName: '천하무적', meetCode: 'SC' },
  { raceName: '부산 5경주', predictedRank: 1, actualRank: 2, horseName: '질풍가도', meetCode: 'BU' },
  { raceName: '서울 7경주', predictedRank: 1, actualRank: 1, horseName: '황금마차', meetCode: 'SC' },
  { raceName: '제주 2경주', predictedRank: 1, actualRank: 4, horseName: '청풍명월', meetCode: 'JJ' },
  { raceName: '부산 3경주', predictedRank: 1, actualRank: 3, horseName: '번개돌풍', meetCode: 'BU' },
]

function DashboardPage() {
  const { data: stats, isLoading, isError } = useAccuracyStats()

  // 경마장별 정확도를 BarChart 형식으로 변환
  const meetData = stats
    ? Object.entries(stats.byMeetCode).map(([code, acc]) => ({
        name: MEET_LABELS[code] ?? code,
        'Top-1': acc.top1,
        'Top-3': acc.top3,
      }))
    : []

  return (
    <Layout>
      <div className="flex flex-col gap-10">
        {/* 페이지 헤더 */}
        <section className="space-y-2">
          <p className="text-sm tracking-[0.2em] text-brand-gold-400">PREDICTION SCORE</p>
          <h1 className="font-heading text-4xl text-white">예측 정확도 대시보드</h1>
          <p className="text-sm text-white/50">
            ML 모델의 누적 예측 성능을 실시간으로 확인합니다.
          </p>
        </section>

        {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ① 핵심 지표 카드
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          {isLoading ? (
            <div className="flex justify-around animate-pulse">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex flex-col items-center gap-3">
                  <div className="h-36 w-36 rounded-full bg-white/10" />
                  <div className="h-3 w-24 rounded-full bg-white/10" />
                </div>
              ))}
            </div>
          ) : isError || !stats ? (
            <p className="text-center text-sm text-red-400">통계를 불러오지 못했습니다.</p>
          ) : (
            <div className="grid grid-cols-2 gap-8 sm:grid-cols-4">
              {/* 원형 게이지 4개 */}
              <CircularGauge value={stats.top1Accuracy}    label="Top-1 적중률"    />
              <CircularGauge value={stats.top3Accuracy}    label="Top-3 적중률"    />
              <CircularGauge value={stats.last30DaysTop1}  label="최근 30일 Top-1" />
              {/* 전체 예측 수는 숫자 카드로 표시 */}
              <div className="flex flex-col items-center gap-3">
                <div className="flex h-[140px] w-[140px] flex-col items-center justify-center rounded-full border-4 border-white/10">
                  <span className="font-heading text-3xl font-bold text-white">
                    {stats.totalPredictions.toLocaleString()}
                  </span>
                  <span className="text-xs text-white/45">건</span>
                </div>
                <p className="text-center text-sm text-white/60">전체 예측 수</p>
              </div>
            </div>
          )}
        </section>

        {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ② 월별 정확도 추이 꺾은선 그래프
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <section className="space-y-4">
          <h2 className="font-heading text-2xl text-white">월별 정확도 추이</h2>
          <div className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5">
            {stats?.monthlyTrend?.length ? (
              // ResponsiveContainer = 부모 너비에 맞게 차트가 자동으로 늘어납니다.
              <ResponsiveContainer width="100%" height={280}>
                <LineChart
                  data={stats.monthlyTrend}
                  margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                >
                  {/* 배경 격자선 */}
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  {/* X축: 월 표시 */}
                  <XAxis
                    dataKey="month"
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }}
                  />
                  {/* Y축: 정확도(%) 표시, 0~100 범위 */}
                  <YAxis
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }}
                    width={45}
                  />
                  <Tooltip
                    {...tooltipStyle}
                    formatter={(v: number) => [`${v}%`]}
                  />
                  <Legend
                    wrapperStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem' }}
                  />
                  {/* Top-1 꺾은선 — 골드색 */}
                  <Line
                    type="monotone"
                    dataKey="top1"
                    name="Top-1 적중률"
                    stroke="#f5c842"
                    strokeWidth={2}
                    dot={{ r: 4, fill: '#f5c842' }}
                    activeDot={{ r: 6 }}
                  />
                  {/* Top-3 꺾은선 — 흰색 계열 */}
                  <Line
                    type="monotone"
                    dataKey="top3"
                    name="Top-3 적중률"
                    stroke="rgba(255,255,255,0.6)"
                    strokeWidth={2}
                    strokeDasharray="5 3"
                    dot={{ r: 4, fill: 'rgba(255,255,255,0.6)' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-64 items-center justify-center">
                <p className="text-sm text-white/40">추이 데이터를 불러오는 중...</p>
              </div>
            )}
          </div>
        </section>

        {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ③ 경마장별 정확도 바 차트
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <section className="space-y-4">
          <h2 className="font-heading text-2xl text-white">경마장별 정확도</h2>
          <div className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5">
            {meetData.length > 0 ? (
              <ResponsiveContainer width="100%" height={220}>
                <BarChart
                  data={meetData}
                  margin={{ top: 10, right: 20, left: 0, bottom: 0 }}
                  barCategoryGap="35%"
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis
                    dataKey="name"
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.6)', fontSize: 12 }}
                  />
                  <YAxis
                    domain={[0, 100]}
                    tickFormatter={(v) => `${v}%`}
                    stroke="rgba(255,255,255,0.3)"
                    tick={{ fill: 'rgba(255,255,255,0.45)', fontSize: 11 }}
                    width={45}
                  />
                  <Tooltip
                    {...tooltipStyle}
                    formatter={(v: number) => [`${v}%`]}
                  />
                  <Legend
                    wrapperStyle={{ color: 'rgba(255,255,255,0.6)', fontSize: '0.75rem' }}
                  />
                  {/* Top-1 막대 — 골드 */}
                  <Bar dataKey="Top-1" fill="#f5c842" radius={[4, 4, 0, 0]} />
                  {/* Top-3 막대 — 반투명 흰색 */}
                  <Bar dataKey="Top-3" fill="rgba(255,255,255,0.25)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-48 items-center justify-center animate-pulse">
                <p className="text-sm text-white/40">불러오는 중...</p>
              </div>
            )}
          </div>
        </section>

        {/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            ④ 최근 예측 목록
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-2xl text-white">최근 예측 결과</h2>
            {/* TODO: [Phase 3] predictions API 연동 후 실제 데이터로 교체 */}
            <span className="rounded-full border border-white/15 bg-white/5 px-3 py-1 text-xs text-white/40">
              데모 데이터
            </span>
          </div>
          <div className="flex flex-col gap-2">
            {DEMO_PREDICTIONS.map((pred, i) => (
              <PredictionResult key={i} {...pred} />
            ))}
          </div>
        </section>
      </div>
    </Layout>
  )
}

export default DashboardPage
