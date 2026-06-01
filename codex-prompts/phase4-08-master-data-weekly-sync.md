# Phase 4 Codex 프롬프트 #8 — 기수/조교사/말 마스터 데이터 주간 동기화

## 배경 및 문제

**현상**: DB에 기수 164명, 조교사 145명, 말 10,574마리가 있는데 다음 필드가 전부 null이다.
- 기수: `birth_year`, `debut_year`, `win_rate_total`, `win_rate_recent`, `place_rate_total`
- 조교사: `birth_year`, `debut_year`, `win_rate_total`, `win_rate_recent`
- 말: `eng_name`(일부만), `father_name`(전부), `color`(전부)

**원인**: FastAPI 서버(`app/services/data_service.py`)에 아래 수집 함수들이 이미 구현되어 있지만,
nightly pipeline(`scripts/nightly_pipeline.py`)에서 한 번도 호출된 적이 없다.

이미 구현된 FastAPI Admin 엔드포인트 (`POST /admin/scheduler/run/{job_name}`):
- `collect_master_jockeys` — 기수 기본정보 + 통산성적 (birthday, debut, win_rate)
- `collect_master_trainers` — 조교사 기본정보 + 통산성적
- `collect_master_horses` — 말 기본목록
- `collect_horse_details` — 말 상세 (모마명, 생년, 성별)
- `collect_jockey_results` — 기수 성적 (승률 직접값 업데이트)

**추가 필요**: 말 `father_name`(부마명), `color`(모색)은 위 API들이 제공하지 않는다.
KRA API `totalHorseInfo_1` (`https://apis.data.go.kr/B551015/API42_1/totalHorseInfo_1`)에서
부마명(`faName`), 모마명(`moName`), 모색(`color`)을 제공한다.

---

## 해야 할 작업 두 가지

### 작업 1: nightly_pipeline.py에 주간 마스터 동기화 추가

`nightly_pipeline.py`의 `main()`에 **요일 조건부 실행** 블록을 추가한다.

- **실행 조건**: 매주 월요일 (`datetime.now().weekday() == 0`)
- **실행 내용**: 아래 job들을 SC/BU/JJ 3개 경마장에 대해 순서대로 호출

```
collect_master_jockeys  (SC, BU, JJ)
collect_master_trainers (SC, BU, JJ)
collect_master_horses   (SC, BU, JJ)
collect_horse_details   (SC, BU, JJ)
collect_jockey_results  (SC, BU, JJ)
```

**Admin 엔드포인트 스펙** (`POST http://localhost:8000/admin/scheduler/run/{job_name}`):
```json
{"meet_code": "SC"}
```
응답:
```json
{
  "success": true,
  "data": {"status": "SUCCESS", "recordsCollected": 164, ...}
}
```
`status == "SKIPPED"` 시 API 한도 초과 → 해당 job 이후 건너뜀, 파이프라인은 계속.

새 함수 `sync_master_data(client) -> dict`를 만들고 main()에서 Phase 0 이후 조건부 호출한다.
결과 요약 로그에도 출력한다.

---

### 작업 2: 말 부마명/모색 수집 — FastAPI에 새 수집 함수 추가

#### 2-A: `app/services/kra_api.py`에 `fetch_total_horse_info` 메서드 추가

이미 `HORSE_TOTAL_URL = "https://apis.data.go.kr/B551015/API42/totalHorseInfo_1"`가 정의됨.

```python
async def fetch_total_horse_info(
    self,
    meet: str,          # "1"(서울), "2"(제주), "3"(부산경남)
    page_no: int = 1,
    num_of_rows: int = 100,
) -> list[dict[str, Any]]:
    """마필종합 상세정보 API — 부마명, 모색, 영문마명 포함."""
```

KRA API 응답 주요 필드:
- `hrName`: 마명
- `hrEngName`: 영문마명
- `faName`: 부마명 (father_name)
- `moName`: 모마명 (mother_name)
- `color`: 모색
- `meet`: 경마장 코드

전체 페이지를 순회해야 하므로 `_fetch_all_pages` 유틸 활용.

#### 2-B: `app/services/data_service.py`에 수집 메서드 추가

`collect_horse_total_info(self, meet_codes: list[str]) -> CollectionSummary` 메서드를 추가한다.

저장 로직 `_save_horse_total_items`:
```python
updates = {
    "eng_name":    item.get("hrEngName"),
    "father_name": item.get("faName"),
    "mother_name": item.get("moName"),
    "color":       item.get("color"),
}
# Horse 테이블에서 name으로 조회 후 not-None 필드만 setattr 업데이트
```

#### 2-C: `app/api/admin.py`에 job 등록

`JOB_NAME_MAP`에 `"collect_horse_total_info": "마필종합 상세정보 수집"` 추가.
`run_scheduler_job` 핸들러에 `elif job_name == "collect_horse_total_info":` 분기 추가.

#### 2-D: nightly_pipeline.py 주간 동기화에 추가

작업 1의 `sync_master_data` 함수에 `collect_horse_total_info` job 추가.
(KRA API 일일 호출 3,000건 한도 주의 — 3개 경마장 × 여러 페이지)

---

## 기존 코드 참고

**`collect_horse_details` 패턴** (data_service.py:272) — 새 함수 구조 참고용:
```python
async def collect_horse_details(self, meet_codes: list[str]) -> CollectionSummary:
    all_items = []
    try:
        for meet_code in meet_codes:
            items = await self.kra_api_service.fetch_horse_detail_list(
                meet=self._meet_code_to_api_value(meet_code),
            )
            for item in items:
                item["_meet_code"] = meet_code
            all_items.extend(items)
        records_collected, null_count, anomaly_count = await self._save_horse_detail_items(all_items)
        await self.db.commit()
        ...
    except KRARateLimitExceededError: ...
    except Exception: ...
```

**`_meet_code_to_api_value`**: SC→"1", JJ→"2", BU→"3"

---

## 완료 기준

1. nightly_pipeline.py 월요일 실행 시 기수/조교사/말 마스터 데이터 동기화
2. `collect_horse_total_info` 함수 추가 및 admin API 등록
3. admin API `POST /admin/scheduler/run/collect_horse_total_info` 수동 실행 가능
4. 실행 후 DB에서 jockey.birth_year, horse.father_name, horse.color 등이 채워짐
5. KRA API SKIPPED 응답 시 해당 job만 건너뛰고 나머지 계속 진행

---

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-8] 마스터 데이터 주간 동기화 + 부마명/모색 수집`

### ML/Python 규칙
- **기존 패턴 준수**: `collect_horse_details` 함수 구조(data_service.py:272) 그대로 따라서 구현
- **에러 격리**: 예외 발생 시 해당 단계만 실패 — 전체 파이프라인 중단 금지
- **KRA API 한도**: `status == "SKIPPED"` 시 해당 job만 건너뜀, 나머지 계속 진행
- **경마장 코드 변환**: `_meet_code_to_api_value` 기존 함수 반드시 사용 (SC→"1", JJ→"2", BU→"3")
- **로그**: 기존 로그 패턴 사용 — `print()` 직접 사용 금지
- **주석**: 함수·중요 로직마다 WHY 설명 한 줄 이상
- **선행 조건**: `nightly_pipeline.py`는 #7 작업 완료·커밋 후 수정 시작 (동일 파일 충돌 방지)

## 파일 위치

- `racepulse/ml-server/app/services/kra_api.py`
- `racepulse/ml-server/app/services/data_service.py`
- `racepulse/ml-server/app/api/admin.py`
- `racepulse/ml-server/scripts/nightly_pipeline.py`
