// =============================================================================
// RaceDetailPage.tsx — 경주 상세 페이지
// 라우트: /races/:raceId
// =============================================================================
// useParams란?
//   URL의 ":raceId" 부분을 읽어오는 React Router 훅입니다.
//   예: /races/42 → useParams() → { raceId: "42" }
//   URL에서 읽은 값은 항상 문자열이므로 Number()로 숫자로 바꿔야 합니다.
// =============================================================================

import { Link, useParams } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import CountdownTimer from '../../components/CountdownTimer'
import DataStatusBadge from '../../components/DataStatusBadge'
import { useRace, useWeather } from '../../hooks/useRaces'

// 경마장 코드 → 한글 이름 변환 맵
const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

function RaceDetailPage() {
  // useParams = URL에서 :raceId 부분을 꺼냅니다.
  // 예: /races/42 → params.raceId === "42"
  const { raceId } = useParams<{ raceId: string }>()

  // URL 파라미터는 문자열이므로 Number()로 숫자 변환이 필요합니다.
  const id = raceId ? Number(raceId) : undefined

  const { data: race, isLoading, isError } = useRace(id)

  // 경주 데이터가 있으면 날씨도 함께 가져옵니다.
  const { data: weather } = useWeather(race?.meetCode, race?.rcDate)

  // 로딩 중
  if (isLoading) {
    return (
      <Layout>
        <div className="flex flex-col gap-6 animate-pulse">
          <div className="h-8 w-48 rounded-full bg-white/10" />
          <div className="h-64 rounded-3xl bg-white/5" />
        </div>
      </Layout>
    )
  }

  // 오류 또는 데이터 없음
  if (isError || !race) {
    return (
      <Layout>
        <div className="rounded-3xl border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
          <p className="text-white/60">경주 정보를 불러오지 못했습니다.</p>
          <Link to="/races" className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
            경주 목록으로 돌아가기
          </Link>
        </div>
      </Layout>
    )
  }

  const meetLabel = MEET_LABELS[race.meetCode] ?? race.meetCode

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 상단 브레드크럼 */}
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">경주 목록</Link>
          <span>/</span>
          <span className="text-white/70">{race.raceName}</span>
        </nav>

        {/* 경주 헤더 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">{meetLabel}</p>
              <h1 className="mt-2 font-heading text-4xl text-white">{race.raceName}</h1>
              {race.dataStatus && (
                <div className="mt-3">
                  <DataStatusBadge status={race.dataStatus} />
                </div>
              )}
            </div>
            {/* 경주 시작 카운트다운 타이머 */}
            {race.status === 'SCHEDULED' && (
              <CountdownTimer targetTime={race.startTime} rcDate={race.rcDate} />
            )}
          </div>
        </section>

        {/* 경주 기본 정보 */}
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[
            { label: '날짜',       value: race.rcDate },
            { label: '출발 시각',  value: race.startTime ?? '미정' },
            { label: '거리',       value: `${race.distance}m` },
            { label: '트랙',       value: race.trackType ?? '미정' },
            { label: '상태',       value: race.status === 'SCHEDULED' ? '예정' : race.status === 'COMPLETED' ? '완료' : '취소' },
            { label: '경주 등급',  value: race.raceClass ?? '일반' },
            { label: '날씨',       value: race.weather ?? '-' },
            { label: '상금',       value: race.prize ? `${race.prize.toLocaleString()}원` : '미공개' },
          ].map(({ label, value }) => (
            <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs text-white/45">{label}</p>
              <p className="mt-2 font-semibold text-white">{value}</p>
            </div>
          ))}
        </section>

        {/* 날씨 예보 (ML 서버 데이터) */}
        {weather && (
          <section className="space-y-3">
            <h2 className="font-heading text-2xl text-white">날씨 예보</h2>
            <div className="grid gap-4 sm:grid-cols-4">
              {[
                { label: '날씨 상태',  value: weather.condition ?? '-' },
                { label: '기온',       value: weather.tempMin != null && weather.tempMax != null ? `${weather.tempMin}°C ~ ${weather.tempMax}°C` : '-' },
                { label: '강수 확률',  value: weather.precipitationProb != null ? `${weather.precipitationProb}%` : '-' },
                { label: '풍속',       value: weather.windSpeed != null ? `${weather.windSpeed}m/s` : '-' },
              ].map(({ label, value }) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <p className="text-xs text-white/45">{label}</p>
                  <p className="mt-2 font-semibold text-white">{value}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* 이동 버튼 */}
        <section className="grid gap-3 sm:grid-cols-3">
          <Link
            to={`/races/${race.id}/entries`}
            className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-center text-sm font-medium text-white transition-colors hover:border-brand-gold-400/40 hover:text-brand-gold-400"
          >
            출전 명단 보기
          </Link>
          <Link
            to={`/races/${race.id}/prediction`}
            className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-center text-sm font-medium text-white/60 transition-colors hover:text-white/80"
          >
            예측 결과 {/* TODO: [Phase 3] AI 예측 연동 후 활성화 */}
          </Link>
          <Link
            to={`/races/${race.id}/commentary`}
            className="rounded-2xl border border-white/10 bg-white/5 px-5 py-4 text-center text-sm font-medium text-white/60 transition-colors hover:text-white/80"
          >
            AI 해설 {/* TODO: [Phase 3] AI 해설 연동 후 활성화 */}
          </Link>
        </section>
      </div>
    </Layout>
  )
}

export default RaceDetailPage
