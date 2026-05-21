# 30. RacePulse Bayesian Monte Carlo 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

이 프롬프트를 실행하기 **전에** 아래 파일들을 순서대로 전부 읽어야 합니다.

```
1. horse_racing_team.md           ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md        ← Phase 2 전체 기록, MC 구현 내용
3. horse_racing_team_v3.md        ← Phase 3 킥오프, 14차 회의 확정사항
4. docs/PROJECT_RULES.md          ← 코딩 규칙 20개
5. docs/phase3/01-bayesian-monte-carlo.md  ← Bayesian 학습 문서 (필수!)
```

---

## 🗂️ 지금까지 한 작업 요약 (컨텍스트)

### Phase 2 Monte Carlo 구현 완료 내역
- `ml-server/app/services/monte_carlo.py`: QMC(Sobol) + Antithetic Variates + **Cholesky 게이트 상관행렬** 구현
- Adaptive 수렴 (10k~100k, CI ±0.5% 기준), 병렬 4코어
- 게이트 브레이크 / 날씨 불확실성 / 스마트 머니 탐지 / 신뢰도 점수

### Phase 3에서 추가하는 것 (이 프롬프트)
Phase 2 MC는 매 경주를 **독립적**으로 예측합니다.
말의 최근 경주 결과가 다음 예측에 전혀 반영되지 않는 문제가 있습니다.

**Bayesian 업데이트**로 이 문제를 해결합니다:
- 말의 최근 5경주 결과를 Beta-Binomial 모델로 반영
- ML 모델 예측값이 prior → 경주 결과로 posterior 업데이트
- 업데이트된 posterior가 MC의 시작 확률(prior)로 주입

---

## 목표

두 개의 파일을 작성합니다:

1. **신규**: `ml-server/app/services/bayesian_updater.py`
   - BayesianUpdater 클래스: Beta-Binomial 모델로 말 우승 확률 업데이트

2. **수정**: `ml-server/app/services/monte_carlo.py`
   - 기존 MC에 Bayesian prior 주입 기능 추가 (기존 로직 최대한 유지)

---

## 프로젝트 환경

- **ML 서버**: FastAPI / Python 3.11
- **현재 경로**: `racepulse/ml-server/app/services/`
- **의존성**: numpy, scipy (이미 설치됨)
- **DB**: PostgreSQL — race_results, prediction_accuracy_logs 테이블 활용

---

## 현재 파일 구조

```
ml-server/app/services/
├── monte_carlo.py          ← Phase 2 구현 완료 — 이 파일 수정
├── prediction_service.py   ← MC 호출하는 서비스
├── data_collector.py
├── feature_engineer.py
└── (bayesian_updater.py)   ← 이 파일 신규 생성
```

---

## 구현 사항

### 파일 1: `bayesian_updater.py` (신규)

```python
# -*- coding: utf-8 -*-
"""
bayesian_updater.py — 말 우승 확률 Bayesian 업데이트
=======================================================
Phase 2 MC는 각 경주를 독립적으로 예측했습니다.
이 모듈은 말의 최근 경주 결과를 반영해 ML 예측값을 보정합니다.

수학적 배경: Beta-Binomial 켤레 분포
  - Prior: Beta(α, β) — ML 모델 예측 확률
  - Likelihood: Binomial — 실제 경주 결과 (1위/비1위)
  - Posterior: Beta(α + wins, β + losses)

장점: 시뮬레이션 없이 O(1)로 계산 가능 (닫힌 형태)
"""
```

**BayesianUpdater 클래스:**

```python
class BayesianUpdater:
    def __init__(self, db_session, prior_weight: float = 10.0, max_races: int = 5):
        """
        prior_weight: ML 예측값에 부여하는 가중치 (클수록 ML 예측에 의존)
                      데이터가 적은 말일수록 prior에 의존 → 기본값 10.0
        max_races: 최근 N경주만 반영 (오래된 결과 제외)
        """
```

**주요 메서드:**

1. `update_single_horse(horse_id, prior_prob, recent_results) -> float`
   ```python
   # prior_prob: ML 모델의 예측 확률 (0~1)
   # recent_results: [(race_date, position), ...] 최신순 정렬
   # 반환값: Bayesian 업데이트된 우승 확률 (0~1)
   
   # Beta 파라미터 계산
   alpha = prior_prob * prior_weight
   beta  = (1 - prior_prob) * prior_weight
   
   # 최근 결과 반영 (지수감쇠 가중치 — 오래된 경주일수록 영향 줄임)
   # decay = 0.9^n (n=0이 가장 최근, n=4가 가장 오래된 것)
   for i, (race_date, position) in enumerate(recent_results[:max_races]):
       decay = 0.9 ** i
       if position == 1:  # 1위
           alpha += 1.0 * decay
       else:              # 비1위
           beta  += 1.0 * decay
   
   # 사후 기댓값 = 업데이트된 우승 확률
   return alpha / (alpha + beta)
   ```

2. `update_race_entries(race_id, entries_with_priors) -> dict[horse_id, float]`
   - race_id에 출전하는 모든 말의 prior를 일괄 업데이트
   - DB에서 각 말의 최근 5경주 결과 조회
   - 반환: {horse_id: updated_probability}

3. `get_recent_results(horse_id) -> list`
   - `race_results` 테이블에서 최근 max_races개 결과 조회
   - 데뷔마 (결과 없음) → 빈 리스트 반환 → prior = ML 예측값 그대로

4. `store_bayesian_log(race_id, horse_id, prior_prob, posterior_prob)`
   - `prediction_accuracy_logs` 테이블에 Bayesian 업데이트 기록
   - (prior → posterior 변화량 추적용)

---

### 파일 2: `monte_carlo.py` 수정

기존 Phase 2 코드를 **최대한 유지**하고 Bayesian prior 주입 부분만 추가합니다.

**수정 위치: MC 시작 시 prior 주입**

```python
# monte_carlo.py — 기존 run_simulation() 함수 시작 부분에 추가
def run_simulation(entries, use_bayesian: bool = True, db_session=None):
    """
    use_bayesian: True이면 Bayesian 업데이트된 prior 사용
                  False이면 Phase 2 방식 그대로 (하위 호환)
    """
    if use_bayesian and db_session:
        # Bayesian 업데이트로 ML 예측 확률 보정
        from app.services.bayesian_updater import BayesianUpdater
        updater = BayesianUpdater(db_session)
        bayesian_priors = updater.update_race_entries(
            race_id=entries[0].race_id,
            entries_with_priors={e.horse_id: e.win_prob for e in entries}
        )
        # 업데이트된 prior를 각 말의 win_prob에 반영
        for entry in entries:
            entry.win_prob = bayesian_priors.get(entry.horse_id, entry.win_prob)
    
    # 이후 기존 Phase 2 MC 로직 그대로 실행...
```

**API 엔드포인트 수정**: `POST /ml/simulate`에 `use_bayesian` 파라미터 추가

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Beta 분포가 뭔지 쉽게 설명 ("0~1 사이 확률값을 모델링하는 분포")
- prior / likelihood / posterior 용어 쉽게 풀어서 설명
- `0.9 ** i` 지수감쇠가 왜 필요한지 설명 (오래된 경기일수록 영향 줄이기)
- 데뷔마 처리 이유 설명 (과거 데이터 없으면 ML 예측만 사용)
- `alpha / (alpha + beta)` 공식이 왜 기댓값인지 설명

---

## 인코딩 주의사항 ⚠️

- 파일 최상단: `# -*- coding: utf-8 -*-`
- UTF-8 (BOM 없음) 저장

---

## Git 규칙

```
브랜치: feat/phase3-ml-bayesian
커밋 메시지: feat: [prompt-30] Bayesian MC — BayesianUpdater (Beta-Binomial) + monte_carlo.py prior 주입
```

---

## 완료 기준

```bash
# 1. ML 서버 기동 확인
cd racepulse/ml-server
uvicorn app.main:app --port 8000 --reload

# 2. Bayesian 업데이트 단위 테스트
python -c "
from app.services.bayesian_updater import BayesianUpdater

# 테스트: prior 30%, 최근 2회 1위, 1회 비1위
updater = BayesianUpdater(db_session=None, prior_weight=10.0)
result = updater.update_single_horse(
    horse_id=1,
    prior_prob=0.30,
    recent_results=[(None, 1), (None, 2), (None, 1)]  # 1위, 2위, 1위
)
print(f'업데이트된 확률: {result:.3f}')  # 기대값: ~0.385
assert 0.35 < result < 0.42, f'기대 범위 벗어남: {result}'
print('✅ Bayesian 업데이트 정상')
"

# 3. MC 시뮬레이션 API 호출
curl -X POST http://localhost:8000/ml/simulate \
  -H 'Content-Type: application/json' \
  -d '{"race_id": 1, "use_bayesian": true}'
```
