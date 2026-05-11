# 05. RacePulse 마사회 API 연동 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
FastAPI 서버에서 한국마사회 공공데이터 API를 호출하여
경주 데이터를 수집하고 PostgreSQL에 저장하는 파이프라인을 구현합니다.
APScheduler로 자동 수집 스케줄을 설정합니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- SQLAlchemy 2.0 (async)
- asyncpg (PostgreSQL 비동기 드라이버)
- APScheduler 3.11.0 (스케줄 수집)
- httpx 0.28.1 (HTTP 요청)
- Redis (수집 카운터/체크포인트 관리)
- 포트: 8000

---

## 현재 파일 구조
```
ml-server/
├── app/
│   ├── main.py              ← FastAPI 앱 (이미 있음)
│   ├── api/
│   │   └── health.py        ← 헬스체크 (이미 있음)
│   ├── core/
│   │   ├── config.py        ← 환경변수 설정 (이미 있음)
│   │   └── database.py      ← DB 연결 (이미 있음)
│   ├── models/              ← DB 모델 (비어있음)
│   ├── services/            ← 비즈니스 로직 (비어있음)
│   └── scheduler/           ← APScheduler (비어있음)
├── requirements.txt
└── .env                     ← KMA_API_KEY 이미 입력됨
```

---

## 마사회 API 정보

### API 기본 정보
```
기관: 한국마사회 공공데이터 API
베이스 URL: https://apis.data.go.kr/B551015/API214_1
인증: serviceKey 쿼리 파라미터 (환경변수 KMA_API_KEY 사용)
응답 형식: JSON
Rate Limit: 일 3,000콜 (2,800콜 도달 시 자동 중단)
```

### 이번에 연동할 API 3개 (핵심 수집)

**① 경주계획표 (RaceScheduleList)**
- 엔드포인트: `/RaceScheduleList`
- 파라미터: `meet`(경마장코드), `rc_year`, `rc_month`
- 수집 주기: 월 1회
- 저장 테이블: `races`

**② 출전표 상세정보 (EntryInfo_1)**
- 엔드포인트: `/EntryInfo_1`
- 파라미터: `meet`, `rc_date`, `rc_no`(경주번호)
- 수집 주기: 목/금요일
- 저장 테이블: `race_entries`, `horses`, `jockeys`, `trainers`

**③ 경주성적 정보 (RaceDetailResult_1)**
- 엔드포인트: `/RaceDetailResult_1`
- 파라미터: `meet`, `rc_date`, `rc_no`
- 수집 주기: 월/화요일 (결과 수집)
- 저장 테이블: `race_results`

---

## 구현 파일 목록

### 1. DB 모델 (SQLAlchemy)
`app/models/race.py`
- `Race` 클래스 → races 테이블
- `RaceEntry` 클래스 → race_entries 테이블
- `RaceResult` 클래스 → race_results 테이블

`app/models/master.py`
- `Horse` 클래스 → horses 테이블
- `Jockey` 클래스 → jockeys 테이블
- `Trainer` 클래스 → trainers 테이블
- `Racecourse` 클래스 → racecourses 테이블

### 2. KRA API 서비스
`app/services/kra_api.py`
- 마사회 API 호출 담당 클래스
- `fetch_race_schedule()` → 경주계획표 수집
- `fetch_entry_info()` → 출전표 수집
- `fetch_race_results()` → 경주성적 수집
- Rate Limit 카운터 (Redis) 관리
- 지수 백오프 재시도 (5분→15분→30분→1시간→3시간)

### 3. 데이터 저장 서비스
`app/services/data_service.py`
- API 응답 데이터를 DB에 저장하는 로직
- 중복 데이터 처리 (upsert: 있으면 업데이트, 없으면 삽입)
- `collection_logs` 테이블에 수집 결과 기록

### 4. APScheduler 설정
`app/scheduler/scheduler.py`
- APScheduler 초기화 및 스케줄 등록

수집 스케줄:
```
월요일 14:00  → 주말 경기 결과 수집
화요일 09:00  → 월요일 경기 결과 수집 (있는 경우)
목요일 10:00  → 주말 출전표 초안 수집
목요일 17:30  → 출전표 업데이트 확인
금요일 08:00  → 출전표 확정본 수집
토요일 09:05  → 마체중/기수변경/트랙상태 수집
일요일 09:05  → 마체중/기수변경/트랙상태 수집
월요일 09:05  → 마체중/기수변경/트랙상태 수집 (있는 경우)
```

### 5. API 라우터 (수동 수집 트리거용)
`app/api/collection.py`
- `POST /collection/test` → 수동으로 수집 테스트 실행
- `GET /collection/status` → 오늘 수집 현황 조회

### 6. main.py 수정
- APScheduler 시작/종료 lifespan 이벤트 추가
- collection 라우터 등록

---

## Rate Limit 안전장치
```
일일 한도: 3,000콜
중단 기준: 2,800콜 도달 시 자동 중단
Redis 키:  kra:daily_count:{날짜}
리셋 시각: 자정(00:00) 자동 리셋
재시도:    지수 백오프 5회
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- SQLAlchemy 모델 클래스, Column, relationship 개념 설명
- `async/await` 비동기 개념 쉽게 설명
- APScheduler 스케줄 설정 방법과 크론 표현식 설명
- upsert(insert or update) 개념 설명
- Rate Limit, 지수 백오프 개념 설명
- Redis 카운터가 왜 필요한지 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단에 `# -*- coding: utf-8 -*-` 추가
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/collection/test` 호출 시 마사회 API 실제 호출 성공
2. 수집된 데이터가 PostgreSQL `races` 테이블에 저장됨
3. `collection_logs` 테이블에 수집 결과 기록됨
4. `GET http://localhost:8000/collection/status` 오늘 수집 현황 조회 성공
5. Redis에 `kra:daily_count:{날짜}` 카운터 증가 확인
