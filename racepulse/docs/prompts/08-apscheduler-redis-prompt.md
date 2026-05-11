# 08. RacePulse APScheduler + Redis 수집 파이프라인 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
FastAPI 서버에 APScheduler 자동 수집 스케줄을 완성하고
Redis로 Rate Limit 카운터와 체크포인트를 관리합니다.
마사회 API 일 3,000콜 한도를 안전하게 관리합니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- APScheduler 3.11.0
- Redis (redis-py 5.2.1)
- 포트: 8000

---

## 현재 파일 구조
```
ml-server/app/
├── main.py
├── api/
│   ├── health.py
│   └── collection.py     ← 05번 프롬프트로 생성됨
├── core/
│   ├── config.py
│   └── database.py
├── models/
│   ├── race.py
│   ├── master.py
│   └── weather.py        ← 06번 프롬프트로 생성됨
├── services/
│   ├── kra_api.py        ← 05번 프롬프트로 생성됨
│   └── weather_api.py    ← 06번 프롬프트로 생성됨
└── scheduler/
    └── scheduler.py      ← 기존 파일 대폭 수정
```

---

## Redis 키 설계

```
kra:daily_count:{YYYYMMDD}        ← 오늘 마사회 API 호출 횟수
kra:checkpoint:{job_name}          ← 마지막 수집 완료 시점
kra:lock:{job_name}                ← 중복 실행 방지 락
weather:cache:{meet_code}:{date}   ← 날씨 데이터 캐시 (1시간 TTL)
```

---

## 구현 파일 목록

### 1. Redis 서비스
`app/core/redis_client.py`

구현 메서드:
- `get_daily_call_count(date)` → 오늘 API 호출 횟수 조회
- `increment_daily_count(date)` → 호출 횟수 +1 (자정 자정 리셋)
- `is_limit_reached(date)` → 2,800콜 초과 여부 확인
- `set_checkpoint(job_name, timestamp)` → 수집 완료 시점 저장
- `get_checkpoint(job_name)` → 마지막 수집 시점 조회
- `acquire_lock(job_name, ttl)` → 중복 실행 방지 락 획득
- `release_lock(job_name)` → 락 해제

### 2. 스케줄러 완성
`app/scheduler/scheduler.py` 전체 재작성

구현할 스케줄 전체:
```python
# 경주 결과 수집
월요일 14:00  → collect_race_results()     # 주말 경기 결과
화요일 09:00  → collect_race_results()     # 월요일 경기 결과

# 출전표 수집
목요일 10:00  → collect_entry_info()       # 출전표 초안
목요일 17:30  → collect_entry_info()       # 업데이트 확인
금요일 08:00  → collect_entry_info()       # 확정본

# 당일 정보 수집
토요일 09:05  → collect_daily_info()       # 마체중/기수변경/트랙상태
일요일 09:05  → collect_daily_info()
월요일 09:05  → collect_daily_info()

# 마스터 데이터 수집
매주 화요일 06:00  → collect_weekly()     # 경주마명단, 레이팅
매월 1일 05:00     → collect_monthly()    # 기수/조교사/마필/진료

# 날씨 수집
매일 06:30  → collect_weather_short()     # 단기예보
매일 18:30  → collect_weather_short()     # 단기예보 업데이트
매일 06:00  → collect_weather_mid()       # 중기예보

# Rate Limit 리셋
매일 00:00  → reset_daily_counter()       # Redis 카운터 초기화
```

### 3. 각 수집 함수 구현
모든 수집 함수에 공통 패턴 적용:
```python
async def collect_race_results():
    # 1. 중복 실행 방지 (Redis 락 획득)
    # 2. Rate Limit 확인 (2,800콜 초과 시 중단)
    # 3. API 호출
    # 4. 지수 백오프 재시도 (실패 시 5분→15분→30분→1시간→3시간)
    # 5. DB 저장
    # 6. 수집 로그 기록 (collection_logs 테이블)
    # 7. 락 해제
```

### 4. 지수 백오프 재시도 유틸리티
`app/core/retry.py`
```python
# 재시도 간격: 5분 → 15분 → 30분 → 1시간 → 3시간
RETRY_DELAYS = [5, 15, 30, 60, 180]  # 분 단위
```

### 5. 관리자 API 추가
`app/api/admin.py`
- `GET /admin/scheduler/status` → 스케줄러 상태 확인
- `GET /admin/rate-limit/status` → 오늘 API 사용량 확인
- `POST /admin/scheduler/run/{job_name}` → 특정 작업 수동 실행

---

## Rate Limit 안전장치 상세

```
일일 한도:    3,000콜
중단 기준:    2,800콜 (안전 마진 200콜)
Redis 키:    kra:daily_count:{YYYYMMDD}
리셋 시각:   매일 자정 00:00
재시도 횟수: 최대 5회
재시도 간격: 5분 → 15분 → 30분 → 1시간 → 3시간

2,800콜 도달 시:
→ 현재 수집 중단
→ collection_logs에 SKIPPED 상태 기록
→ 다음 스케줄 실행 시 이어서 수집 (체크포인트 활용)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- APScheduler cron 표현식 설명 (예: `cron(day_of_week='mon', hour=14)`)
- Redis 락(분산 락)이 왜 필요한지 설명 (중복 실행 방지)
- 지수 백오프(Exponential Backoff)란 무엇인지 설명
- Rate Limit 카운터를 Redis에 저장하는 이유 설명
- 체크포인트가 왜 필요한지 설명 (중단 후 이어서 수집)

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `GET http://localhost:8000/admin/scheduler/status` → 전체 스케줄 목록 및 다음 실행 시간 확인
2. `GET http://localhost:8000/admin/rate-limit/status` → 오늘 API 사용량 조회
3. `POST http://localhost:8000/admin/scheduler/run/collect_weather_short` → 수동 실행 성공
4. Redis에서 `kra:daily_count:{오늘날짜}` 카운터 증가 확인
5. 수집 완료 후 `collection_logs` 테이블에 SUCCESS 로그 기록 확인
