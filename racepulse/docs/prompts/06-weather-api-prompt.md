# 06. RacePulse 기상청 API 연동 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
FastAPI 서버에서 기상청 공공데이터 API를 호출하여
경마장별 날씨 예보를 수집하고 PostgreSQL에 저장합니다.
날씨 데이터는 ML 예측 모델의 핵심 피처로 사용됩니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- SQLAlchemy 2.0 (async)
- httpx 0.28.1
- APScheduler 3.11.0
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
│   ├── config.py         ← WEATHER_API_KEY 설정됨
│   └── database.py
├── models/
│   ├── race.py           ← 05번 프롬프트로 생성됨
│   └── master.py         ← 05번 프롬프트로 생성됨
├── services/
│   └── kra_api.py        ← 05번 프롬프트로 생성됨
└── scheduler/
    └── scheduler.py      ← 05번 프롬프트로 생성됨
```

---

## 기상청 API 정보

### API 기본 정보
```
기관: 기상청 공공데이터 API (data.go.kr)
베이스 URL: https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0
인증: serviceKey 쿼리 파라미터 (환경변수 WEATHER_API_KEY 사용)
응답 형식: JSON
```

### 사용할 API 2개

**① 단기예보 (getVilageFcst)**
- 엔드포인트: `/getVilageFcst`
- 파라미터: `base_date`, `base_time`, `nx`(X격자), `ny`(Y격자)
- 제공 정보: 기온, 강수확률, 풍속, 날씨상태
- 수집 주기: 하루 2회 (오전 6시, 오후 6시)

**② 중기예보 (getMidFcst)**
- 엔드포인트: `/getMidFcst`
- 파라미터: `regId`(예보구역코드), `tmFc`(발표시각)
- 제공 정보: 3~10일 날씨 전망
- 수집 주기: 하루 1회

---

## 경마장별 격자 좌표

기상청 API는 위경도 대신 격자 좌표(nx, ny)를 사용합니다.

```python
RACECOURSE_COORDINATES = {
    'SC': {'nx': 62, 'ny': 122, 'regId': '11B00000'},  # 서울/과천
    'BU': {'nx': 98, 'ny': 76,  'regId': '11H20000'},  # 부산
    'JJ': {'nx': 52, 'ny': 38,  'regId': '11G00000'},  # 제주
}
```

---

## 구현 파일 목록

### 1. DB 모델
`app/models/weather.py`
- `WeatherForecast` 클래스 → `weather_forecasts` 테이블

테이블 컬럼:
```
id, meet_code(SC/BU/JJ), forecast_date,
temp_min, temp_max, precipitation_prob,
wind_speed, condition, source,
created_at, updated_at
```

### 2. 기상청 API 서비스
`app/services/weather_api.py`

구현 메서드:
- `fetch_short_term_forecast(meet_code)` → 단기예보 수집
- `fetch_mid_term_forecast(meet_code)` → 중기예보 수집
- `save_forecast(meet_code, forecast_data)` → DB 저장 (upsert)
- `get_weather_condition(pty, sky)` → 날씨 상태 변환
  - pty(강수형태): 0=없음, 1=비, 2=비/눈, 3=눈, 4=소나기
  - sky(하늘상태): 1=맑음, 3=구름많음, 4=흐림

### 3. 스케줄러 추가
`app/scheduler/scheduler.py` 에 날씨 수집 스케줄 추가:
```
매일 06:30  → 단기예보 수집 (3개 경마장)
매일 18:30  → 단기예보 업데이트
매일 06:00  → 중기예보 수집
```

### 4. API 라우터 추가
`app/api/collection.py` 에 날씨 수집 엔드포인트 추가:
- `POST /collection/weather/test` → 수동 날씨 수집 테스트
- `GET /weather/{meet_code}/{date}` → 특정 경마장 날씨 조회

---

## 날씨 상태 변환 규칙
```python
# 기상청 코드 → 우리 시스템 텍스트 변환
def get_weather_condition(pty: int, sky: int) -> str:
    if pty == 1: return "비"
    if pty == 2: return "비/눈"
    if pty == 3: return "눈"
    if pty == 4: return "소나기"
    if sky == 1: return "맑음"
    if sky == 3: return "구름많음"
    if sky == 4: return "흐림"
    return "알 수 없음"
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 기상청 격자 좌표 개념 설명 (왜 위경도가 아닌 nx/ny를 쓰는지)
- upsert 개념 설명 (있으면 업데이트, 없으면 삽입)
- pty, sky 코드값이 무엇을 의미하는지 설명
- APScheduler cron 표현식 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- 한글 주석이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/collection/weather/test` 호출 시 기상청 API 실제 호출 성공
2. `weather_forecasts` 테이블에 3개 경마장 날씨 데이터 저장 확인
3. `GET http://localhost:8000/weather/SC/2026-05-08` 날씨 조회 성공
4. 날씨 condition 값이 한글로 정상 저장됨 확인 ("맑음", "비" 등)
