# Copula 상관행렬 — 학습 문서

> RacePulse Phase 3 / 작성일: 2026-05-15
> 난이도: ★★★★☆ (Phase 3 선택 항목 — 시간 허용 시 구현)

---

## 1. 지금까지의 MC가 놓치는 것

Phase 2 MC에서 각 말은 **서로 독립**이라고 가정합니다.

```
말 A가 1위할 확률 = 34%
말 B가 1위할 확률 = 28%
→ 서로 영향 없음 (독립 가정)
```

하지만 현실은 다릅니다.

> **"같은 조교사 밑의 두 말은 훈련 환경이 같아서 같이 좋은 날, 같이 나쁜 날이 있다"**
> **"비 오는 날에는 특정 혈통 말들이 동시에 성적이 좋다"**

즉, 말들 사이에는 **숨겨진 상관관계**가 있습니다.
Copula는 이 공동 의존성을 모델링하는 도구입니다.

---

## 2. Copula란?

**"각 말의 순위 확률 분포를 유지하면서, 말들 간의 상관관계를 추가로 붙이는 수학적 도구"**

Sklar의 정리:

```
모든 결합 분포 = 각 주변 분포 + Copula (상관 구조)
```

쉬운 비유:

```
각 말의 예측 확률 = 각 악기의 악보
Copula            = 그 악기들이 어떻게 함께 연주되는지 (하모니)
```

---

## 3. RacePulse에서 쓸 Copula: Gaussian Copula

가장 직관적이고 구현이 쉬운 Gaussian Copula를 사용합니다.

### 상관행렬 정의

말들 사이의 상관계수 ρ (rho) 행렬을 만듭니다.

```
      말A  말B  말C
말A [  1   0.6  0.2 ]
말B [ 0.6   1   0.1 ]
말C [ 0.2  0.1   1  ]
```

`ρ(A,B) = 0.6` → "말A와 말B는 꽤 함께 잘하는 경향"

### 상관계수 계산 기준

| 기준 | 상관계수 증가 요인 |
|------|-------------------|
| 같은 조교사 | +0.15 |
| 같은 혈통 (부마 동일) | +0.1 |
| 같은 경마장 출신 | +0.05 |
| 역대 동반 출전 성적 유사 | 계산값 |

### 시뮬레이션 방법 (Cholesky 분해)

```python
import numpy as np

# 상관행렬 Σ (예: 5마리)
Σ = build_correlation_matrix(entries)  # rival_records, trainer 등으로 계산

# Cholesky 분해 (이미 Phase 2 MC에 구현됨!)
L = np.linalg.cholesky(Σ)

# 상관있는 정규 난수 생성
Z = np.random.standard_normal(n_horses)
X = L @ Z  # 상관구조 적용

# 확률값으로 변환
from scipy.stats import norm
U = norm.cdf(X)  # 0~1 사이 균등분포로 변환

# 각 말의 순위 확률에 매핑
rank_probs = [inverse_cdf(u, horse_prior) for u, horse_prior in zip(U, priors)]
```

> **Phase 2 MC에 이미 Cholesky 분해가 구현되어 있습니다!**
> `monte_carlo.py`의 게이트 상관행렬 파트가 바로 이 구조입니다.
> Phase 3에서는 게이트 편향뿐 아니라 말-말 상관관계까지 확장하는 것입니다.

---

## 4. Bayesian · Sequential과의 관계

```
ML 모델 예측 (v3.0)
    ↓
Bayesian 업데이트 → 과거 결과 반영한 prior
    ↓
Sequential 업데이트 → 당일 트랙/컨디션 반영
    ↓
Copula 적용 → 말들 간 상관구조 반영
    ↓
최종 MC 시뮬레이션 결과
```

세 가지가 **레이어드**로 쌓이는 구조입니다.

---

## 5. 난이도와 기대 효과

| 항목 | 내용 |
|------|------|
| 구현 난이도 | ★★★★☆ — Cholesky는 이미 있으나 상관행렬 계산 로직 신설 필요 |
| 기대 정확도 향상 | 낮음~중간 (Top-3에서 체감 어려울 수 있음) |
| 포트폴리오 임팩트 | 높음 — "Copula 기반 MC" 는 실제 퀀트 금융에서 쓰는 기법 |
| 데이터 의존성 | rival_records (이미 538,717쌍 보유) 활용 가능 |

---

## 6. 참고 자료

- Sklar's Theorem (1959) — Copula의 수학적 기반
- [scipy.stats 문서](https://docs.scipy.org/doc/scipy/reference/stats.html) — norm, multivariate_normal
- RacePulse 기존 구현: `racepulse/ml-server/app/services/monte_carlo.py` (Cholesky 게이트 파트)
