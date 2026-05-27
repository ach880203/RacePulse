// =============================================================================
// JockeyListPage.tsx — 기수 목록 페이지
// 라우트: /jockeys
// =============================================================================

import { useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../../components/layout/Layout'
import { useJockeys } from '../../hooks/usePersons'

const MEET_OPTIONS = [
  { value: '',   label: '전체 경마장' },
  { value: 'SC', label: '서울' },
  { value: 'BU', label: '부산' },
  { value: 'JJ', label: '제주' },
]

const MEET_LABELS: Record<string, string> = {
  SC: '서울',
  BU: '부산',
  JJ: '제주',
}

function JockeyListPage() {
  const [searchInput, setSearchInput] = useState('')
  const [nameQuery, setNameQuery]     = useState('')
  const [meetCode, setMeetCode]       = useState('')
  const [page, setPage]               = useState(0)

  const { data, isLoading, isError } = useJockeys({
    name:     nameQuery || undefined,
    meetCode: meetCode  || undefined,
    page,
    size: 20,
  })

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setNameQuery(searchInput.trim())
    setPage(0)
  }

  const handleMeetCodeChange = (code: string) => {
    setMeetCode(code)
    setPage(0)
  }

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 헤더 */}
        <section>
          <p className="text-sm tracking-[0.2em] text-brand-gold-400">기수</p>
          <h1 className="mt-2 font-heading text-4xl text-white">기수 목록</h1>
          <p className="mt-2 text-sm text-white/50">
            {data ? `총 ${data.totalElements.toLocaleString()}명` : '검색 중...'}
          </p>
        </section>

        {/* 검색 + 필터 */}
        <section className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <form onSubmit={handleSearch} className="flex flex-1 gap-2">
            <input
              type="text"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              placeholder="기수 이름으로 검색"
              className="flex-1 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white outline-none placeholder:text-white/35 focus:border-brand-gold-400/60 transition"
            />
            <button
              type="submit"
              className="rounded-2xl bg-brand-gold-400 px-5 py-3 text-sm font-semibold text-brand-navy-950 transition hover:bg-brand-gold-300"
            >
              검색
            </button>
          </form>

          <div className="flex gap-2">
            {MEET_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                type="button"
                onClick={() => handleMeetCodeChange(opt.value)}
                className={[
                  'rounded-full px-4 py-2 text-sm font-semibold transition',
                  meetCode === opt.value
                    ? 'bg-brand-gold-400 text-brand-navy-950'
                    : 'border border-white/10 text-white/60 hover:bg-white/8 hover:text-white',
                ].join(' ')}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </section>

        {/* 로딩 */}
        {isLoading && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 animate-pulse">
            {Array.from({ length: 12 }).map((_, i) => (
              <div key={i} className="h-36 rounded-[2rem] bg-white/5" />
            ))}
          </div>
        )}

        {/* 오류 */}
        {isError && (
          <div className="rounded-[2rem] border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
            <p className="text-sm text-red-400">기수 목록을 불러오지 못했습니다.</p>
          </div>
        )}

        {/* 결과 없음 */}
        {!isLoading && !isError && data?.content.length === 0 && (
          <div className="rounded-[2rem] border border-white/10 bg-white/5 px-6 py-16 text-center">
            <p className="text-white/50">검색 결과가 없습니다.</p>
          </div>
        )}

        {/* 기수 카드 목록 */}
        {data && data.content.length > 0 && (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {data.content.map((jockey) => {
              const winPct    = jockey.winRateTotal   != null ? (jockey.winRateTotal   * 100).toFixed(1) : null
              const recentPct = jockey.winRateRecent  != null ? (jockey.winRateRecent  * 100).toFixed(1) : null
              const placePct  = jockey.placeRateTotal != null ? (jockey.placeRateTotal * 100).toFixed(1) : null

              return (
                <Link
                  key={jockey.id}
                  to={`/jockeys/${jockey.id}`}
                  className="group rounded-[2rem] border border-white/10 bg-white/5 p-5 transition hover:border-brand-gold-400/40 hover:bg-white/8"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="text-xs text-white/45">{MEET_LABELS[jockey.meetCode] ?? jockey.meetCode}</p>
                      <h3 className="mt-1 font-heading text-xl text-white group-hover:text-brand-gold-400 transition">
                        {jockey.name}
                      </h3>
                      {jockey.engName && (
                        <p className="mt-0.5 text-xs text-white/40">{jockey.engName}</p>
                      )}
                    </div>
                    <span
                      className={[
                        'shrink-0 rounded-full px-2 py-0.5 text-xs font-medium',
                        jockey.isActive
                          ? 'bg-brand-gold-400/15 text-brand-gold-400'
                          : 'bg-white/10 text-white/40',
                      ].join(' ')}
                    >
                      {jockey.isActive ? '현역' : '은퇴'}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-3 gap-2 text-center">
                    <div>
                      <p className="text-[10px] text-white/40">통산 승률</p>
                      <p className="mt-0.5 text-sm font-semibold text-white">{winPct != null ? `${winPct}%` : '-'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/40">최근 승률</p>
                      <p className="mt-0.5 text-sm font-semibold text-brand-gold-400">{recentPct != null ? `${recentPct}%` : '-'}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/40">연대율</p>
                      <p className="mt-0.5 text-sm font-semibold text-white">{placePct != null ? `${placePct}%` : '-'}</p>
                    </div>
                  </div>

                  {jockey.debutYear && (
                    <p className="mt-3 text-xs text-white/35">{jockey.debutYear}년 데뷔</p>
                  )}
                </Link>
              )
            })}
          </div>
        )}

        {/* 페이지네이션 */}
        {data && data.totalPages > 1 && (
          <div className="flex items-center justify-center gap-2">
            <button
              type="button"
              disabled={page === 0}
              onClick={() => setPage((p) => p - 1)}
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 transition hover:bg-white/8 disabled:opacity-30"
            >
              이전
            </button>
            <span className="text-sm text-white/50">
              {page + 1} / {data.totalPages}
            </span>
            <button
              type="button"
              disabled={page + 1 >= data.totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-white/60 transition hover:bg-white/8 disabled:opacity-30"
            >
              다음
            </button>
          </div>
        )}
      </div>
    </Layout>
  )
}

export default JockeyListPage
