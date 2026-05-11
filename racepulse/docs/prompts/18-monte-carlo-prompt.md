# 18. RacePulse Monte Carlo 시뮬레이션 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
ML 예측값을 확률 분포로 변환하여 10,000회 시뮬레이션을 돌립니다.
각 말의 순위별 확률(1위 34%, 2위 28% 등)을 계산하고
FE 레이스 시뮬레이션 애니메이션의 데이터 소스로 제공합니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- numpy (수치 계산)
- scipy (확률 분포)
- PostgreSQL (결과 저장)

---

## Monte Carlo란?
무작위 숫자를 수만 번 뽑아서 확률을 계산하는 방법입니다.
예: "동전을 10,000번 던지면 앞면이 약 5,000번 나온다"

경마에 적용하면:
- ML 모델이 "이 말 승률 34%"라고 예측
- 10,000번 시뮬레이션 → 약 3,400번 1위
- 실제 확률 분포를 구할 수 있음

---

## 현재 파일 구조
```
ml-server/app/
├── services/
│   ├── predictor.py          ← ML 예측 (15번)
│   └── feature_engineering.py
└── models/
    └── ml.py                 ← Prediction 모델
```

---

## 구현 파일 목록

### 1. Monte Carlo 서비스
`app/services/monte_carlo.py`

구현 메서드:
- `run_simulation(race_id, n_simulations=10000)` → 시뮬레이션 실행
  - predictions 테이블에서 각 말의 승률 로드
  - 10,000회 시뮬레이션 실행
  - 각 말의 순위별 확률 계산
  - 이변 확률 계산 (배당률 기반)
- `calculate_rank_distribution(win_probabilities)` → 순위 분포 계산
- `calculate_upset_probability(race_id)` → 이변 확률 계산
- `save_simulation_result(race_id, result)` → 결과 저장

### 2. 시뮬레이션 결과 형식
```python
simulation_result = {
    "race_id": 1,
    "n_simulations": 10000,
    "horses": [
        {
            "horse_id": 10,
            "horse_name": "천하제일",
            "rank_distribution": {
                "1": 34.2,   # 1위 확률 34.2%
                "2": 28.1,   # 2위 확률 28.1%
                "3": 18.5,   # 3위 확률 18.5%
                "4+": 19.2   # 4위 이하 확률
            },
            "expected_rank": 1.8  # 기댓값
        }
    ],
    "upset_probability": 12.3,  # 이변 확률 %
    "computed_at": "2026-05-11T10:00:00"
}
```

### 3. API 엔드포인트
`app/api/ml.py` 에 추가:
```
POST /ml/simulate/{race_id}        ← 시뮬레이션 실행
GET  /ml/simulate/{race_id}/result ← 시뮬레이션 결과 조회
```

Spring Boot 프록시용:
```
GET /api/v1/predictions/{raceId}/simulation
```

---

## 이변 확률 계산 공식
```python
# 배당률이 높은 말이 이길수록 이변
# 단승 배당률 10배 이상 말이 1위 → 이변
upset_prob = (고배당말_1위_횟수 / n_simulations) * 100
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Monte Carlo 시뮬레이션 개념을 쉽게 설명 (주사위 예시)
- numpy 확률 추출 방법 설명 (`np.random.choice`)
- 확률 분포가 왜 필요한지 설명 (단순 순위보다 풍부한 정보)
- 이변(Upset)이 무엇인지 설명
- 10,000번 반복이 왜 정확한지 설명 (대수의 법칙)

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/ml/simulate/1` 10,000회 시뮬레이션 실행 성공
2. 각 말의 순위별 확률 합계가 100%인지 확인
3. `GET http://localhost:8000/ml/simulate/1/result` 결과 조회 성공
4. Spring Boot를 통해 FE에서 시뮬레이션 결과 조회 가능 확인
