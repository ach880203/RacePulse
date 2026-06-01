# Phase 4 Codex 프롬프트 #7 — nightly_pipeline에 경주 결과 자동 재수집 추가

## 배경 및 문제

`racepulse/ml-server/scripts/nightly_pipeline.py`는 매일 새벽 5시에 실행되는 야간 파이프라인이다.

**발견된 문제**: 주말 경마 완료 후 race_results(순위, 기록)가 DB에 저장되지 않은 경주들이 있다.
예) 2026-05-23(금), 2026-05-24(토) 경주: race_entries는 COLLECTED 상태인데 race_results = 0건.

**원인**: 경마는 금~일 3일 시행. bulk_collect(새벽 3시)가 해당 날짜를 시도했을 때 KRA API에 결과 데이터가 아직 없었다. 이후 KRA API에 결과가 올라와도 자동 재수집 로직이 없다.

**증거**: 아래 쿼리로 확인됨.
```sql
SELECT r.rc_date, r.id, COUNT(rr.id) as result_count
FROM races r
LEFT JOIN race_entries re ON re.race_id = r.id
LEFT JOIN race_results rr ON rr.race_entry_id = re.id
WHERE r.rc_date >= CURRENT_DATE - INTERVAL '14 days'
  AND r.rc_date < CURRENT_DATE
GROUP BY r.rc_date, r.id
HAVING COUNT(rr.id) = 0;
```

---

## 해야 할 작업

`racepulse/ml-server/scripts/nightly_pipeline.py` 파일에 **Phase 0** 함수를 추가하고 `main()`에 삽입한다.

### 구현 스펙

**새 함수 `collect_missing_results(client)`**:
- `asyncpg`로 DB에서 "최근 14일 이내 완료된 경주 중 race_results가 없는 (meet_code, rc_date)" 목록을 조회한다.
- 각 (meet_code, rc_date)에 대해 FastAPI 엔드포인트를 호출해 results를 수집한다.
- 반환: `{"collected": int, "skipped": int}` dict

**FastAPI 엔드포인트**: `POST http://localhost:8000/collection/test`
```json
{
  "collection_type": "results",
  "meet_code": "SC",
  "target_date": "2026-05-24"
}
```
성공 응답 예시:
```json
{
  "success": true,
  "data": {
    "status": "SUCCESS",
    "recordsCollected": 108,
    "qualityStatus": "GOOD"
  }
}
```
`status == "SKIPPED"`이면 일일 KRA API 한도 초과 → 즉시 중단.

**DB 쿼리** (asyncpg 사용, DB_URL 상수 이미 정의됨):
```sql
SELECT DISTINCT r.meet_code, r.rc_date
FROM races r
WHERE r.rc_date >= CURRENT_DATE - INTERVAL '14 days'
  AND r.rc_date < CURRENT_DATE
  AND NOT EXISTS (
    SELECT 1 FROM race_results rr
    JOIN race_entries re ON rr.race_entry_id = re.id
    WHERE re.race_id = r.id
  )
ORDER BY r.rc_date DESC
```

**main() 수정**: Phase 1 시작 직전에 Phase 0으로 `collect_missing_results(client)` 호출 추가.
결과 요약 로그에도 `collect_result` 항목 추가.

---

## 참고: 현재 nightly_pipeline.py 구조

```
API_BASE = "http://localhost:8000"
DB_URL   = "postgresql://racepulse:racepulse_dev@localhost:5432/racepulse"
LOG_FILE = ...
FRONTEND = ...

async def calculate_new_features(client) -> dict  # Phase 1-A
async def update_rivals(client) -> dict            # Phase 1-B
async def update_running_styles(client) -> dict    # Phase 1-C
async def verify_fe_build() -> dict                # Phase 1-D
async def retrain_models(client) -> dict           # Phase 2

async def main():
    # health check
    # Phase 1: asyncio.gather(calculate_new_features, update_rivals, update_running_styles, verify_fe_build)
    # Phase 2: retrain_models
    # 결과 요약 로그
```

`asyncpg`는 이미 import 되어 있다 (`import asyncpg`).
`httpx`도 이미 import 되어 있다 (`import httpx`).

---

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-7] nightly_pipeline 경주 결과 자동 재수집 추가`

### ML/Python 규칙
- **기존 패턴 준수**: 파일 내 기존 `async def` 함수 구조와 완전히 동일하게 작성
- **에러 격리**: 예외 발생 시 해당 단계만 실패 처리 — 전체 파이프라인 중단 금지
- **로그**: 기존 로그 패턴(`log_result` 또는 `logger`) 사용 — `print()` 직접 사용 금지
- **KRA API 한도**: `status == "SKIPPED"` 응답 시 이후 수집만 중단, 파이프라인(Phase 1, 2)은 계속 진행
- **주석**: 함수·중요 로직마다 WHY 설명 한 줄 이상
- **충돌 주의**: #8 작업은 이 작업 완료·커밋 후 시작할 것 (동일 파일 `nightly_pipeline.py` 충돌 방지)

## 완료 기준

1. `collect_missing_results` 함수가 nightly_pipeline.py에 추가됨
2. `main()`에서 Phase 1 직전에 호출됨
3. 결과 요약 로그에 수집 결과 출력됨
4. KRA API 한도 초과(SKIPPED) 시 수집만 중단하고 나머지 파이프라인(Phase 1, 2)은 계속 진행
5. 오류 발생 시 예외를 잡아 로그에 기록하고 파이프라인 전체를 멈추지 않음
