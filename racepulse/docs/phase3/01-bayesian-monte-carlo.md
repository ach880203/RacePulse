# Bayesian Monte Carlo — 학습 문서

> RacePulse Phase 3 / 작성일: 2026-05-15

---

## 1. 왜 Bayesian인가?

### 기존 Monte Carlo의 한계

Phase 2 MC는 **매 경주를 독립적**으로 시뮬레이션합니다.

```
경주 A → MC 시뮬레이션 (독립)
경주 B → MC 시뮬레이션 (독립)
경주 C → MC 시뮬레이션 (독립)
```

즉, "지난 경주에서 1위를 했다"는 정보가 다음 예측에 반영되지 않습니다.
현실에서 말의 컨디션은 연속적으로 이어집니다.

### Bayesian 업데이트의 아이디어

**"이전 결과를 보고 믿음을 업데이트한다"**

```
사전 확률 (Prior)    = ML 모델이 예측한 확률 (v3.0 XGBoost + LightGBM)
관측값   (Likelihood) = 실제 경주 결과 (착순)
사후 확률 (Posterior) = 업데이트된 예측 확률
```

수식:

```
P(우승 | 최근결과) ∝ P(최근결과 | 우승확률) × P(우승확률)
```

쉽게 말하면:
- 모델이 "이 말은 30% 확률로 1위"라고 했는데
- 최근 3경주에서 모두 1위를 했다면
- Bayesian 업데이트 후 → "37%로 상향"

---

## 2. Beta-Binomial 모델 (실제 구현 방식)

RacePulse에서 쓸 가장 간단하고 효율적인 방법입니다.

### 왜 Beta-Binomial인가?

- "1위를 할 확률"이 0~1 사이 → **Beta 분포**가 이를 모델링하기 딱 좋음
- "1위를 했다/안 했다"는 이진 결과 → **Binomial** 분포
- 이 둘은 **켤레 분포(Conjugate pair)** — 계산식이 닫힌 형태로 나옴 (시뮬레이션 없이 O(1))

### 파라미터

```
Beta(α, β) 에서

α = 사전 확률 × 가중치 + 최근 1위 횟수
β = (1 - 사전 확률) × 가중치 + 최근 비1위 횟수
```

### 예시

```python
# 모델 사전 확률: 30% (α_prior=3, β_prior=7 로 스케일링)
prior_alpha = 0.30 * 10  # = 3.0
prior_beta  = 0.70 * 10  # = 7.0

# 최근 3경주 결과: 1위, 2위, 1위 → 1위 2회, 비1위 1회
wins   = 2
losses = 1

# 사후 파라미터
posterior_alpha = prior_alpha + wins    # 3 + 2 = 5
posterior_beta  = prior_beta  + losses  # 7 + 1 = 8

# 사후 기댓값 (업데이트된 확률)
posterior_mean = posterior_alpha / (posterior_alpha + posterior_beta)
# = 5 / 13 ≈ 0.385 → 38.5%로 상향!
```

### 구현 위치

```
ml-server/app/services/bayesian_updater.py  ← 신설
ml-server/app/services/monte_carlo.py       ← prior 주입 방식 수정
```

---

## 3. 언제 업데이트되나?

```
월요일 14:00  → 주말 경기 결과 수집
                ↓
              BayesianUpdater.update(horse_id, race_result)
                ↓
              prediction_accuracy_logs 기록
                ↓
              다음 경주 MC 시뮬레이션 시 업데이트된 prior 사용
```

---

## 4. 주의사항

- **과거 데이터가 적은 말**: prior에 더 많이 의존 → 가중치(`가중치` = 10) 조정 가능
- **오래된 결과**: 최근 5경주까지만 반영, 그 이전은 지수감쇠로 가중치 낮춤
- **데뷔마**: prior = ML 모델 예측값 100% (Bayesian 업데이트 없음)

---

## 5. 유저에게 어떻게 보이나?

```
기존: "1위 확률: 30%"
Phase 3: "1위 확률: 38.5% (최근 3경주 반영)"
```

FE에서 Bayesian 업데이트 적용 여부를 작은 아이콘으로 표시 (동적 UI 27번).
