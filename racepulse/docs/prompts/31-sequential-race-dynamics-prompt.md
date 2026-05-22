# 31. RacePulse Sequential Race Dynamics 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

이 프롬프트를 실행하기 **전에** 아래 파일들을 순서대로 전부 읽어야 합니다.

```
1. horse_racing_team.md            ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md         ← Phase 2 전체 기록, Redis 구조 이해
3. horse_racing_team_v3.md         ← Phase 3 킥오프, 14차 회의 확정사항
4. docs/PROJECT_RULES.md           ← 코딩 규칙 20개
5. docs/phase3/02-sequential-race-dynamics.md  ← Sequential 학습 문서 (필수!)
```

**선행 조건**: `prompt-30 (Bayesian MC)` 완료 후 실행 권장 (같은 브랜치)

---

## 🗂️ 지금까지 한 작업 요약 (컨텍스트)

### Redis 현황 (Phase 2 구현 완료)
- APScheduler + Redis로 당일 피처 스토어 100% 캐싱 구현
- MC 결과, AI 해설 결과도 Redis에 캐싱
- Redis 연결: `ml-server/app/core/redis_client.py` (이미 구현됨)

### 문제: 현재 예측은 정적
```
08:00 출전표 확정 → ML 예측 1회 실행 → 1~12경주 예측값 고정 (변경 없음)
```

### Phase 3에서 추가하는 것 (이 프롬프트)
```
08:00 초기 예측
↓ 1경주 결과 수집
  → Redis 저장 → 2경주 예측 자동 업데이트
↓ 2경주 결과 수집
  → Redis 저장 → 3경주 예측 자동 업데이트
↓ ... 반복 (당일 자정에 자동 만료)
```

---

## 목표

**신규 파일** 1개를 작성합니다:

`ml-server/app/services/sequential_updater.py`
- 앞 경주 결과를 Redis에 저장
- 뒷 경주 예측을 자동으로 fine-tuning

---

## 프로젝트 환경

- **ML 서버**: FastAPI / Python 3.11
- **Redis**: `ml-server/app/core/redis_client.py` (이미 연결됨)
- **APScheduler**: 이미 구현됨 — Sequential 업데이트 훅 추가만 하면 됨
- **Flyway V13**: `trainer_changes`, `equipment_changes` 테이블 이미 있음 (prompt-29 완료 후)

---

## 현재 파일 구조

```
ml-server/app/
├── core/
│   ├── redis_client.py     ← Redis 연결 (이미 구현됨)
│   └── config.py
├── services/
│   ├── monte_carlo.py      ← Phase 2 MC (prompt-30에서 Bayesian 추가됨)
│   ├── bayesian_updater.py ← prompt-30에서 신규 생성됨
│   ├── data_collector.py
│   └── (sequential_updater.py)  ← 이 파일 신규 생성
└── routers/
    └── ml_router.py        ← 신규 API 엔드포인트 추가
```

---

## 구현 사항

### `sequential_updater.py` (신규)

```python
# -*- coding: utf-8 -*-
"""
sequential_updater.py — Sequential Race Dynamics
=================================================
같은 날 앞 경주 결과가 뒷 경주 예측에 영향을 줍니다.
Redis에 당일 경주 결과를 임시 저장하고,
뒷 경주 예측 시 트랙 컨디션·기수 폼 등을 자동 반영합니다.

[Redis Key 구조]
race:today:{rc_date}:{race_no}:result     → 완료된 경주 착순 데이터
race:today:{rc_date}:track_condition      → 당일 트랙 상태 실황
race:today:{rc_date}:{jockey_id}:form     → 기수 당일 폼 (금일 성적)

[TTL]
자정(00:00) 자동 만료 → 다음 날 데이터에 영향 없음
"""
```

**SequentialUpdater 클래스:**

**메서드 1**: `store_race_result(rc_date, race_no, result_data)`
```python
# 경주 완료 시 Redis에 결과 저장
# result_data: {"착순": [{horse_id, position, time}, ...], "track_condition": "건조"}

# Redis에 저장 (TTL: 자정까지 남은 초)
redis.setex(
    f"race:today:{rc_date}:{race_no}:result",
    ttl=seconds_until_midnight(),
    value=json.dumps(result_data)
)

# 트랙 컨디션 업데이트 (당일 실황으로 계속 갱신)
redis.setex(
    f"race:today:{rc_date}:track_condition",
    ttl=seconds_until_midnight(),
    value=result_data["track_condition"]
)

# 기수별 당일 폼 업데이트
for horse_result in result_data["착순"]:
    self._update_jockey_form(rc_date, horse_result["jockey_id"], horse_result["position"])
```

**메서드 2**: `get_sequential_adjustments(rc_date, target_race_no) -> dict`
```python
# 목표 경주 번호 이전의 완료된 경주들을 확인하고 조정값 계산
# 반환: {
#   "track_condition": "습윤",    # 현재 트랙 상태
#   "track_bias": 0.15,          # 추입마 보정값 (+0.15 = 유리)
#   "jockey_forms": {            # 기수별 오늘 폼
#     1: {"today_win": 2, "today_race": 3, "form_factor": 1.2},
#   }
# }

# 완료된 경주가 없으면 → 기본값 반환 (조정 없음)
```

**메서드 3**: `apply_sequential_prior(entries, adjustments) -> list`
```python
# 각 말의 예측 확률에 Sequential 조정값 적용
# 트랙 상태에 따른 주행 스타일 보정:
#   건조 → LEADER(선행마) 확률 +5%
#   다습 → CLOSER(추입마) 확률 +10%
#   포화 → 전체 불확실성 증가 (분산 확대)
#
# 기수 당일 폼 보정:
#   오늘 2승 이상 → 해당 기수 말 확률 +3%
#   오늘 0승 3레이스 이상 → -3%
```

**메서드 4 (내부)**: `seconds_until_midnight() -> int`
```python
# 자정까지 남은 초 계산 (TTL 계산용)
# KST 기준 (UTC+9)
```

### APScheduler 훅 추가

`ml-server/app/core/scheduler.py` (이미 존재) 또는 `ml_router.py`에 아래 API 추가:

```python
# POST /ml/sequential/update
# 마사회 API에서 경주 결과가 수집될 때 호출
@router.post("/sequential/update")
async def update_sequential(rc_date: str, completed_race_no: int):
    """
    경주 결과가 수집되면 이 API를 호출합니다.
    1. Redis에 결과 저장
    2. 다음 경주 예측을 Sequential으로 업데이트
    """

# GET /ml/sequential/status/{rc_date}
# 오늘 Sequential 업데이트 현황 조회 (FE에서 "1경주 결과 반영 완료" 표시용)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Redis `setex`가 무엇인지 설명 (set + expire = 만료 시간 있는 저장)
- TTL이 왜 자정까지인지 설명 (당일 데이터만 유효하기 때문)
- 트랙 상태가 왜 예측에 영향을 주는지 설명 (건조=선행마 유리, 다습=추입마 유리)
- 기수 폼이 왜 당일 단위인지 설명 (컨디션은 날마다 변함)
- `json.dumps` / `json.loads`가 필요한 이유 설명 (Redis는 문자열만 저장 가능)
- `seconds_until_midnight()` 왜 KST 기준인지 설명 (경마는 한국 시간 기준)

---

## 인코딩 주의사항 ⚠️

- 파일 최상단: `# -*- coding: utf-8 -*-`
- UTF-8 (BOM 없음) 저장

---

## Git 규칙

```
브랜치: feat/phase3-ml-bayesian
커밋 메시지: feat: [prompt-31] Sequential Race Dynamics — Redis 당일 경주 결과 + 뒷 경주 예측 자동 업데이트
```

---

## 완료 기준

```bash
# 1. ML 서버 기동 확인
cd racepulse/ml-server
uvicorn app.main:app --port 8000 --reload

# 2. Sequential 업데이트 단위 테스트
python -c "
from app.services.sequential_updater import SequentialUpdater
import fakeredis  # 테스트용 가짜 Redis

updater = SequentialUpdater(redis=fakeredis.FakeRedis())

# 1경주 결과 저장
updater.store_race_result(
    rc_date='2026-06-07',
    race_no=1,
    result_data={
        '착순': [{'horse_id': 1, 'position': 1, 'jockey_id': 10}],
        'track_condition': '습윤'
    }
)

# 2경주 조정값 조회
adj = updater.get_sequential_adjustments('2026-06-07', target_race_no=2)
print(f'트랙 상태: {adj[\"track_condition\"]}')  # 습윤
print(f'추입마 보정: {adj[\"track_bias\"]}')     # 0.10 (양수)
print('✅ Sequential 업데이트 정상')
"

# 3. API 호출 테스트
curl -X POST 'http://localhost:8000/ml/sequential/update?rc_date=2026-06-07&completed_race_no=1'
curl 'http://localhost:8000/ml/sequential/status/2026-06-07'
```
