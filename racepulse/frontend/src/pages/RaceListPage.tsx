// List = 화면에 보이는 행만 실제 DOM으로 그려 긴 목록 렌더링 비용을 줄이는 가상화 컴포넌트입니다.
import { List } from 'react-window'
import type { RowComponentProps } from 'react-window'

// Link = 경주 카드를 눌렀을 때 상세 경로로 이동시키는 라우터 링크입니다.
// useSearchParams = 필터 상태를 URL 쿼리 파라미터로 관리해 뒤로가기 시 상태를 복원합니다.
import { Link, useSearchParams } from 'react-router-dom'

// Layout = 페이지 공통 헤더/푸터를 감싸는 레이아웃 컴포넌트입니다.
import Layout from '../components/layout/Layout'

// useRaces = 경주 목록을 서버에서 가져오는 React Query 훅입니다.
import { useRaces } from '../hooks/useRaces'

// DataStatusBadge = 데이터 수집 상태 뱃지 컴포넌트입니다.
import DataStatusBadge from '../components/DataStatusBadge'

// 타입 정의
import type { MeetCode, Race, RaceStatus } from '../types/race'

// =============================================================================
// 상수 정의
// =============================================================================
type MeetFilter = 'ALL' | MeetCode

const MEET_FILTERS: { value: MeetFilter; label: string }[] = [
  { value: 'ALL', label: '전체' },
  { value: 'SC',  label: '서울' },
  { value: 'BU',  label: '부산' },
  { value: 'JJ',  label: '제주' },
]

const MEET_LABELS: Record<MeetCode, string> = {
  SC: '서울',
  BU: '부산',
  JJ: '제주',
}

const STATUS_LABELS: Record<RaceStatus, string> = {
  SCHEDULED: '예정',
  COMPLETED: '완료',
  CANCELLED: '취소',
}

// 한 페이지에 표시할 경주 수
const PAGE_SIZE = 10

// 100건 이상부터 가상화를 켭니다. 적은 목록은 일반 렌더링이 더 단순하고 충분히 빠릅니다.
const VIRTUAL_LIST_THRESHOLD = 100

// react-window는 각 행의 높이를 미리 알아야 스크롤 위치를 빠르게 계산할 수 있습니다.
const VIRTUAL_ROW_HEIGHT = 178

// =============================================================================
// 로딩 스켈레톤
// =============================================================================
function RaceRowSkeleton() {
  return (
    <div className="animate-pulse rounded-[1.75rem] border border-white/10 bg-white/5 p-5">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <div className="h-3 w-20 rounded-full bg-white/10" />
          <div className="h-6 w-36 rounded-full bg-white/15" />
        </div>
        <div className="grid grid-cols-2 gap-4 sm:min-w-[16rem]">
          <div className="h-4 w-16 rounded-full bg-white/10" />
          <div className="h-4 w-16 rounded-full bg-white/10" />
        </div>
      </div>
    </div>
  )
}

interface RaceCardProps {
  race: Race
}

function RaceCard({ race }: RaceCardProps) {
  return (
    <Link
      to={`/races/${race.id}`}
      className="group block rounded-[1.75rem] border border-white/10 bg-white/5 p-5 transition-transform hover:-translate-y-1 hover:border-brand-gold-400/40"
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="space-y-2">
          <p className="text-sm text-white/55">
            {MEET_LABELS[race.meetCode] ?? race.meetCode} 경마장
          </p>
          <h3 className="font-heading text-2xl text-white group-hover:text-brand-gold-400">
            {race.raceName}
          </h3>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm text-white/68 sm:min-w-[16rem]">
          <div>
            <p className="text-white/45">거리</p>
            <p className="mt-1 font-semibold text-white">{race.distance}m</p>
          </div>
          <div>
            <p className="text-white/45">출발시간</p>
            <p className="mt-1 font-semibold text-white">{race.startTime ?? '미정'}</p>
          </div>
        </div>
      </div>

      <div className="mt-5 flex items-center justify-between border-t border-white/8 pt-4 text-sm">
        <span className="text-white/55">상태</span>
        {race.dataStatus
          ? <DataStatusBadge status={race.dataStatus} />
          : (
            <span className="rounded-full border border-brand-gold-400/35 bg-brand-gold-400/10 px-3 py-1 text-brand-gold-400">
              {STATUS_LABELS[race.status] ?? race.status}
            </span>
          )
        }
      </div>
    </Link>
  )
}

interface VirtualRaceRowProps {
  races: Race[]
}

function VirtualRaceRow({ index, style, races }: RowComponentProps<VirtualRaceRowProps>) {
  // 가상화는 전체 목록을 DOM에 다 넣지 않고, 스크롤 위치 주변 행만 그립니다.
  // 이 wrapper에 react-window가 계산한 style을 붙여야 스크롤 위치가 정확합니다.
  return (
    <div style={style} className="px-1 pb-4">
      <RaceCard race={races[index]} />
    </div>
  )
}

// =============================================================================
// RaceListPage 컴포넌트
// =============================================================================
function RaceListPage() {
  // URL 쿼리 파라미터로 필터 상태를 관리합니다.
  // 뒤로가기 시 브라우저가 URL을 복원하므로 필터 상태가 그대로 유지됩니다.
  const [searchParams, setSearchParams] = useSearchParams()

  const selectedMeetCode = (searchParams.get('meetCode') ?? 'ALL') as MeetFilter
  const selectedDate     = searchParams.get('date') ?? new Date().toISOString().slice(0, 10)
  const currentPage      = Number(searchParams.get('page') ?? '0')

  const { data, isLoading, isError, isFetching } = useRaces({
    meetCode: selectedMeetCode,
    rcDate: selectedDate,
    page: currentPage,
    size: PAGE_SIZE,
  })

  function handleMeetCodeChange(value: MeetFilter) {
    setSearchParams((prev) => {
      prev.set('meetCode', value)
      prev.set('page', '0')
      return prev
    })
  }

  function handleDateChange(value: string) {
    setSearchParams((prev) => {
      prev.set('date', value)
      prev.set('page', '0')
      return prev
    })
  }

  const races = data?.content ?? []
  const totalPages = data?.totalPages ?? 0
  const totalElements = data?.totalElements ?? 0

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 페이지 헤더 */}
        <section className="space-y-3">
          <p className="text-sm tracking-[0.2em] text-brand-gold-400">RACE BOARD</p>
          <h1 className="font-heading text-4xl text-white">경주 목록</h1>
          <p className="max-w-2xl text-sm leading-7 text-white/65">
            날짜와 경마장으로 경주를 필터링합니다.
          </p>
        </section>

        {/* 필터 바 */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/50 p-5">
          <div className="flex flex-col gap-5 md:flex-row md:items-end md:justify-between">
            {/* 경마장 필터 */}
            <div className="space-y-3">
              <p className="text-sm text-white/60">경마장 선택</p>
              <div className="flex flex-wrap gap-2">
                {MEET_FILTERS.map((filter) => (
                  <button
                    key={filter.value}
                    type="button"
                    onClick={() => handleMeetCodeChange(filter.value)}
                    className={[
                      'rounded-full px-4 py-2 text-sm font-medium transition-colors',
                      selectedMeetCode === filter.value
                        ? 'bg-brand-gold-400 text-brand-navy-950'
                        : 'bg-white/6 text-white/72 hover:bg-white/10 hover:text-white',
                    ].join(' ')}
                  >
                    {filter.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 날짜 필터 */}
            <label className="flex flex-col gap-2 text-sm text-white/60">
              날짜 선택
              <input
                type="date"
                value={selectedDate}
                onChange={(e) => handleDateChange(e.target.value)}
                className="rounded-2xl border border-white/10 bg-brand-navy-950 px-4 py-3 text-white outline-none transition-colors focus:border-brand-gold-400"
              />
            </label>
          </div>
        </section>

        {/* 경주 목록 */}
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-heading text-3xl text-white">
              경주 목록
              {/* isFetching = 백그라운드에서 새 데이터를 가져오는 중 */}
              {isFetching && (
                <span className="ml-3 text-sm font-normal text-white/40">업데이트 중...</span>
              )}
            </h2>
            {totalElements > 0 && (
              <span className="rounded-full border border-brand-gold-400/30 bg-brand-gold-400/10 px-3 py-1 text-xs text-brand-gold-400">
                총 {totalElements}건
              </span>
            )}
          </div>

          {/* 로딩 중 스켈레톤 */}
          {isLoading && (
            <div className="grid gap-4">
              {Array.from({ length: 3 }).map((_, i) => (
                <RaceRowSkeleton key={i} />
              ))}
            </div>
          )}

          {/* 오류 */}
          {isError && (
            <div className="rounded-[1.75rem] border border-red-400/20 bg-red-400/5 px-5 py-10 text-center">
              <p className="text-sm text-red-400">
                데이터를 불러오지 못했습니다. 잠시 후 다시 시도해주세요.
              </p>
            </div>
          )}

          {/* 데이터 없음 */}
          {!isLoading && !isError && races.length === 0 && (
            <div className="rounded-[1.75rem] border border-dashed border-white/15 bg-white/4 px-5 py-10 text-center">
              <p className="text-base text-white/72">해당 조건의 경주가 없습니다.</p>
              <p className="mt-2 text-sm text-white/45">다른 날짜나 경마장을 선택해보세요.</p>
            </div>
          )}

          {/* 실제 경주 카드 */}
          {!isLoading && races.length > 0 && (
            <div className="grid gap-4">
              {races.length >= VIRTUAL_LIST_THRESHOLD ? (
                <List
                  className="rounded-[1.75rem]"
                  rowComponent={VirtualRaceRow}
                  rowCount={races.length}
                  rowHeight={VIRTUAL_ROW_HEIGHT}
                  rowProps={{ races }}
                  overscanCount={4}
                  style={{ height: 720 }}
                />
              ) : (
                races.map((race) => (
                  <RaceCard key={race.id} race={race} />
                ))
              )}
            </div>
          )}

          {/* 페이지네이션 */}
          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-2 pt-4">
              <button
                type="button"
                onClick={() => setSearchParams((prev) => { prev.set('page', String(Math.max(0, currentPage - 1))); return prev })}
                disabled={currentPage === 0}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-30"
              >
                이전
              </button>

              {/* 페이지 번호 버튼들 */}
              {Array.from({ length: Math.min(totalPages, 5) }).map((_, i) => {
                // 현재 페이지 주변 5개만 표시합니다.
                const start = Math.max(0, Math.min(currentPage - 2, totalPages - 5))
                const pageNum = start + i
                return (
                  <button
                    key={pageNum}
                    type="button"
                    onClick={() => setSearchParams((prev) => { prev.set('page', String(pageNum)); return prev })}
                    className={[
                      'h-9 w-9 rounded-full text-sm font-medium transition-colors',
                      currentPage === pageNum
                        ? 'bg-brand-gold-400 text-brand-navy-950'
                        : 'border border-white/10 bg-white/5 text-white/70 hover:bg-white/10',
                    ].join(' ')}
                  >
                    {pageNum + 1}
                  </button>
                )
              })}

              <button
                type="button"
                onClick={() => setSearchParams((prev) => { prev.set('page', String(Math.min(totalPages - 1, currentPage + 1))); return prev })}
                disabled={currentPage >= totalPages - 1}
                className="rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm text-white/70 transition-colors hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-30"
              >
                다음
              </button>
            </div>
          )}
        </section>
      </div>
    </Layout>
  )
}

export default RaceListPage
