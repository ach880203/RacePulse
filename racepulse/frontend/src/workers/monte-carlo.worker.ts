// =============================================================================
// monte-carlo.worker.ts — 브라우저 안에서 따로 실행되는 Monte Carlo 계산 작업실
// =============================================================================
// Web Worker란?
//   화면을 그리는 메인 스레드와 분리된 "별도 작업실"입니다.
//   계산이 오래 걸려도 버튼 클릭, 슬라이더 이동, 스크롤 같은 화면 동작이 멈추지 않습니다.
//
// postMessage / onmessage란?
//   메인 화면과 Worker는 서로 직접 함수를 호출하지 못합니다.
//   대신 postMessage로 편지를 보내고, onmessage로 편지를 받아 처리합니다.
// =============================================================================

// Worker 입력 말 타입입니다.
// horse_id = 백엔드/ML 데이터에서 내려온 말 고유 번호입니다.
// horse_name = 화면에 표시할 말 이름입니다.
// win_prob = 기본 우승 확률이며 0~1 사이 소수로 받습니다.
// gate_no = 출발 게이트 번호입니다.
// odds_win = 단승 배당이며 아직 없으면 null일 수 있습니다.
// prob_adjustment = 사용자가 가상 시나리오 슬라이더로 더하거나 뺀 확률입니다.
interface SimulationHorseInput {
  horse_id: number
  horse_name: string
  win_prob: number
  gate_no: number
  odds_win: number | null
  prob_adjustment: number
}

// Worker 전체 입력 타입입니다.
// horses = 이번 경주에 출전하는 말 목록입니다.
// n_simulations = 몇 번 반복해서 가상 경주를 돌릴지 정하는 숫자입니다.
interface SimulationInput {
  horses: SimulationHorseInput[]
  n_simulations: number
}

// 각 말의 등수 분포 타입입니다.
// "4+"는 4등 이하를 한 묶음으로 보여 주기 위한 표시입니다.
interface RankDistribution {
  '1': number
  '2': number
  '3': number
  '4+': number
}

// Worker가 화면으로 돌려주는 말별 결과 타입입니다.
// expected_rank = 여러 번 돌린 결과의 평균 예상 등수입니다.
// win_prob_adjusted = 조정값을 반영한 최종 우승 확률입니다.
interface SimulationResult {
  horse_id: number
  rank_distribution: RankDistribution
  expected_rank: number
  win_prob_adjusted: number
}

// Worker 성공 응답 타입입니다.
// type을 붙이면 화면에서 "성공 응답인지, 실패 응답인지" 안전하게 구분할 수 있습니다.
interface SimulationSuccessMessage {
  type: 'success'
  results: SimulationResult[]
}

// Worker 실패 응답 타입입니다.
// message에는 화면에 바로 보여 줄 수 있는 한글 오류 문구를 담습니다.
interface SimulationErrorMessage {
  type: 'error'
  message: string
}

// Math.random 결과가 0에 가까울 때 계산이 너무 치우치지 않도록 최소값을 둡니다.
const MIN_WEIGHT = 0.001

function clamp(value: number, min: number, max: number): number {
  // clamp는 숫자가 정해진 범위를 벗어나지 않게 잘라내는 작은 안전장치입니다.
  return Math.min(max, Math.max(min, value))
}

function normalizeWeights(horses: SimulationHorseInput[]): number[] {
  // 사용자가 여러 말의 확률을 동시에 올리거나 내리면 전체 합이 1이 아닐 수 있습니다.
  // Monte Carlo 추첨은 상대 비율이 필요하므로, 합계로 나눠 다시 1에 가까운 비율로 맞춥니다.
  const adjustedWeights = horses.map((horse) => {
    return clamp(horse.win_prob + horse.prob_adjustment, MIN_WEIGHT, 1)
  })
  const totalWeight = adjustedWeights.reduce((sum, weight) => sum + weight, 0)

  if (totalWeight <= 0) {
    return horses.map(() => 1 / Math.max(1, horses.length))
  }

  return adjustedWeights.map((weight) => weight / totalWeight)
}

function drawWeightedIndex(weights: number[], usedIndexes: Set<number>): number {
  // 아직 뽑히지 않은 말들의 가중치 합만 사용해야 같은 말이 1등과 2등에 동시에 나오지 않습니다.
  const availableWeight = weights.reduce((sum, weight, index) => {
    return usedIndexes.has(index) ? sum : sum + weight
  }, 0)
  let randomPoint = Math.random() * availableWeight

  for (let index = 0; index < weights.length; index += 1) {
    if (usedIndexes.has(index)) {
      continue
    }

    randomPoint -= weights[index]

    if (randomPoint <= 0) {
      return index
    }
  }

  // 아주 드문 부동소수점 오차 상황에서는 마지막 남은 말을 반환합니다.
  return weights.findIndex((_, index) => !usedIndexes.has(index))
}

function runSimulation(input: SimulationInput): SimulationResult[] {
  const simulationCount = clamp(input.n_simulations, 10_000, 50_000)
  const weights = normalizeWeights(input.horses)
  const rankBuckets = input.horses.map(() => ({ '1': 0, '2': 0, '3': 0, '4+': 0 }))
  const rankSums = input.horses.map(() => 0)

  for (let simulationIndex = 0; simulationIndex < simulationCount; simulationIndex += 1) {
    const usedIndexes = new Set<number>()

    for (let rank = 1; rank <= input.horses.length; rank += 1) {
      const horseIndex = drawWeightedIndex(weights, usedIndexes)
      usedIndexes.add(horseIndex)
      rankSums[horseIndex] += rank

      if (rank === 1) {
        rankBuckets[horseIndex]['1'] += 1
      } else if (rank === 2) {
        rankBuckets[horseIndex]['2'] += 1
      } else if (rank === 3) {
        rankBuckets[horseIndex]['3'] += 1
      } else {
        rankBuckets[horseIndex]['4+'] += 1
      }
    }
  }

  return input.horses.map((horse, index) => ({
    horse_id: horse.horse_id,
    rank_distribution: {
      '1': (rankBuckets[index]['1'] / simulationCount) * 100,
      '2': (rankBuckets[index]['2'] / simulationCount) * 100,
      '3': (rankBuckets[index]['3'] / simulationCount) * 100,
      '4+': (rankBuckets[index]['4+'] / simulationCount) * 100,
    },
    expected_rank: rankSums[index] / simulationCount,
    win_prob_adjusted: weights[index],
  }))
}

self.onmessage = (event: MessageEvent<SimulationInput>) => {
  try {
    const results = runSimulation(event.data)
    const message: SimulationSuccessMessage = {
      type: 'success',
      results,
    }

    self.postMessage(message)
  } catch {
    const message: SimulationErrorMessage = {
      type: 'error',
      message: '가상 시나리오 계산 중 오류가 발생했습니다.',
    }

    self.postMessage(message)
  }
}

export {}
