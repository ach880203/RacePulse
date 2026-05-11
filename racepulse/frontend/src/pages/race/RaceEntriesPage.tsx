// =============================================================================
// RaceEntriesPage.tsx — 출전 명단 페이지
// 라우트: /races/:raceId/entries
// =============================================================================

import { Link, useParams } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import DataStatusBadge from '../../components/DataStatusBadge'
import { useRace, useRaceEntries } from '../../hooks/useRaces'

const MEET_LABELS: Record<string, string> = {
  SC: '서울',
  BU: '부산',
  JJ: '제주',
}

function RaceEntriesPage() {
  const { raceId } = useParams<{ raceId: string }>()
  const id = raceId ? Number(raceId) : undefined

  // 경주 기본 정보 (상단 요약에 사용)
  const { data: race } = useRace(id)
  // 출전 명단
  const { data: entries, isLoading, isError } = useRaceEntries(id)

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 브레드크럼 */}
        <nav className="flex items-center gap-2 text-sm text-white/45">
          <Link to="/races" className="hover:text-white/70">경주 목록</Link>
          <span>/</span>
          {race && (
            <>
              <Link to={`/races/${id}`} className="hover:text-white/70">{race.raceName}</Link>
              <span>/</span>
            </>
          )}
          <span className="text-white/70">출전 명단</span>
        </nav>

        {/* 경주 요약 헤더 */}
        {race && (
          <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5">
            <p className="text-sm text-brand-gold-400">{MEET_LABELS[race.meetCode] ?? race.meetCode}</p>
            <h1 className="mt-1 font-heading text-3xl text-white">{race.raceName} — 출전 명단</h1>
            <p className="mt-2 text-sm text-white/50">
              {race.rcDate} · {race.distance}m · 출발 {race.startTime ?? '미정'}
            </p>
          </section>
        )}

        {/* 로딩 */}
        {isLoading && (
          <div className="space-y-3 animate-pulse">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-16 rounded-2xl bg-white/5" />
            ))}
          </div>
        )}

        {/* 오류 */}
        {isError && (
          <div className="rounded-3xl border border-red-400/20 bg-red-400/5 px-6 py-10 text-center">
            <p className="text-sm text-red-400">출전 명단을 불러오지 못했습니다.</p>
            <p className="mt-2 text-xs text-white/40">
              출전 명단 API가 아직 준비 중일 수 있습니다.
            </p>
          </div>
        )}

        {/* 데이터 없음 */}
        {!isLoading && !isError && entries?.length === 0 && (
          <div className="rounded-3xl border border-dashed border-white/15 bg-white/4 px-5 py-10 text-center">
            <p className="text-white/60">출전 명단이 아직 등록되지 않았습니다.</p>
          </div>
        )}

        {/* 출전 명단 테이블 */}
        {!isLoading && entries && entries.length > 0 && (
          <section className="overflow-x-auto rounded-[2rem] border border-white/10">
            <table className="w-full min-w-[640px] text-sm">
              <thead>
                <tr className="border-b border-white/10 bg-white/5 text-left text-xs text-white/45">
                  <th className="px-4 py-3 font-medium">마번</th>
                  <th className="px-4 py-3 font-medium">말 이름</th>
                  <th className="px-4 py-3 font-medium">기수</th>
                  <th className="px-4 py-3 font-medium">조교사</th>
                  <th className="px-4 py-3 font-medium text-right">마체중</th>
                  <th className="px-4 py-3 font-medium text-right">부담중량</th>
                  <th className="px-4 py-3 font-medium text-right">배당</th>
                  <th className="px-4 py-3 font-medium">상태</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/8">
                {entries.map((entry) => (
                  <tr
                    key={entry.id}
                    className="transition-colors hover:bg-white/4"
                  >
                    {/* 마번 */}
                    <td className="px-4 py-4">
                      <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-gold-400/15 font-heading text-sm font-bold text-brand-gold-400">
                        {entry.gateNo}
                      </span>
                    </td>
                    {/* 말 이름 — 클릭 시 경주마 상세 페이지로 이동 */}
                    <td className="px-4 py-4">
                      <Link
                        to={`/horses/${entry.horseId}`}
                        className="font-semibold text-white hover:text-brand-gold-400"
                      >
                        {entry.horseName}
                      </Link>
                      {entry.horseEngName && (
                        <p className="text-xs text-white/40">{entry.horseEngName}</p>
                      )}
                    </td>
                    {/* 기수 — 클릭 시 기수 상세 페이지로 이동 */}
                    <td className="px-4 py-4">
                      {entry.jockeyId ? (
                        <Link
                          to={`/jockeys/${entry.jockeyId}`}
                          className="text-white/80 hover:text-brand-gold-400"
                        >
                          {entry.jockeyName ?? '-'}
                        </Link>
                      ) : (
                        <span className="text-white/40">-</span>
                      )}
                    </td>
                    {/* 조교사 */}
                    <td className="px-4 py-4">
                      {entry.trainerId ? (
                        <Link
                          to={`/trainers/${entry.trainerId}`}
                          className="text-white/80 hover:text-brand-gold-400"
                        >
                          {entry.trainerName ?? '-'}
                        </Link>
                      ) : (
                        <span className="text-white/40">-</span>
                      )}
                    </td>
                    <td className="px-4 py-4 text-right text-white/70">
                      {entry.weight != null ? `${entry.weight}kg` : '-'}
                    </td>
                    <td className="px-4 py-4 text-right text-white/70">
                      {entry.burden != null ? `${entry.burden}kg` : '-'}
                    </td>
                    <td className="px-4 py-4 text-right font-semibold text-brand-gold-400">
                      {entry.odds != null ? entry.odds.toFixed(1) : '-'}
                    </td>
                    <td className="px-4 py-4">
                      <DataStatusBadge status={entry.dataStatus ?? undefined} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>
        )}
      </div>
    </Layout>
  )
}

export default RaceEntriesPage
