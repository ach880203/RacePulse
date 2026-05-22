// =============================================================================
// CounterfactualUI.tsx — 가상 시나리오 분석 UI
// =============================================================================
// Counterfactual(반사실적 분석)이란?
//   "이미 알고 있는 기본 예측에서 조건 하나가 달랐다면 결과가 어떻게 바뀌었을까?"를 보는 분석입니다.
//   예: 기수가 바뀌었다면, 마체중이 줄었다면, 트랙이 젖었다면 같은 질문을 숫자로 비교합니다.
// =============================================================================

import { useCallback, useEffect, useMemo, useRef, useState } from 'react' // React 상태, 생명주기, 메모리 보관 기능을 사용합니다.

import LoadingAnimation from './LoadingAnimation' // Worker 계산 중 화면에 보여 줄 말 달리기 로딩 애니메이션입니다.
import WinProbabilityBar from './WinProbabilityBar' // 기본/조정 후 우승 확률 막대를 그릴 때 재사용하는 컴포넌트입니다.
import type { PredictionItem } from '../../types/prediction' // 예측 API에서 받은 말별 기본 예측 타입입니다.

// Worker로 보낼 말 1마리 입력 타입입니다.
// 화면 타입과 Worker 타입을 맞추면 postMessage로 잘못된 데이터를 보내는 실수를 줄일 수 있습니다.
interface WorkerHorseInput {
  horse_id: number
  horse_name: string
  win_prob: number
  gate_no: number
  odds_win: number | null
  prob_adjustment: number
}

// Worker 전체 입력 타입입니다.
// n_simulations는 계산 정확도와 속도의 균형을 정하는 반복 횟수입니다.
interface WorkerSimulationInput {
  horses: WorkerHorseInput[]
  n_simulations: number
}

// Worker가 돌려주는 등수 분포 타입입니다.
// 4등 이하는 화면을 단순하게 유지하기 위해 "4+"로 묶습니다.
interface WorkerRankDistribution {
  '1': number
  '2': number
  '3': number
  '4+': number
}

// Worker가 돌려주는 말별 계산 결과 타입입니다.
// win_prob_adjusted는 사용자가 조정한 뒤 다시 정규화된 우승 확률입니다.
interface WorkerSimulationResult {
  horse_id: number
  rank_distribution: WorkerRankDistribution
  expected_rank: number
  win_prob_adjusted: number
}

// Worker 성공/실패 메시지를 구분하는 타입입니다.
// type 값으로 분기하면 오류 메시지도 안전하게 처리할 수 있습니다.
type WorkerMessage =
  | { type: 'success'; results: WorkerSimulationResult[] }
  | { type: 'error'; message: string }

// 컴포넌트가 부모에게 받는 값입니다.
// predictions는 기본 예측 데이터이며, 이 데이터에서 가상 시나리오 입력을 만듭니다.
interface CounterfactualUIProps {
  predictions: PredictionItem[]
}

// 화면에서 조정값을 빠르게 찾기 위해 말 ID를 key로 쓰는 객체 타입입니다.
type AdjustmentMap = Record<number, number>

// 10,000번은 브라우저에서도 빠르게 돌면서 변화 방향을 확인하기에 충분한 기본값입니다.
const DEFAULT_SIMULATION_COUNT = 10_000

function toPercentValue(probability: number | null): number {
  // 백엔드 값이 null이면 아직 예측값이 없다는 뜻이므로 화면 계산에서는 0으로 안전하게 처리합니다.
  return probability ?? 0
}

function toWorkerProbability(percentValue: number): number {
  // 화면의 35.0% 같은 값을 Worker가 쓰기 쉬운 0.35 소수로 바꿉니다.
  return Math.max(0, Math.min(1, percentValue / 100))
}

function formatDelta(delta: number): string {
  // 변화량은 항상 부호를 보여 줘야 상승/하락을 빠르게 읽을 수 있습니다.
  return `${delta >= 0 ? '+' : ''}${delta.toFixed(1)}%`
}

function CounterfactualUI({ predictions }: CounterfactualUIProps) {
  const sortedPredictions = useMemo(() => {
    // 원본 배열을 직접 정렬하면 부모 컴포넌트 데이터 순서가 바뀔 수 있어 복사본을 정렬합니다.
    return [...predictions].sort((a, b) => a.predictedRank - b.predictedRank)
  }, [predictions])

  const initialAdjustments = useMemo(() => {
    // 모든 말을 0% 조정 상태로 시작합니다.
    return sortedPredictions.reduce<AdjustmentMap>((map, prediction) => {
      map[prediction.horseId] = 0
      return map
    }, {})
  }, [sortedPredictions])

  const [scenarioName, setScenarioName] = useState('기수 변경 시나리오')
  const [adjustments, setAdjustments] = useState<AdjustmentMap>(initialAdjustments)
  const [results, setResults] = useState<WorkerSimulationResult[]>([])
  const [isCalculating, setIsCalculating] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  // useRef는 화면이 다시 그려져도 같은 Worker 인스턴스를 보관하기 위해 사용합니다.
  // Worker를 매 렌더마다 새로 만들면 이전 계산을 잃고 브라우저 자원도 낭비됩니다.
  const workerRef = useRef<Worker | null>(null)

  // debounceTimerRef는 슬라이더가 움직이는 동안 계산을 잠깐 미루기 위해 사용합니다.
  // 사용자가 1%씩 움직일 때마다 10,000번 계산하면 Worker라도 불필요한 작업이 너무 많아집니다.
  const debounceTimerRef = useRef<number | null>(null)

  const resultMap = useMemo(() => {
    return results.reduce<Record<number, WorkerSimulationResult>>((map, result) => {
      map[result.horse_id] = result
      return map
    }, {})
  }, [results])

  const runWorkerSimulation = useCallback((nextAdjustments: AdjustmentMap) => {
    if (!workerRef.current) {
      return
    }

    const horses: WorkerHorseInput[] = sortedPredictions.map((prediction) => ({
      horse_id: prediction.horseId,
      horse_name: prediction.horseName,
      win_prob: toWorkerProbability(toPercentValue(prediction.winProbability)),
      gate_no: prediction.gateNo ?? 0,
      odds_win: null,
      prob_adjustment: (nextAdjustments[prediction.horseId] ?? 0) / 100,
    }))

    const input: WorkerSimulationInput = {
      horses,
      n_simulations: DEFAULT_SIMULATION_COUNT,
    }

    setIsCalculating(true)
    setErrorMessage(null)
    workerRef.current.postMessage(input)
  }, [sortedPredictions])

  useEffect(() => {
    // Vite는 new URL(..., import.meta.url) 형태를 보고 Worker 파일을 별도 번들로 묶어 줍니다.
    workerRef.current = new Worker(new URL('../../workers/monte-carlo.worker.ts', import.meta.url), {
      type: 'module',
    })

    workerRef.current.onmessage = (event: MessageEvent<WorkerMessage>) => {
      if (event.data.type === 'error') {
        setErrorMessage(event.data.message)
        setIsCalculating(false)
        return
      }

      setResults(event.data.results)
      setIsCalculating(false)
    }

    runWorkerSimulation(initialAdjustments)

    return () => {
      if (debounceTimerRef.current != null) {
        window.clearTimeout(debounceTimerRef.current)
      }

      // 화면을 떠날 때 Worker를 종료해야 보이지 않는 계산이 계속 돌지 않습니다.
      workerRef.current?.terminate()
      workerRef.current = null
    }
  }, [initialAdjustments, runWorkerSimulation])

  // initialAdjustments(부모에서 내려온 초기값)이 바뀌면 내부 슬라이더 상태를 동기화합니다.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { setAdjustments(initialAdjustments) }, [initialAdjustments])

  const scheduleSimulation = (nextAdjustments: AdjustmentMap) => {
    if (debounceTimerRef.current != null) {
      window.clearTimeout(debounceTimerRef.current)
    }

    // debounce는 "마지막 조작 후 잠깐 기다렸다가 한 번만 실행"하는 처리입니다.
    // 슬라이더 드래그 중에는 숫자만 즉시 바꾸고, 계산은 사용자가 멈춘 뒤 실행합니다.
    debounceTimerRef.current = window.setTimeout(() => {
      runWorkerSimulation(nextAdjustments)
    }, 350)
  }

  const handleAdjustmentChange = (horseId: number, value: number) => {
    const nextAdjustments = {
      ...adjustments,
      [horseId]: value,
    }

    setAdjustments(nextAdjustments)
    scheduleSimulation(nextAdjustments)
  }

  const handleReset = () => {
    setScenarioName('기수 변경 시나리오')
    setAdjustments(initialAdjustments)
    runWorkerSimulation(initialAdjustments)
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
      <div className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-5 lg:p-6">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm tracking-[0.18em] text-brand-gold-400">가상 분석</p>
            <h2 className="mt-2 font-heading text-3xl text-white">가상 시나리오 분석</h2>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-white/65">
              말별 우승 확률을 조정해 조건이 달라졌을 때 예상 순위 분포가 어떻게 바뀌는지 확인합니다.
            </p>
          </div>

          <button
            type="button"
            onClick={handleReset}
            className="w-fit rounded-full border border-brand-gold-400/40 px-4 py-2 text-sm font-semibold text-brand-gold-400 transition hover:bg-brand-gold-400 hover:text-brand-navy-950"
          >
            초기화
          </button>
        </div>

        <label className="mt-5 block">
          <span className="text-sm text-white/60">시나리오 이름</span>
          <input
            value={scenarioName}
            onChange={(event) => setScenarioName(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-white/10 bg-brand-navy-950/70 px-4 py-3 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-brand-gold-400/70"
            placeholder="예: 날씨 변화 시나리오"
          />
        </label>
      </div>

      {isCalculating && <LoadingAnimation />}

      {errorMessage && (
        <div className="rounded-2xl border border-red-400/20 bg-red-400/10 p-4 text-sm text-red-300">
          {errorMessage}
        </div>
      )}

      <div className="grid gap-4">
        {sortedPredictions.map((prediction) => {
          const baseProbability = toPercentValue(prediction.winProbability)
          const result = resultMap[prediction.horseId]
          const adjustedProbability = result ? result.win_prob_adjusted * 100 : baseProbability
          const delta = adjustedProbability - baseProbability
          const isUp = delta >= 0

          return (
            <article key={prediction.horseId} className="rounded-[2rem] border border-white/10 bg-white/5 p-5">
              <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(18rem,0.7fr)]">
                <div className="space-y-5">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div>
                      <p className="text-xs tracking-[0.16em] text-white/45">게이트 {prediction.gateNo ?? '-'}번</p>
                      <h3 className="mt-1 font-heading text-2xl text-white">{prediction.horseName}</h3>
                    </div>
                    <span className={`w-fit rounded-full px-3 py-1 text-sm font-semibold ${isUp ? 'bg-brand-gold-400/15 text-brand-gold-400' : 'bg-red-400/15 text-red-300'}`}>
                      {isUp ? '▲' : '▼'} {formatDelta(delta)}
                    </span>
                  </div>

                  <div className="grid gap-4 lg:grid-cols-2">
                    <WinProbabilityBar probability={baseProbability} label="기본 우승 확률" />
                    <WinProbabilityBar probability={adjustedProbability} label="조정 후 우승 확률" />
                  </div>

                  <label className="block">
                    <div className="mb-2 flex items-center justify-between text-sm">
                      <span className="text-white/65">승률 조정</span>
                      <span className="font-mono text-brand-gold-400">{formatDelta(adjustments[prediction.horseId] ?? 0)}</span>
                    </div>
                    <input
                      type="range"
                      min="-50"
                      max="50"
                      step="1"
                      value={adjustments[prediction.horseId] ?? 0}
                      onChange={(event) => handleAdjustmentChange(prediction.horseId, Number(event.target.value))}
                      className="w-full accent-brand-gold-500"
                    />
                  </label>
                </div>

                <div className="grid gap-3 rounded-2xl border border-white/10 bg-brand-navy-950/45 p-4">
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
