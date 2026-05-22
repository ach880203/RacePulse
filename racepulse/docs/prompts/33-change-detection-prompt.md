# 33. RacePulse 변경사항 감지 5종 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

이 프롬프트를 실행하기 **전에** 아래 파일들을 순서대로 전부 읽어야 합니다.

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, 기수변경 감지 기존 구현 내용
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (변경감지 5종 전부 확정)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: `prompt-29 (V13 마이그레이션)` 완료 필수
- `trainer_changes` / `equipment_changes` 테이블이 V13에서 생성됨

---

## 🗂️ 지금까지 한 작업 요약 (컨텍스트)

### Phase 2 기수변경 감지 (이미 구현됨)
- `ml-server/app/services/data_collector.py` 에 기수변경 감지 로직 존재
- 기수변경 시 AI 해설 캐시 무효화 + 자동 재생성 트리거 구현 완료
- Redis Pub/Sub 구조로 BE에 변경 이벤트 발행

### Phase 3에서 추가하는 것 (이 프롬프트)
14차 회의 확정: **감지 5종 전부 구현**

| 변경 종류 | 뱃지 | 영향도 | 기존 여부 |
|-----------|------|--------|----------|
| 기수변경 | 🔴 빨강 | 매우 큼 | ✅ Phase 2 구현됨 — 개선 |
| 출전 취소 | ⚫ 회색 | 매우 큼 | 신규 |
| 조교사 변경 | 🟠 주황 | 중간 | 신규 |
| 장비변경 (블링커 등) | 🟡 노랑 | 중간 | 신규 |
| 트랙 상태 급변 | 🔵 파랑 | 중간 | 신규 |

---

## 목표

`ml-server/app/services/change_detector.py` 파일을 신규 생성합니다.
5종 감지 로직 + Redis Pub/Sub 발행 + DB 이력 저장을 담당합니다.

---

## 프로젝트 환경

- **ML 서버**: FastAPI / Python 3.11
- **Redis**: Pub/Sub 채널 `racepulse:changes` (BE가 구독)
- **DB**: `trainer_changes` / `equipment_changes` 테이블 (V13 생성됨)
- **스케줄**: APScheduler 30분 간격으로 변경 감지 (14차 회의 확정)
- **기존 감지**: `data_collector.py`의 기수변경 감지 로직 — 이 파일로 통합·개선

---

## 현재 파일 구조

```
ml-server/app/services/
├── data_collector.py       ← 기수변경 감지 로직 존재 → 여기서 분리·이관
├── monte_carlo.py          ← Bayesian+Copula 추가됨 (prompt-30~32)
├── bayesian_updater.py     ← prompt-30 생성
├── sequential_updater.py   ← prompt-31 생성
└── (change_detector.py)    ← 이 파일 신규 생성
```

---

## 구현 사항

### `change_detector.py` (신규)

```python
# -*- coding: utf-8 -*-
"""
change_detector.py — 경주 변경사항 감지 5종
=============================================
경주 출전 정보가 확정 후에도 다음과 같은 변경이 발생할 수 있습니다:
  1. 기수 변경 (🔴): 가장 영향이 크고 자주 발생
  2. 출전 취소 (⚫): 말 또는 출전 자체가 취소됨
  3. 조교사 변경 (🟠): 훈련 환경 변화
  4. 장비 변경 (🟡): 블링커 등 장비 교체
  5. 트랙 급변 (🔵): 날씨로 인한 트랙 상태 급격 변화

감지된 변경은:
  - DB (trainer_changes / equipment_changes 등) 에 이력 저장
  - Redis Pub/Sub 채널 'racepulse:changes' 에 이벤트 발행
  - AI 해설 캐시 무효화 (기수·조교사·장비 변경 시)
  - MC 재시뮬레이션 트리거 (모든 변경 시)
"""
```

**ChangeDetector 클래스:**

**메서드 1**: `detect_all(rc_date: str, race_no: int = None)`
```python
# 전체 5종 감지를 한 번에 실행하는 메인 메서드
# race_no가 None이면 해당 날짜 전체 경주 검사
# APScheduler에서 30분마다 이 메서드를 호출합니다

changes = []
changes += self.detect_jockey_changes(rc_date, race_no)
changes += self.detect_scratches(rc_date, race_no)        # 출전 취소
changes += self.detect_trainer_changes(rc_date, race_no)
changes += self.detect_equipment_changes(rc_date, race_no)
changes += self.detect_track_condition_change(rc_date)

for change in changes:
    self._save_to_db(change)
    self._publish_to_redis(change)
    if change.affects_commentary:
        self._invalidate_commentary_cache(change.race_id)
    self._trigger_mc_resimulation(change.race_id)

return changes
```

**메서드 2**: `detect_jockey_changes(rc_date, race_no) -> list[ChangeEvent]`
```python
# 기수변경 감지 — Phase 2 data_collector.py 로직을 이관·개선
# 마사회 API 최신 출전표와 DB 저장값을 비교
# 변경 감지 시:
#   - race_entries 테이블의 jockey_id 업데이트
#   - ChangeEvent(type='JOCKEY', badge='🔴', impact='VERY_HIGH') 반환
```

**메서드 3**: `detect_scratches(rc_date, race_no) -> list[ChangeEvent]`
```python
# 출전 취소 감지 (⚫)
# 마사회 API에서 출전 취소된 말 감지
# 취소된 말은 race_entries.is_scratched = True 로 업데이트
# ChangeEvent(type='SCRATCH', badge='⚫', impact='VERY_HIGH') 반환
```

**메서드 4**: `detect_trainer_changes(rc_date, race_no) -> list[ChangeEvent]`
```python
# 조교사 변경 감지 (🟠)
# 마사회 API 최신값과 DB의 entries.trainer_id 비교
# 변경 감지 시:
#   - trainer_changes 테이블에 이력 저장 (previous_change_id 체인 포함)
#   - Bayesian prior 자동 조정 트리거
# ChangeEvent(type='TRAINER', badge='🟠', impact='MEDIUM') 반환
```

**메서드 5**: `detect_equipment_changes(rc_date, race_no) -> list[ChangeEvent]`
```python
# 장비 변경 감지 (🟡) — 블링커, 안장, 편자 등
# 마사회 API의 equipment 필드와 DB 저장값 비교
# 변경 감지 시:
#   - equipment_changes 테이블에 이력 저장
#   - blinker_first_time 여부 자동 판별 (첫 착용인지 확인)
# ChangeEvent(type='EQUIPMENT', badge='🟡', impact='MEDIUM') 반환
```

**메서드 6**: `detect_track_condition_change(rc_date) -> list[ChangeEvent]`
```python
# 트랙 상태 급변 감지 (🔵)
# 기상청 API + 마사회 트랙 함수율 비교
# 이전 예측 시점 트랙 상태 vs 현재 트랙 상태 비교
# 급변 기준: 트랙 등급(良→稍重→重→不良) 1단계 이상 변화
# ChangeEvent(type='TRACK', badge='🔵', impact='MEDIUM') 반환
```

**ChangeEvent 데이터 클래스:**
```python
@dataclass
class ChangeEvent:
    type: str            # JOCKEY / SCRATCH / TRAINER / EQUIPMENT / TRACK
    badge: str           # 🔴 / ⚫ / 🟠 / 🟡 / 🔵
    impact: str          # VERY_HIGH / HIGH / MEDIUM / LOW
    race_id: int
    horse_id: int | None
    old_value: str | None
    new_value: str | None
    detected_at: datetime
    affects_commentary: bool   # AI 해설 캐시 무효화 여부
```

**내부 메서드들:**
```python
def _save_to_db(self, change: ChangeEvent)
    # 변경 종류에 따라 trainer_changes 또는 equipment_changes 테이블에 저장

def _publish_to_redis(self, change: ChangeEvent)
    # Redis Pub/Sub 채널 'racepulse:changes'에 JSON 발행
    # BE Spring Boot가 이 채널을 구독해서 실시간 알림 처리
    redis.publish('racepulse:changes', json.dumps({
        "type": change.type,
        "badge": change.badge,
        "race_id": change.race_id,
        "horse_id": change.horse_id,
        "old_value": change.old_value,
        "new_value": change.new_value,
        "detected_at": change.detected_at.isoformat()
    }))

def _invalidate_commentary_cache(self, race_id: int)
    # Redis에서 해당 경주 AI 해설 캐시 삭제
    # 삭제 후 자동 재생성 트리거 (prompt-35에서 구현)
    redis.delete(f"commentary:pre:{race_id}")
    redis.delete(f"commentary:post:{race_id}")

def _trigger_mc_resimulation(self, race_id: int)
    # Redis에 MC 재시뮬레이션 요청 발행
    redis.publish('racepulse:resimulate', json.dumps({"race_id": race_id}))
```

### APScheduler 훅 추가

`ml-server/app/core/scheduler.py` 에 30분 간격 스케줄 추가:

```python
# 30분마다 변경사항 감지 실행 (14차 회의 확정)
@scheduler.scheduled_job('interval', minutes=30, id='change_detection')
def run_change_detection():
    detector = ChangeDetector(db_session, redis_client)
    today = datetime.now(KST).strftime('%Y%m%d')
    changes = detector.detect_all(rc_date=today)
    logger.info(f"변경 감지 완료: {len(changes)}건")
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `@dataclass`가 무엇인지 설명 (데이터만 담는 클래스를 쉽게 만드는 도구)
- Redis `publish`가 뭔지 설명 (채널에 메시지를 보내면 구독자가 받는 구조)
- Pub/Sub 패턴이 왜 유용한지 설명 (ML-BE 직접 호출 없이 느슨하게 연결)
- `blinker_first_time` 판별 로직이 왜 필요한지 설명 (처음 착용 vs 다시 착용은 영향이 다름)
- 트랙 등급 1단계 변화가 급변 기준인 이유 설명 (良→稍重도 실제 성적 영향 큼)
- `previous_change_id` 체인이 왜 필요한지 설명 (A→B→A 변경 흐름 추적)

---

## 인코딩 주의사항 ⚠️

- 파일 최상단: `# -*- coding: utf-8 -*-`
- UTF-8 (BOM 없음) 저장

---

## Git 규칙

```
브랜치: feat/phase3-be-changes
커밋 메시지: feat: [prompt-33] 변경사항 감지 5종 — ChangeDetector (기수/취소/조교사/장비/트랙) + Redis Pub/Sub
```

---

## 완료 기준

```bash
# 1. ML 서버 기동
cd racepulse/ml-server
uvicorn app.main:app --port 8000 --reload

# 2. 감지 단위 테스트
python -c "
from app.services.change_detector import ChangeDetector, ChangeEvent

# 트랙 급변 감지 테스트 (DB 없이 가능)
detector = ChangeDetector(db_session=None, redis=None)
# detect_track_condition_change 는 良→重 변화를 감지해야 함
print('✅ ChangeDetector 임포트 성공')
"

# 3. APScheduler 30분 스케줄 등록 확인
curl http://localhost:8000/scheduler/jobs
# 'change_detection' 잡이 목록에 있어야 함
```
