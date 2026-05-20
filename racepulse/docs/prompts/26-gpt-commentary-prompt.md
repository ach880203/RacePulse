# 26. RacePulse GPT-4o-mini AI 해설 프롬프트 초안 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표

경마 AI 해설을 자동 생성하는 GPT-4o-mini 프롬프트 2종을 구현합니다.

- **금요일 사전 해설** (출전표 확정 후 08:00 자동 생성) — 600~1000자
- **월요일 결과 해설** (경기 결과 수집 후 14:00 자동 생성) — 800~1200자

1차 회의 확정사항: Redis 캐싱 + 사행성 방지 시스템 프롬프트 필수.

---

## 프로젝트 환경

- Python 3.13 / FastAPI
- OpenAI GPT-4o-mini (`OPENAI_API_KEY` 환경변수)
- Redis 캐싱 (캐시 키: `pre_race:{meet}:{rc_date}:{race_no}` / `post_race:{meet}:{rc_date}:{race_no}`)
- PostgreSQL (경주/출전마/기수/조교사/예측 결과 데이터 조회)

---

## 현재 파일/폴더 구조

```
ml-server/app/
├── services/
│   └── ai_commentary.py    ← 이 파일에 구현
├── api/
│   └── commentary.py       ← 이미 존재하는 라우터
└── models/
    └── race.py             ← Race, RaceEntry, RaceResult 모델
```

---

## 구현 사항

### 1. `ai_commentary.py` — GPT-4o-mini 프롬프트 구현

#### 1-1. 시스템 프롬프트 (사행성 방지 필수)

```python
SYSTEM_PROMPT = """
당신은 경마 데이터 분석 전문 해설가입니다.
순수한 데이터 분석과 통계 기반으로 경마를 해설합니다.

절대 금지사항:
- "이 말에 투자하세요", "베팅을 추천합니다" 등 직접적 투자 권유
- "확실한 1위", "반드시 우승" 등 단정적 표현
- 사행성을 조장하는 어떠한 표현

필수 포함사항:
- "데이터 기준으로", "통계적으로", "참고용 분석" 등 표현 사용
- 모든 해설 하단에 면책 문구 포함:
  "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."
"""
```

#### 1-2. 금요일 사전 해설 생성 함수

```python
async def generate_pre_race_commentary(
    race_id: int,
    db: AsyncSession,
    redis_client: Redis,
) -> str:
```

**GPT에 전달할 데이터:**
- 경주 기본 정보 (거리, 트랙 상태, 날씨)
- 출전마 목록 + 기수 + 조교사
- 각 말의 최근 5경주 성적 (race_results에서 조회)
- ML 예측 결과 (predictions 테이블 — win_prob)
- 배당률 (race_entries.odds_win)

**해설 구성 (600~1000자):**
```
1. 오늘의 핵심 변수 (트랙/날씨/거리)
2. 주목 말 3선 (예측 상위 3마리) — 강점/약점/기수 콤비 히스토리
3. 이번 경주 관전 포인트
4. 이변 가능성 (upset_probability 기반)
5. 면책 문구
```

#### 1-3. 월요일 결과 해설 생성 함수

```python
async def generate_post_race_commentary(
    race_id: int,
    db: AsyncSession,
    redis_client: Redis,
) -> str:
```

**GPT에 전달할 데이터:**
- 실제 경주 결과 (race_results — 착순/기록)
- ML 예측 결과 vs 실제 결과 비교
- 이변 지수 (배당률 기반: 고배당 말이 상위권 진입 여부)
- Monte Carlo 예측 정확도 (confidence_score)

**해설 구성 (800~1200자):**
```
1. 이변 지수 (Upset Meter) — 배당률 기반 이변 정도 수치화
2. 경기 하이라이트 + 결정적 순간
3. ML 예측 vs 실제 복기 (틀렸다면 이유 솔직하게)
4. 다음 경주 예고 + 주목 말
5. 면책 문구
```

#### 1-4. Redis 캐싱

```python
# 사전 해설 캐시 키
PRE_CACHE_KEY = "pre_race:{meet}:{rc_date}:{race_no}"

# 결과 해설 캐시 키
POST_CACHE_KEY = "post_race:{meet}:{rc_date}:{race_no}"

# 캐시 만료: 7일 (경주가 끝나도 일주일은 조회 가능)
CACHE_TTL = 60 * 60 * 24 * 7
```

#### 1-5. DB 저장

해설 생성 후 `ai_commentary` 테이블에 저장:
```python
# type: 'PRE' 또는 'POST'
# model_used: 'gpt-4o-mini'
# cache_key: 위의 캐시 키
# prompt_tokens, completion_tokens: API 응답에서 추출
```

### 2. `commentary.py` 라우터 확인 및 수정

기존 파일의 엔드포인트가 위 함수를 올바르게 호출하는지 확인:
```
GET /commentary/{raceId}/pre  → generate_pre_race_commentary()
GET /commentary/{raceId}/post → generate_post_race_commentary()
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- GPT API 호출 방식(`client.chat.completions.create`) 설명
- `system` / `user` 프롬프트의 차이 설명
- Redis 캐싱이 왜 필요한지 설명 (비용 절감, 속도)
- `prompt_tokens`, `completion_tokens`가 무엇인지 설명
- 사행성 방지가 왜 코드 레벨에서 필요한지 설명

---

## 인코딩 주의사항 ⚠️

- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- GPT 프롬프트 내 한글이 깨지지 않도록 확인

---

## Git 규칙

```
브랜치: feat/phase2-ai-commentary
커밋 메시지: feat: [prompt-26] GPT-4o-mini AI 해설 시스템 구현 (사전/결과 해설 + Redis 캐싱)
```

---

## 완료 기준

```bash
# FastAPI 서버 실행 상태에서
GET http://localhost:8000/commentary/31/pre
# → AI 해설 텍스트 반환 (600자 이상)
# → 면책 문구 포함 확인
# → Redis에 캐시 저장 확인

GET http://localhost:8000/commentary/31/pre  (재호출)
# → Redis 캐시에서 즉시 반환 (GPT 재호출 없음)
```
