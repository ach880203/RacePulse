# Sequential Race Dynamics — 학습 문서

> RacePulse Phase 3 / 작성일: 2026-05-15

---

## 1. 개념

**"같은 날 앞 경주 결과가 뒷 경주 예측에 영향을 준다"**

경마는 하루에 여러 경주가 열립니다 (보통 7~12경주).
1경주의 결과(트랙 상태, 말의 실제 컨디션 등)가
2경주, 3경주 예측에 유용한 정보가 됩니다.

### 현재 방식 (정적)

```
08:00  출전표 확정
         ↓
       ML 예측 (하루 전체 한 번에)
         ↓
       1경주, 2경주, ... 12경주 예측값 고정
```

### Sequential 방식 (동적)

```
08:00  출전표 확정 → 전체 경주 초기 예측
         ↓
1경주 시작 → 결과 수집
         ↓
       당일 트랙 실황 반영 → 2경주 예측 업데이트
         ↓
2경주 시작 → 결과 수집
         ↓
       3경주 예측 업데이트
         ↓
       ... 반복
```

---

## 2. 무엇이 업데이트되나?

### 2-1. 트랙 컨디션 실황

마사회 API에서 트랙 함수율을 제공합니다.

| 상태 | 함수율 | 특징 |
|------|--------|------|
| 건조 (良) | 0~15% | 속도 최고 / 선행마 유리 |
| 습윤 (稍重) | 15~30% | 중간 |
| 다습 (重) | 30~50% | 추입마 유리 |
| 포화 (不良) | 50%+ | 기록 대폭 저하 |

1경주 후 트랙 상태가 "건조 → 다습"으로 바뀌었다면,
2경주에서 추입 스타일 말의 확률을 상향 조정합니다.

### 2-2. 기수 실황 컨디션

"오늘 이 기수가 1경주에서 어떤 레이스를 펼쳤나?"
→ 기수의 오늘 컨디션 추정 → 같은 기수가 타는 뒷 경주 예측 미세 조정.

### 2-3. 말 당일 실제 컨디션

마체중 예측과 실제 마체중 차이 반영.
(ex: 마체중이 예측보다 -10kg → 컨디션 하락 신호)

---

## 3. 구현 방식 (Redis 활용)

당일 경주 결과를 PostgreSQL에 영구 저장하기 전,
Redis에 임시로 빠르게 저장해서 다음 경주 예측에 즉시 반영합니다.

```
Redis Key 구조:
race:today:{rc_date}:{race_no}:result   → 착순 데이터
race:today:{rc_date}:track_condition    → 트랙 상태 실황
race:today:{rc_date}:{jockey_id}:form  → 기수 당일 폼
```

TTL: 자정(00:00)에 자동 만료.

```python
# 의사코드
def update_sequential_prior(rc_date: str, completed_race_no: int):
    track = redis.get(f"race:today:{rc_date}:track_condition")
    for future_race in get_remaining_races(rc_date, after=completed_race_no):
        adjusted_priors = adjust_for_track(future_race.entries, track)
        redis.setex(
            f"race:prediction:{rc_date}:{future_race.race_no}:sequential",
            ttl=86400,
            value=adjusted_priors
        )
```

---

## 4. Bayesian과의 관계

| | Bayesian 업데이트 | Sequential Race Dynamics |
|---|---|---|
| 시간 범위 | 과거 수 주~수개월 | 당일 |
| 데이터 | 역대 경주 결과 | 오늘 앞 경주 결과 |
| 목적 | 장기 폼 반영 | 당일 컨디션 반영 |
| 업데이트 주기 | 경주 결과 수집 시 (월/화) | 당일 경주 사이 (실시간) |

둘은 **보완 관계**입니다. Bayesian이 prior를 만들면, Sequential이 당일 상황으로 fine-tuning합니다.

---

## 5. 유저에게 어떻게 보이나?

```
2경주 예측 페이지 접속 시:
"1경주 결과 반영 완료 — 트랙 상태 건조→습윤 변경으로 추입마 확률 조정됨"
```

FE 동적 UI 28번: 실시간 컨디션 갱신 바로 시각화.
