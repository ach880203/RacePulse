// =============================================================================
// CounterfactualUI.tsx — 가상 시나리오 분석 UI (A안 리설계)
// =============================================================================
// 조건별 4개 슬라이더 → 각 조건의 가중치를 합산해 prob_adjustment 생성
// 시뮬레이션 횟수 프리셋 버튼 (1만/3만/7만/10만)
// =============================================================================

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import LoadingAnimation from './LoadingAnimation'
import WinProbabilityBar from './WinProbabilityBar'
import type { PredictionItem } from '../../types/prediction'

// ─── Worker 인터페이스 ────────────────────────────────────────────────────────

interface WorkerHorseInput {
  horse_id: number
  horse_name: string
  win_prob: number
  gate_no: number
  odds_win: number | null
  prob_adjustment: number
}

interface WorkerSimulationInput {
  horses: WorkerHorseInput[]
  n_simulations: number
}

interface WorkerRankDistribution {
  '1': number
  '2': number
  '3': number
  '4+': number
}

interface WorkerSimulationResult {
  horse_id: number
  rank_distribution: WorkerRankDistribution
  expected_rank: number
  win_prob_adjusted: number
}

type WorkerMessage =
  | { type: 'success'; results: WorkerSimulationResult[] }
  | { type: 'error'; message: string }

// ─── 시뮬레이션 횟수 프리셋 ──────────────────────────────────────────────────

const SIM_PRESETS = [
  { label: '1만',  value: 10_000  },
  { label: '3만',  value: 30_000  },
  { label: '7만',  value: 70_000  },
  { label: '10만', value: 100_000 },
]

// ─── 조건별 슬라이더 정의 ────────────────────────────────────────────────────

interface ConditionDef {
  key: keyof HorseConditions
  label: string
  description: string
  min: number
  max: number
  step: number
  unit: string
  // 슬라이더 값 → prob_adjustment(%) 변환 가중치
  weight: number
}

// 각 조건이 우승 확률에 미치는 영향 계수 (경험적 근거)
// 합산 최대치: ±6 + ±2.4 + ±4 + ±3 = ±15.4%
const CONDITION_DEFS: ConditionDef[] = [
  {
    key: 'jockeySkill',
    label: '기수 능력 보정',
    description: '현재 기수보다 우수하거나 미숙한 기수로 교체했을 때의 영향',
    min: -5, max: 5, step: 1, unit: '단계',
    weight: 1.2,  // 1단계당 ±1.2%
  },
  {
    key: 'weightChange',
    label: '마체중 변화',
    description: '경주 전 마체중이 증감했을 때의 영향 (양수=증가, 음수=감소)',
    min: -8, max: 8, step: 1, unit: 'kg',
    weight: 0.3,  // 1kg당 ±0.3%
  },
  {
    key: 'trackFit',
    label: '트랙 적합도',
    description: '이 말이 현재 트랙 상태에 얼마나 유리/불리한지의 보정',
    min: -2, max: 2, step: 1, unit: '단계',
    weight: 2.0,  // 1단계당 ±2.0%
  },
  {
    key: 'weatherFit',
    label: '날씨 적합도',
    description: '이 말이 현재 날씨 조건에 얼마나 유리/불리한지의 보정',
    min: -2, max: 2, step: 1, unit: '단계',
    weight: 1.5,  // 1단계당 ±1.5%
  },
]

// ─── 타입 ────────────────────────────────────────────────────────────────────

interface HorseConditions {
  jockeySkill:  number  // -5 ~ +5
  weightChange: number  // -8 ~ +8 (kg)
  trackFit:     number  // -2 ~ +2
  weatherFit:   number  // -2 ~ +2
}

type ConditionsMap = Record<number, HorseConditions>

interface CounterfactualUIProps {
  predictions: PredictionItem[]
}

// ─── 헬퍼 함수 ───────────────────────────────────────────────────────────────

function defaultConditions(): HorseConditions {
  return { jockeySkill: 0, weightChange: 0, trackFit: 0, weatherFit: 0 }
}

function computeProbAdjustment(cond: HorseConditions): number {
  // 각 조건 × 가중치를 합산해 백분율(%)로 반환, Worker는 소수로 사용하므로 /100
  const pct =
    cond.jockeySkill  * 1.2 +
    cond.weightChange * 0.3 +
    cond.trackFit     * 2.0 +
    cond.weatherFit   * 1.5
  return pct / 100
}

function toWorkerProbability(winProbability: number | null): number {
  return Math.max(0, Math.min(1, (winProbability ?? 0) / 100))
}

function formatDelta(delta: number): string {
  return `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`
}

function formatConditionValue(def: ConditionDef, value: number): string {
  if (value === 0) return '기본값'
  const sign = value > 0 ? '+' : ''
  return `${sign}${value}${def.unit}`
}

// ─── 슬라이더 컴포넌트 ───────────────────────────────────────────────────────

function ConditionSlider({
  def,
  value,
  onChange,
}: {
  def: ConditionDef
  value: number
  onChange: (v: number) => void
}) {
  const impactPct = value * def.weight
  const isPositive = value > 0
  const isNegative = value < 0

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div>
          <span className="font-semibold text-white/85">{def.label}</span>
          <p className="mt-0.5 text-[11px] text-white/40 leading-relaxed">{def.description}</p>
        </div>
        <div className="shrink-0 text-right ml-4">
          <span className={[
            'font-mono text-sm font-semibold',
            isPositive ? 'text-brand-gold-400' : isNegative ? 'text-red-400' : 'text-white/40',
          ].join(' ')}>
            {formatConditionValue(def, value)}
          </span>
          {value !== 0 && (
            <p className={[
              'text-[10px] font-mono',
              isPositive ? 'text-brand-gold-400/70' : 'text-red-400/70',
            ].join(' ')}>
              {formatDelta(impactPct)} 영향
            </p>
          )}
        </div>
      </div>
      <div className="relative">
        <input
          type="range"
          min={def.min}
          max={def.max}
          step={def.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full accent-brand-gold-500"
        />
        {/* 가이드 레이블 */}
        <div className="flex justify-between text-[10px] text-white/25 mt-0.5">
          <span>불리</span>
          <span>기본</span>
          <span>유리</span>
        </div>
      </div>
    </div>
  )
}

// ─── 메인 컴포넌트 ───────────────────────────────────────────────────────────

function CounterfactualUI({ predictions }: CounterfactualUIProps) {
  const sortedPredictions = useMemo(
    () => [...predictions].sort((a, b) => a.predictedRank - b.predictedRank),
    [predictions],
  )

  const initialConditions = useMemo(() => {
    return sortedPredictions.reduce<ConditionsMap>((map, p) => {
      map[p.horseId] = defaultConditions()
      return map
    }, {})
  }, [sortedPredictions])

  const [simCount, setSimCount]               = useState(10_000)
  const [completedCount, setCompletedCount]   = useState<number | null>(null)
  const [conditions, setConditions]           = useState<ConditionsMap>(initialConditions)
  const [results, setResults]                 = useState<WorkerSimulationResult[]>([])
  const [isCalculating, setIsCalculating]     = useState(false)
  const [errorMessage, setErrorMessage]       = useState<string | null>(null)

  const workerRef       = useRef<Worker | null>(null)
  const debounceRef     = useRef<number | null>(null)
  const pendingCountRef = useRef<number>(simCount)

  const resultMap = useMemo(
    () => results.reduce<Record<number, WorkerSimulationResult>>((map, r) => {
      map[r.horse_id] = r
      return map
    }, {}),
    [results],
  )

  const runSimulation = useCallback((conds: ConditionsMap, n: number) => {
    if (!workerRef.current) return

    const horses: WorkerHorseInput[] = sortedPredictions.map((p) => ({
      horse_id:        p.horseId,
      horse_name:      p.horseName,
      win_prob:        toWorkerProbability(p.winProbability),
      gate_no:         p.gateNo ?? 0,
      odds_win:        null,
      prob_adjustment: computeProbAdjustment(conds[p.horseId] ?? defaultConditions()),
    }))

    const input: WorkerSimulationInput = { horses, n_simulations: n }
    pendingCountRef.current = n
    setIsCalculating(true)
    setErrorMessage(null)
    workerRef.current.postMessage(input)
  }, [sortedPredictions])

  useEffect(() => {
    workerRef.current = new Worker(
      new URL('../../workers/monte-carlo.worker.ts', import.meta.url),
      { type: 'module' },
    )

    workerRef.current.onmessage = (event: MessageEvent<WorkerMessage>) => {
      if (event.data.type === 'error') {
        setErrorMessage(event.data.message)
        setIsCalculating(false)
        return
      }
      setResults(event.data.results)
      setCompletedCount(pendingCountRef.current)
      setIsCalculating(false)
    }

    runSimulation(initialConditions, simCount)

    return () => {
      if (debounceRef.current != null) window.clearTimeout(debounceRef.current)
      workerRef.current?.terminate()
      workerRef.current = null
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // initialConditions 변경 시 내부 state 동기화
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setConditions(initialConditions) }, [initialConditions])

  const scheduleSimulation = (nextConds: ConditionsMap, n: number) => {
    if (debounceRef.current != null) window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(() => {
      runSimulation(nextConds, n)
    }, 350)
  }

  const handleConditionChange = (
    horseId: number,
    key: keyof HorseConditions,
    value: number,
  ) => {
    const nextConditions = {
      ...conditions,
      [horseId]: { ...(conditions[horseId] ?? defaultConditions()), [key]: value },
    }
    setConditions(nextConditions)
    scheduleSimulation(nextConditions, simCount)
  }

  const handleSimCountChange = (n: number) => {
    setSimCount(n)
    runSimulation(conditions, n)
  }

  const handleReset = () => {
    setConditions(initialConditions)
    setCompletedCount(null)
    runSimulation(initialConditions, simCount)
  }

  if (!sortedPredictions.length) {
    return (
      <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 text-sm text-white/65">
        가상 시나리오를 계산할 예측 데이터가 없습니다.
      </section>
    )
  }

  return (
    <section className="space-y-5">
      {/* 헤더 */}
      <div className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5 lg:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm tracking-[0.18em] text-brand-gold-400">가상 분석</p>
            <h2 className="mt-2 font-heading text-3xl text-white">가상 시나리오 분석</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-white/65">
              기수 능력·마체중·트랙·날씨 4가지 조건을 말별로 조정하면,
              가상 경주를 N회 반복해 순위 분포가 어떻게 바뀌는지 보여줍니다.
            </p>
          </div>

          <div className="flex shrink-0 flex-col items-end gap-3">
            {/* 횟수 프리셋 */}
            <div className="flex flex-col items-end gap-1.5">
              <p className="text-xs text-white/45">시뮬레이션 횟수</p>
              <div className="flex gap-1.5">
                {SIM_PRESETS.map((preset) => (
                  <button
                    key={preset.value}
                    type="button"
                    disabled={isCalculating}
                    onClick={() => handleSimCountChange(preset.value)}
                    className={[
                      'rounded-full px-3 py-1.5 text-xs font-semibold transition disabled:opacity-40',
                      simCount === preset.value
                        ? 'bg-brand-gold-400 text-brand-navy-950'
                        : 'border border-white/15 text-white/60 hover:bg-white/8',
                    ].join(' ')}
                  >
                    {preset.label}
                  </button>
                ))}
              </div>
            </div>

            {/* 완료 배지 */}
            {!isCalculating && completedCount != null && (
              <span className="rounded-full bg-brand-gold-400/15 px-3 py-1 text-xs font-semibold text-brand-gold-400">
                {completedCount.toLocaleString()}회 시뮬레이션 완료
              </span>
            )}

            <button
              type="button"
              onClick={handleReset}
              className="rounded-full border border-brand-gold-400/40 px-4 py-2 text-sm font-semibold text-brand-gold-400 transition hover:bg-brand-gold-400 hover:text-brand-navy-950"
            >
              초기화
            </button>
          </div>
        </div>
      </div>

      {isCalculating && <LoadingAnimation />}

      {errorMessage && (
        <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
          {errorMessage}
        </div>
      )}

      {/* 말별 카드 */}
      <div className="grid gap-4">
        {sortedPredictions.map((prediction) => {
          const baseProbability    = prediction.winProbability ?? 0
          const result             = resultMap[prediction.horseId]
          const adjustedProbability = result ? result.win_prob_adjusted * 100 : baseProbability
          const delta              = adjustedProbability - baseProbability
          const isUp               = delta >= 0
          const cond               = conditions[prediction.horseId] ?? defaultConditions()

          // 해당 말의 조건이 하나라도 변경됐는지 확인
          const hasChanged = Object.values(cond).some((v) => v !== 0)

          return (
            <article key={prediction.horseId} className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
              {/* 말 이름 + 변화량 */}
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-xs tracking-[0.16em] text-white/45">게이트 {prediction.gateNo ?? '-'}번</p>
                  <h3 className="mt-1 font-heading text-2xl text-white">{prediction.horseName}</h3>
                </div>
                <div className="flex items-center gap-2">
                  {hasChanged && (
                    <span className={[
                      'rounded-full px-3 py-1 text-sm font-semibold',
                      isUp ? 'bg-brand-gold-400/15 text-brand-gold-400' : 'bg-red-400/15 text-red-300',
                    ].join(' ')}>
                      {isUp ? '▲' : '▼'} {formatDelta(delta)}
                    </span>
                  )}
                  {!hasChanged && (
                    <span className="rounded-full bg-white/5 px-3 py-1 text-sm text-white/35">조정 없음</span>
                  )}
                </div>
              </div>

              <div className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.7fr)]">
                {/* 조건 슬라이더 */}
                <div className="space-y-5">
                  {CONDITION_DEFS.map((def) => (
                    <ConditionSlider
                      key={def.key}
                      def={def}
                      value={cond[def.key]}
                      onChange={(v) => handleConditionChange(prediction.horseId, def.key, v)}
                    />
                  ))}

                  {/* 기본 vs 조정 후 확률 막대 */}
                  <div className="grid gap-3 pt-1 sm:grid-cols-2">
                    <WinProbabilityBar probability={baseProbability}    label="기본 우승 확률" />
                    <WinProbabilityBar probability={adjustedProbability} label="조정 후 우승 확률" />
                  </div>
                </div>

                {/* 순위 분포 */}
                <div className="grid content-start gap-3 rounded-2xl border border-white/10 bg-brand-navy-950/45 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white/55">평균 예상 순위</span>
                    <span className="font-mono text-xl text-white">
                      {result ? `${result.expected_rank.toFixed(2)}위` : '-'}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-center">
                    {(['1', '2', '3', '4+'] as const).map((rankKey) => (
                      <div key={rankKey} className="rounded-xl bg-white/5 p-3">
                        <p className="text-xs text-white/45">{rankKey}위</p>
                        <p className="mt-1 font-mono text-sm text-white">
                          {result ? `${result.rank_distribution[rankKey].toFixed(1)}%` : '-'}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </article>
          )
        })}
      </div>
    </section>
  )
}

export default CounterfactualUI
