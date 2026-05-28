// =============================================================================
// CommentaryPage.tsx — AI 해설 페이지
// 라우트: /races/:raceId/commentary
// =============================================================================
// 경주 상태에 따라 사전 해설과 결과 해설을 탭으로 전환해 보여줍니다.
// 화면 하단에는 사행 행위 방지를 위한 면책 문구를 항상 고정 노출합니다.
// =============================================================================

import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import Layout from '../../components/layout/Layout'
import TypingAnimation from '../../components/dynamic/TypingAnimation'
import { usePostRaceCommentary, usePreRaceCommentary } from '../../hooks/useCommentary'
import { useRace } from '../../hooks/useRaces'
import type { CommentaryResponse, CommentaryType } from '../../types/commentary'

const MEET_LABELS: Record<string, string> = {
  SC: '서울경마공원',
  BU: '부산경남경마공원',
  JJ: '제주경마공원',
}

type CommentaryTab = 'PRE' | 'POST'

function getCommentaryText(commentary: CommentaryResponse | undefined) {
  return commentary?.content ?? commentary?.message ?? '해설이 아직 생성되지 않았습니다.'
}

function formatQualityScore(score: CommentaryResponse['qualityScore']) {
  if (score == null || score === '') {
    return null
  }

  const numberScore = Number(score)
  return Number.isFinite(numberScore) ? Math.round(numberScore) : null
}

function CommentaryPage() {
  const { raceId } = useParams<{ raceId: string }>()
  const id = raceId ? Number(raceId) : undefined
  const hasValidRaceId = id != null && Number.isFinite(id)

  const { data: race, isLoading: raceLoading, isError: raceError } = useRace(hasValidRaceId ? id : undefined)
  const isCompletedRace = race?.status === 'COMPLETED'
  const [activeTab, setActiveTab] = useState<CommentaryTab>('PRE')

  const {
    data: preCommentary,
    isLoading: preLoading,
    isError: preError,
  } = usePreRaceCommentary(hasValidRaceId ? id : undefined)

  const {
    data: postCommentary,
    isLoading: postLoading,
    isError: postError,
  } = usePostRaceCommentary(hasValidRaceId ? id : undefined, isCompletedRace)

  useEffect(() => {
    // 완료된 경주는 결과 해설을 먼저 보여 주되, 사용자가 필요하면 사전 해설 탭으로 되돌아갈 수 있습니다.
    if (isCompletedRace) {
      setActiveTab('POST')
    }
  }, [isCompletedRace])

  const activeCommentary = activeTab === 'POST' ? postCommentary : preCommentary
  const activeLoading = raceLoading || (activeTab === 'POST' ? postLoading : preLoading)
  const activeError = raceError || (activeTab === 'POST' ? postError : preError)
  const qualityScore = formatQualityScore(activeCommentary?.qualityScore)
  const meetLabel = race ? MEET_LABELS[race.meetCode] ?? race.meetCode : ''

  const tabs = useMemo<Array<{ id: CommentaryType; label: string; disabled: boolean }>>(
    () => [
      { id: 'PRE', label: '사전 해설', disabled: false },
      { id: 'POST', label: '결과 해설', disabled: !isCompletedRace },
    ],
    [isCompletedRace],
  )

  if (!hasValidRaceId) {
    return (
      <Layout>
        <div className="rounded-[2rem] border border-red-400/20 bg-red-400/5 px-6 py-12 text-center">
          <p className="text-base text-red-400">경주 번호가 올바르지 않습니다.</p>
          <Link to="/races" className="mt-4 inline-block text-sm text-brand-gold-400 hover:underline">
            경주 목록으로 돌아가기
          </Link>
        </div>
      </Layout>
    )
  }

  return (
    <Layout>
      <div className="flex flex-col gap-8">
        {/* 상단 브레드크럼은 목록, 상세, 현재 해설 화면의 위치 관계를 보여줍니다. */}
        <nav className="flex flex-wrap items-center gap-2 text-sm text-white/45">
          <Link to={`/races/${id}`} className="hover:text-white/70">경주 상세</Link>
          {race && (
            <>
              <span>/</span>
              <span className="text-white/70">{race.raceName}</span>
            </>
          )}
          <span>/</span>
          <span className="text-white/70">AI 해설</span>
        </nav>

        {/* 해설 헤더는 AI 분석 화면임을 알려주고, 품질 점수가 있을 때만 신뢰도를 함께 표시합니다. */}
        <section className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 lg:p-8">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="text-sm tracking-[0.2em] text-brand-gold-400">{meetLabel || '경주 분석'}</p>
              <h1 className="mt-2 font-heading text-4xl text-white">AI 해설</h1>
              <p className="mt-3 text-sm leading-7 text-white/65">
                GPT-4.1 기반 경주 분석 해설입니다.
              </p>
            </div>
            {qualityScore != null && (
              <div className="rounded-2xl border border-brand-gold-400/30 bg-brand-gold-400/10 px-5 py-4 text-right">
                <p className="text-xs text-white/50">AI 신뢰도</p>
                <p className="mt-1 font-heading text-3xl text-brand-gold-400">{qualityScore}점</p>
              </div>
            )}
          </div>
        </section>

        {/* 탭 전환은 경주 완료 여부에 따라 결과 해설 접근을 제한해 불필요한 빈 요청을 막습니다. */}
        <section className="space-y-5">
          <div className="flex flex-wrap gap-2 rounded-[2rem] border border-white/10 bg-white/5 p-2">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                disabled={tab.disabled}
                onClick={() => setActiveTab(tab.id)}
                className={[
                  'rounded-full px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-35',
                  activeTab === tab.id
                    ? 'bg-brand-gold-400 text-brand-navy-950'
                    : 'text-white/60 hover:bg-white/8 hover:text-white',
                ].join(' ')}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <article className="min-h-80 rounded-[2rem] border border-white/10 bg-white/5 p-6 lg:p-8">
            {activeLoading && (
              <div className="rounded-2xl border border-white/10 bg-brand-navy-950/40 p-5">
                <TypingAnimation text="AI 해설을 불러오는 중입니다..." speed={45} />
              </div>
            )}

            {!activeLoading && activeError && (
              <div className="rounded-2xl border border-red-400/20 bg-red-400/5 px-5 py-8 text-center">
                <p className="text-sm text-red-400">AI 해설을 불러오지 못했습니다.</p>
                <p className="mt-2 text-xs text-white/45">잠시 후 다시 시도해주세요.</p>
              </div>
            )}

            {!activeLoading && !activeError && (
              <div className="whitespace-pre-wrap text-base leading-8 text-white/82">
                {getCommentaryText(activeCommentary)}
              </div>
            )}
          </article>
        </section>

        {/* 면책 문구는 AI 해설이 베팅 권유가 아니라 데이터 분석 자료임을 명확히 하기 위해 항상 노출합니다. */}
        <section className="rounded-[2rem] border border-brand-gold-400/25 bg-brand-gold-400/10 p-5 text-sm leading-7 text-white/80">
          본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다.
        </section>
      </div>
    </Layout>
  )
}

export default CommentaryPage
