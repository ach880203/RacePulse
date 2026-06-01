// =============================================================================
// RaceResultPage.tsx — 경주 결과 페이지
// 라우트: /races/:raceId/result
// =============================================================================
// 이 화면은 경주 기본 정보와 실제 착순을 함께 보여줍니다.
// 예측 데이터가 준비된 경우에는 AI 예측과 실제 결과를 나란히 비교합니다.
// =============================================================================

import { Link, useParams } from 'react-router-dom'

import Layout from '../../components/layout/Layout'
import DataStatusBadge from '../../components/DataStatusBadge'
import { usePrediction } from '../../hooks/usePrediction'
import { useRace, useRaceResult } from '../../hooks/useRaces'
import type { RaceResult } from '../../types/entry'

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

function formatRank(result: RaceResult) {
  return result.finishOrder != null ? `${result.finishOrder}위` : '-'
}

function formatMargin(result: RaceResult) {
  if (result.finishOrder === 1) {
    return '-'
  }

  return result.margin ?? '-'
}

function RaceResultPage() {
  const { raceId } = useParams<{ raceId: string }>()
  const id = raceId ? Number(raceId) : undefined

  const hasValidRaceId = id != null && Number.isFinite(id)
  const { data: race, isLoading: raceLoading, isError: raceError } = useRace(hasValidRaceId ? id : undefined)
  const { data: results, isLoading: resultLoading, isError: resultError } = useRaceResult(hasValidRaceId ? id : undefined)
  const { data: prediction } = usePrediction(hasValidRaceId ? id : undefined)

  if (raceLoading || resultLoading) {
    return (
      <Layout>
        <div className="grid gap-6 animate-pulse">
          <div className="h-8 w-64 rounded-full bg-white/10" />
          <div className="h-44 rounded-[2rem] bg-white/5" />
          <div className="h-72 rounded-[2rem] bg-white/5" />
        </div>
      </Layout>
    )
  }

  if (!hasValidRaceId || raceError || resultError || !race) {
    return (
      <Layout>
        <div className="rounded-[2rem] border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
          <p className="text-base text-red-400">경주 결과를 불러오지 못했습니다.</p>
          <p className="mt-2 text-sm text-white/55">경주 번호가 올바른지 확인한 뒤 다시 시도해주세요.</p>
          <Link to="/races" className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
            경주 목록으로 돌아가기
          </Link>
        </div>
      </Layout>
    )
  }

  const meetLabel = MEET_LABELS[race.meetCode] ?? race.meetCode
  const sortedResults = [...(results ?? [])].sort((a, b) => (a.finishOrder ?? 999) - (b.finishOrder ?? 999))
  const sortedPredictions = prediction?.predictions
    ? [...prediction.predictions].sort((a, b) => a.predictedRank - b.predictedRank)
    : []

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 상단 브레드크럼은 현재 사용자가 어느 경주 결과를 보고 있는지 알려줍니다. */}
        <nav className="flex flex-wrap items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">경주 목록</Link>
          <span>/</span>
          <Link to={`/races/${race.id}`} className="hover:text-white/70">{race.raceName}</Link>
          <span>/</span>
          <span className="text-white/70">경주 결과</span>
        </nav>

        {/* 경주 요약 영역은 결과 표를 보기 전에 장소, 날짜, 거리 같은 핵심 조건을 먼저 고정해 줍니다. */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">{meetLabel}</p>
              <h1 className="mt-2 font-heading text-4xl text-white">{race.raceName}</h1>
              <p className="mt-3 text-sm text-white/60">
                제{race.raceNo}경주 · {race.rcDate}
              </p>
            </div>
            {race.dataStatus && <DataStatusBadge status={race.dataStatus} />}
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs text-white/45">거리</p>
              <p className="mt-2 font-semibold text-white">{race.distance}m</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs text-white/45">트랙</p>
              <p className="mt-2 font-semibold text-white">{race.trackType ?? '미정'}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs text-white/45">날씨</p>
              <p className="mt-2 font-semibold text-white">{race.weather ?? '-'}</p>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <p className="text-xs text-white/45">상태</p>
              <p className="mt-2 font-semibold text-white">{race.status === 'COMPLETED' ? '완료' : race.status === 'SCHEDULED' ? '예정' : '취소'}</p>
            </div>
          </div>
        </section>

        {/* 최종 순위 섹션은 실제 착순, 경주마, 기수, 기록, 차이를 표 형태로 표시합니다. */}
        <section className="space-y-4">
          <div className="flex items-end justify-between gap-4">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">최종 순위</p>
              <h2 className="mt-2 font-heading text-3xl text-white">실제 경주 결과</h2>
            </div>
            <p className="text-sm text-white/45">{sortedResults.length}건</p>
          </div>

          {sortedResults.length === 0 ? (
            <div className="rounded-[2rem] border border-white/10 bg-white/5 px-6 py-12 text-center">
              <p className="text-white/60">결과 데이터가 없습니다</p>
            </div>
          ) : (
            <div className="overflow-hidden rounded-[2rem] border border-white/10 bg-white/5">
              <div className="hidden grid-cols-[6rem_minmax(10rem,1fr)_8rem_8rem_8rem] gap-4 border-b border-white/10 px-5 py-4 text-xs text-white/45 md:grid">
                <span>순위</span>
                <span>경주마</span>
                <span>게이트</span>
                <span>기수</span>
                <span>기록</span>
              </div>
              <div className="divide-y divide-white/10">
                {sortedResults.map((result) => {
                  const isWinner = result.finishOrder === 1
                  const isPodium = result.finishOrder != null && result.finishOrder <= 3

                  return (
                    <article
                      key={result.id}
                      className="grid gap-3 px-5 py-5 md:grid-cols-[6rem_minmax(10rem,1fr)_8rem_8rem_8rem]"
                    >
                      <p className={['font-heading text-2xl', isWinner ? 'text-brand-gold-400' : isPodium ? 'text-white' : 'text-white/60'].join(' ')}>
                        {formatRank(result)}
                      </p>
                      <div>
                        <p className={isWinner ? 'font-semibold text-brand-gold-400' : 'font-semibold text-white'}>{result.horseName}</p>
                        <p className="mt-1 text-xs text-white/45">차이 {formatMargin(result)}</p>
                      </div>
                      <p className="text-sm text-white/65">게이트 {result.gateNo ?? '-'}</p>
                      <p className="text-sm text-white/65">{result.jockeyName ?? '-'}</p>
                      <p className="text-sm font-semibold text-white">{result.finishTime ?? '-'}</p>
                    </article>
                  )
                })}
              </div>
            </div>
          )}
        </section>

        {/* 예측 비교 섹션은 예측 데이터가 있을 때만 보여 사용자가 실제 결과와 모델 판단 차이를 확인하게 합니다. */}
        {sortedPredictions.length > 0 && (
          <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6">
            <p className="text-sm tracking-[0.2em] text-brand-gold-400">예측 대 실제</p>
            <h2 className="mt-2 font-heading text-3xl text-white">AI 예측 비교</h2>
            <p className="mt-3 text-sm leading-7 text-white/65">이 경주의 AI 예측과 실제 결과를 비교합니다.</p>
            <div className="mt-5 grid gap-3 md:grid-cols-3">
              {sortedPredictions.slice(0, 3).map((item) => {
                const actual = sortedResults.find((result) => result.horseId === item.horseId)
                return (
                  <div key={item.horseId} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs text-white/45">예측 {item.predictedRank}위</p>
                    <p className="mt-2 font-semibold text-white">{item.horseName}</p>
                    <p className="mt-2 text-sm text-white/60">실제 {actual?.finishOrder != null ? `${actual.finishOrder}위` : '-'}</p>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        <div className="flex flex-wrap gap-3">
          <Link
            to={`/races/${race.id}/commentary`}
            className="rounded-2xl bg-brand-gold-400 px-5 py-3 text-sm font-semibold text-brand-navy-950 transition hover:bg-brand-gold-500"
          >
            AI 해설 보기
          </Link>
          <Link
            to={`/races/${race.id}`}
            className="rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-semibold text-white/70 transition hover:text-white"
          >
            경주 상세로 돌아가기
          </Link>
        </div>
      </div>
    </Layout>
  )
}

export default RaceResultPage
