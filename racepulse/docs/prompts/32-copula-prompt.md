# 32. RacePulse Copula 상관행렬 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

이 프롬프트를 실행하기 **전에** 아래 파일들을 순서대로 전부 읽어야 합니다.

```
1. horse_racing_team.md         ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md      ← Phase 2 전체 기록, MC Cholesky 구현 내용
3. horse_racing_team_v3.md      ← Phase 3 킥오프, 14차 회의 확정사항
4. docs/PROJECT_RULES.md        ← 코딩 규칙 20개
5. docs/phase3/03-copula.md     ← Copula 학습 문서 (필수!)
```

**선행 조건**: `prompt-30 (Bayesian MC)` 완료 후 실행 (같은 브랜치, 같은 파일 수정)

---

## 🗂️ 지금까지 한 작업 요약 (컨텍스트)

### Phase 2 MC에서 이미 구현된 것 — Cholesky 분해
```python
# monte_carlo.py — Phase 2 게이트 상관행렬 (이미 구현됨)
# 게이트 1번 → 게이트 2번 말이 같이 잘하는 경향 등을 반영
Σ_gate = build_gate_correlation_matrix(gate_numbers)
L_gate = np.linalg.cholesky(Σ_gate)  # Cholesky 분해
```

### Phase 3에서 확장하는 것 (이 프롬프트)
Phase 2는 **게이트 번호** 기반 상관행렬만 있습니다.
Phase 3는 **말-말 직접 상관관계**를 추가합니다:

```
Phase 2: 게이트 상관 (1번 게이트 말과 2번 게이트 말의 관계)
Phase 3: 말-말 상관 (같은 조교사 말들, 같은 혈통 말들의 관계)
```

### 데이터 현황
- `rival_records` 테이블: 538,717쌍 직접 대결 이력 (Phase 2에서 구축 완료)
- `horse_running_style` 테이블: 8,726마리 주행 스타일 분류 완료

---

## 목표

`ml-server/app/services/monte_carlo.py`에 Copula 상관행렬 빌더를 추가합니다.
기존 Cholesky 게이트 파트를 **말-말 상관관계로 확장**합니다.

새로 추가할 것만 명시 — 기존 MC 로직은 최대한 유지하세요.

---

## 프로젝트 환경

- **ML 서버**: FastAPI / Python 3.11
- **수치 라이브러리**: numpy, scipy (이미 설치됨)
- **DB**: rival_records, horses, trainers 테이블 활용

---

## 현재 파일 구조

```
ml-server/app/services/
├── monte_carlo.py      ← Phase 2 구현 + prompt-30 Bayesian 추가됨
│                          여기에 Copula 빌더 추가
├── bayesian_updater.py ← prompt-30에서 생성됨
└── sequential_updater.py ← prompt-31에서 생성됨
```

---

## 구현 사항

### `monte_carlo.py`에 추가: `build_horse_correlation_matrix(entries, db_session)`

```python
def build_horse_correlation_matrix(entries, db_session) -> np.ndarray:
    """
    말들 간의 상관계수 행렬 Σ를 만듭니다.
    
    Copula란?
    각 말의 예측 확률 분포는 유지하면서, 말들 사이의 상관관계를 추가로 붙이는 도구입니다.
    비유: 각 말의 악보(예측 확률)는 그대로, 하모니(상관관계)만 추가합니다.
    
    상관계수 ρ (rho) 계산 기준 (14차 회의 확정):
    - 같은 조교사:          +0.15
    - 같은 혈통 (부마 동일): +0.10
    - 같은 경마장 출신:      +0.05
    - 역대 직접 대결 성적:   rival_records 테이블 기반 계산값
    
    반환: n×n 상관행렬 (n = 출전 말 수)
          대각선 = 1.0 (자기 자신과의 상관 = 1)
          비대각 = 0~1 (다른 말과의 상관도)
    """
    n = len(entries)
    
    # 초기값: 단위행렬 (모든 말은 독립으로 시작)
    Σ = np.eye(n)
    
    for i, entry_i in enumerate(entries):
        for j, entry_j in enumerate(entries):
            if i >= j:
                continue  # 대각선 이상만 계산 (대칭행렬이므로)
            
            rho = 0.0
            
            # 1. 같은 조교사 → 훈련 환경이 같아 같이 좋은 날, 같이 나쁜 날이 있음
            if entry_i.trainer_id == entry_j.trainer_id:
                rho += 0.15
            
            # 2. 같은 혈통 (부마 동일) → 유전적 특성이 유사해 날씨 등에 동일 반응
            if entry_i.father_horse_id and entry_i.father_horse_id == entry_j.father_horse_id:
                rho += 0.10
            
            # 3. 같은 경마장 출신 → 해당 트랙에 익숙한 정도 유사
            if entry_i.meet_code == entry_j.meet_code:
                rho += 0.05
            
            # 4. 역대 직접 대결 성적 (rival_records 조회)
            rival_rho = _get_rival_correlation(
                entry_i.horse_id, entry_j.horse_id, db_session
            )
            rho += rival_rho
            
            # 상관계수는 -1~1 사이, 여기서는 0~0.8로 클리핑 (과도한 상관 방지)
            rho = min(rho, 0.8)
            Σ[i, j] = rho
            Σ[j, i] = rho  # 대칭 행렬: (i,j) = (j,i)
    
    return Σ


def _get_rival_correlation(horse_id_1, horse_id_2, db_session) -> float:
    """
    rival_records에서 두 말의 직접 대결 성적 유사도를 상관계수로 변환합니다.
    
    계산 방법:
    - 평균 순위 차이가 작을수록 → 비슷한 실력 → 같이 좋고 나쁜 날 많음 → 높은 상관
    - 대결 횟수가 적으면 → 신뢰도 낮음 → 보정값 감쇠
    """
    # horse_id_1 < horse_id_2 순서 맞추기 (DB 제약조건)
    h1, h2 = (horse_id_1, horse_id_2) if horse_id_1 < horse_id_2 else (horse_id_2, horse_id_1)
    
    record = db_session.execute(
        "SELECT total_races, horse1_avg_position, horse2_avg_position "
        "FROM rival_records WHERE horse_id_1 = :h1 AND horse_id_2 = :h2",
        {"h1": h1, "h2": h2}
    ).fetchone()
    
    if not record or record.total_races < 3:
        return 0.0  # 대결 횟수 3회 미만 → 신뢰 불가, 상관 없음으로 처리
    
    # 평균 순위 차이 → 작을수록 실력이 비슷함
    pos_diff = abs((record.horse1_avg_position or 5) - (record.horse2_avg_position or 5))
    
    # 차이가 0이면 상관 0.1, 차이가 클수록 0으로 감소
    # 대결 횟수 보정: 많을수록 신뢰도 증가 (최대 1.0)
    base_rho = max(0.0, 0.1 - pos_diff * 0.02)
    confidence = min(record.total_races / 10.0, 1.0)
    
    return base_rho * confidence
```

### `run_simulation()`에 Copula 적용 추가

```python
def run_simulation(entries, use_bayesian=True, use_copula=True, db_session=None):
    # ... Bayesian prior 주입 (prompt-30에서 추가됨) ...
    
    if use_copula and db_session and len(entries) > 1:
        # 1. 말-말 상관행렬 계산
        Σ_horse = build_horse_correlation_matrix(entries, db_session)
        
        # 2. Cholesky 분해 (이미 Phase 2에 구현됨! 게이트 상관 파트와 동일 방식)
        try:
            L_horse = np.linalg.cholesky(Σ_horse)
        except np.linalg.LinAlgError:
            # 행렬이 양정치가 아닐 경우 (수치 오류) → 소폭 정규화
            Σ_horse += np.eye(len(entries)) * 1e-6
            L_horse = np.linalg.cholesky(Σ_horse)
        
        # 3. 상관있는 정규 난수 생성 → 각 말의 확률에 노이즈 주입
        # (기존 Phase 2 게이트 Cholesky와 동일한 방식, 대상만 말-말로 확장)
        Z = np.random.standard_normal(len(entries))
        X = L_horse @ Z  # 상관구조 적용된 난수
        
        from scipy.stats import norm
        U = norm.cdf(X)  # 균등분포로 변환 (0~1)
        
        # 4. 각 말의 예측 확률에 Copula 노이즈 반영
        for i, entry in enumerate(entries):
            entry.win_prob = _apply_copula_noise(entry.win_prob, U[i])
    
    # ... 이후 기존 MC 시뮬레이션 로직 그대로 ...
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Copula가 뭔지 쉬운 비유로 설명 (악보 + 하모니)
- 상관행렬이 왜 대칭인지 설명 (A↔B 상관 = B↔A 상관)
- Cholesky 분해가 뭔지 설명 (상관행렬을 나눠서 난수에 입혀주는 도구)
- `np.linalg.LinAlgError` 예외 처리 이유 설명 (수치 오류 방어)
- `norm.cdf(X)`가 왜 0~1인지 설명 (누적분포함수의 성질)
- 같은 조교사 말이 왜 상관이 높은지 현실적 이유 설명

---

## 인코딩 주의사항 ⚠️

- 파일 최상단: `# -*- coding: utf-8 -*-`
- UTF-8 (BOM 없음) 저장

---

## Git 규칙

```
브랜치: feat/phase3-ml-bayesian
커밋 메시지: feat: [prompt-32] Copula 상관행렬 — Cholesky 게이트 확장 → 말-말 상관관계 적용
```

---

## 완료 기준

```bash
# 1. ML 서버 기동 확인
cd racepulse/ml-server
uvicorn app.main:app --port 8000 --reload

# 2. Copula 단위 테스트
python -c "
import numpy as np
from app.services.monte_carlo import build_horse_correlation_matrix

# 가짜 entries 3마리 (같은 조교사 2마리 + 다른 조교사 1마리)
class FakeEntry:
    def __init__(self, horse_id, trainer_id, father_horse_id, meet_code):
        self.horse_id = horse_id
        self.trainer_id = trainer_id
        self.father_horse_id = father_horse_id
        self.meet_code = meet_code

entries = [
    FakeEntry(1, 100, 10, 'KSB'),  # 말A: 조교사 100, 부마 10
    FakeEntry(2, 100, 10, 'KSB'),  # 말B: 같은 조교사, 같은 부마 → 상관 높아야 함
    FakeEntry(3, 200, 20, 'GJA'),  # 말C: 다른 조교사, 다른 부마 → 상관 낮아야 함
]

Σ = build_horse_correlation_matrix(entries, db_session=None)
print(f'상관행렬:\\n{Σ}')
assert Σ[0, 1] >= 0.20, f'말A-말B 상관이 너무 낮음: {Σ[0, 1]}'  # 0.15+0.10=0.25
assert Σ[0, 2] <= 0.10, f'말A-말C 상관이 너무 높음: {Σ[0, 2]}'
print('✅ Copula 상관행렬 정상')
"

# 3. 전체 시뮬레이션 (Bayesian + Sequential + Copula 통합)
curl -X POST http://localhost:8000/ml/simulate \
  -H 'Content-Type: application/json' \
  -d '{"race_id": 1, "use_bayesian": true, "use_copula": true}'
```

---

## ⚠️ 주의사항

1. **기존 게이트 Cholesky 로직은 절대 삭제하지 마세요** — 병행 적용
2. 상관행렬이 **양정치(Positive Definite)**여야 Cholesky 분해 가능 — LinAlgError 방어 필수
3. 출전 말이 1마리인 경우 Copula 불필요 — `if len(entries) > 1` 조건 필수
4. `rival_records`에 데이터가 없는 말 쌍은 상관 0으로 처리 (graceful fallback)
