# 35. RacePulse AI 해설 고도화 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, AI 해설 기존 구현 내용
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (AI 해설 고도화 방향)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: 없음 — 독립적으로 실행 가능

---

## 🗂️ 지금까지 한 작업 요약

### 현재 AI 해설 구현 (Phase 2 완료)
- **파일**: `ml-server/app/services/ai_commentary.py`
- **모델**: `gpt-4o-mini` (단일 모델, 사전/결과 구분 없음)
- **temperature**: `0.7` 고정 (사전/결과 구분 없음)
- **품질 관리**: 없음
- **DB 컬럼**: `model_used`, `prompt_tokens`, `completion_tokens` (V9에서 생성)

### Phase 3에서 추가된 것 (V13 마이그레이션 완료)
- `ai_commentary` 테이블에 품질 컬럼 추가됨:
  - `quality_score SMALLINT` — 0~100점
  - `temperature_used NUMERIC(3,2)` — 사용된 temperature 값 기록
  - `retry_count SMALLINT` — 재시도 횟수
  - `generation_ms INTEGER` — 생성 소요 시간(ms)

---

## 목표

`ml-server/app/services/ai_commentary.py` 파일을 수정합니다.
기존 로직을 **최대한 유지**하면서 아래 4가지만 추가합니다.

---

## 프로젝트 환경

- **ML 서버**: FastAPI / Python 3.11
- **OpenAI SDK**: `openai` (이미 설치됨)
- **GPT 모델**: `gpt-4.1` (사전 해설), `gpt-4.1-mini` (결과 해설)
- **DB**: `ai_commentary` 테이블 (V9 + V13 컬럼 추가됨)

---

## 구현 사항 (4가지)

### 변경 1: 모델 및 temperature 분리

```python
# 기존 (변경 전)
DEFAULT_MODEL = "gpt-4o-mini"
# _call_gpt() 안에서 temperature=0.7 고정

# 변경 후
# 14차 회의 확정: 사전 해설 = GPT-4.1(창의적), 결과 해설 = GPT-4.1-mini(사실 기반)
PRE_RACE_MODEL   = "gpt-4.1"       # 사전 해설 — 더 풍부한 표현력
POST_RACE_MODEL  = "gpt-4.1-mini"  # 결과 해설 — 비용 절감 + 정확성 우선
PRE_TEMPERATURE  = 0.7             # 사전 해설 — 창의적인 표현 허용
POST_TEMPERATURE = 0.3             # 결과 해설 — 사실 기반, 일관된 어조
```

`generate_pre_race_commentary()` → `PRE_RACE_MODEL`, `PRE_TEMPERATURE` 사용
`generate_post_race_commentary()` → `POST_RACE_MODEL`, `POST_TEMPERATURE` 사용

`_call_gpt()`에 `model`과 `temperature` 파라미터 추가:
```python
async def _call_gpt(
    self,
    user_prompt: str,
    model: str = PRE_RACE_MODEL,
    temperature: float = PRE_TEMPERATURE,
) -> tuple[str, dict]:
```

### 변경 2: 사행성 이중 필터 + 자동 retry

14차 회의 확정: GPT 시스템 프롬프트 1차 + BE 키워드 스캔 2차 / retry 2회 / fallback 템플릿

```python
# 사행성 금지어 목록 (이 단어가 해설에 포함되면 재시도)
FORBIDDEN_KEYWORDS = [
    "베팅 추천", "이 말에 걸어라", "확실한 1위", "승산이 높은",
    "투자하세요", "확실히 유리", "반드시 이길", "다크호스",
]

async def _check_and_filter(self, content: str) -> tuple[str, bool]:
    """
    생성된 해설에서 사행성 표현을 검사합니다.
    
    @return (content, is_clean)
      is_clean = True  → 사행성 없음, 그대로 사용
      is_clean = False → 사행성 감지, 재시도 필요
    """
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in content:
            logger.warning("[사행성 필터] 금지어 감지: '%s'", keyword)
            return content, False
    return content, True
```

`_call_gpt_with_retry()` 신규 메서드:
```python
async def _call_gpt_with_retry(
    self,
    user_prompt: str,
    model: str,
    temperature: float,
    max_retries: int = 2,
) -> tuple[str, dict, int]:
    """
    사행성 필터 통과할 때까지 최대 max_retries번 재시도합니다.
    
    @return (content, usage, retry_count)
    """
    start_ms = int(datetime.now().timestamp() * 1000)
    
    for attempt in range(max_retries + 1):
        content, usage = await self._call_gpt(user_prompt, model, temperature)
        content, is_clean = await self._check_and_filter(content)
        
        if is_clean:
            elapsed_ms = int(datetime.now().timestamp() * 1000) - start_ms
            return content, usage, attempt
        
        if attempt < max_retries:
            logger.info("[사행성 필터] %d차 재시도...", attempt + 1)
    
    # 최대 재시도 초과 → fallback 템플릿 사용
    logger.error("[사행성 필터] %d회 재시도 초과. fallback 템플릿 사용.", max_retries)
    elapsed_ms = int(datetime.now().timestamp() * 1000) - start_ms
    return self._get_fallback_template(), {}, max_retries
```

fallback 템플릿:
```python
def _get_fallback_template(self) -> str:
    """GPT 재시도 초과 시 사용하는 기본 템플릿입니다."""
    return (
        "이번 경주의 데이터 분석이 일시적으로 제공되지 않습니다.\n"
        "출전마 정보는 경주 상세 페이지에서 확인하세요.\n\n"
        "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."
    )
```

### 변경 3: 품질 점수 계산 및 DB 저장

```python
def _calculate_quality_score(
    self,
    content: str,
    retry_count: int,
    is_fallback: bool,
) -> int:
    """
    AI 해설의 품질을 0~100점으로 채점합니다.
    
    14차 회의 확정 기준:
      HIGH (80+): 정상 생성, 면책문구 포함, 적정 길이
      MED  (50~79): 재시도 발생 또는 짧은 해설
      LOW  (0~49): 2회 재시도 or fallback 사용
    
    연속 LOW 3회 시 관리자 알림 (이 함수 밖에서 처리)
    """
    if is_fallback:
        return 10  # fallback = 최저점
    
    score = 100
    
    # 재시도할수록 점수 감소
    score -= retry_count * 20
    
    # 면책 문구 없으면 감점
    if "사행 행위와 무관" not in content:
        score -= 15
    
    # 너무 짧으면 감점 (300자 미만)
    if len(content) < 300:
        score -= 20
    
    return max(0, min(100, score))
```

`save_to_db()`에 V13 품질 컬럼 추가:
```python
async def save_to_db(
    self,
    race_id: int,
    commentary_type: str,
    content: str,
    cache_key: str,
    model_used: str,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    # V13에서 추가된 품질 컬럼들
    quality_score: Optional[int] = None,
    temperature_used: Optional[float] = None,
    retry_count: int = 0,
    generation_ms: Optional[int] = None,
) -> AICommentary:
```

### 변경 4: 시스템 프롬프트 고도화 (Chain-of-Thought + Few-shot)

14차 회의 확정: "스포츠 중계 해설위원" 관점 + Chain-of-Thought 4단계 + Few-shot 예시

기존 `SYSTEM_PROMPT` 상수를 아래로 교체:

```python
SYSTEM_PROMPT = """당신은 경마 전문 데이터 분석 해설위원입니다.
스포츠 중계 해설위원의 시각으로 경마 데이터를 분석하고, 흥미롭고 객관적인 해설을 작성합니다.

[분석 4단계 Chain-of-Thought]
1단계: 트랙/날씨/거리 — 오늘 경주 환경이 어떤 스타일의 말에 유리한가?
2단계: 출전마 현황 — 각 말의 최근 폼, 기수 궁합, 컨디션 신호는?
3단계: 핵심 변수 — 예상치 못한 변수(기수 변경, 마체중 급변 등)가 있는가?
4단계: 관전 포인트 — 이 경주에서 주목해야 할 순간은?

[절대 금지 표현]
- "베팅 추천", "이 말에 걸어라", "확실한 1위", "승산이 높은", "투자하세요"
- "반드시 이길", "확실히 유리", "다크호스" (단, "이변 가능성이 큽니다"는 허용)
- 특정 말을 단정하는 표현 ("A가 무조건 우승", "B는 절대 안 됨")

[필수 포함 표현]
- "데이터 기준으로", "통계적으로", "참고용 분석으로"
- 해설 하단 고정 면책 문구:
  "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."

[Few-shot 예시 — 좋은 표현]
✅ "통계적으로 이 조건에서 선행마의 3착 이내 비율은 68%였습니다."
✅ "데이터 기준으로 이 기수-말 조합의 최근 10경주 TOP3 진입률은 40%입니다."
✅ "이변 가능성이 큽니다 — 최근 컨디션 상승세가 배당률에 반영되지 않았습니다."

[Few-shot 예시 — 나쁜 표현]
❌ "이 말에 걸어보세요."
❌ "확실히 1위 후보입니다."
❌ "다크호스로 주목하세요."

한국어로 작성하세요."""
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `temperature` 값이 왜 사전/결과 해설에서 다른지 설명 (창의성 vs 정확성)
- `gpt-4.1` vs `gpt-4.1-mini`의 차이 설명 (품질 vs 비용)
- Chain-of-Thought가 왜 해설 품질을 높이는지 설명 (단계별 사고 유도)
- Few-shot이 무엇인지 설명 (예시를 보여주면 GPT가 스타일을 따라함)
- `quality_score`가 왜 필요한지 설명 (관리자가 해설 품질 모니터링 가능)
- `generation_ms`가 왜 기록되는지 설명 (GPT 응답이 느리면 UX에 영향)

---

## 인코딩 주의사항 ⚠️

- 파일 최상단: `# -*- coding: utf-8 -*-`
- UTF-8 (BOM 없음) 저장

---

## Git 규칙

```
브랜치: feat/phase3-be-ai
커밋 메시지: feat: [prompt-35] AI 해설 고도화 — GPT-4.1 전환 + temperature 분리 + 사행성 이중 필터 + 품질 점수
```

---

## 완료 기준

```bash
# 1. ML 서버 기동
cd racepulse/ml-server
uvicorn app.main:app --port 8000 --reload

# 2. 사행성 필터 단위 테스트
python -c "
import asyncio
from app.services.ai_commentary import AICommentaryService

svc = AICommentaryService.__new__(AICommentaryService)

# 금지어 포함 → is_clean = False
async def test():
    _, clean = await svc._check_and_filter('이 말에 베팅 추천합니다.')
    assert not clean, '금지어 감지 실패'

    _, clean2 = await svc._check_and_filter('통계적으로 이 말의 3착 비율은 68%입니다.')
    assert clean2, '정상 해설 오탐지'

    print('OK')

asyncio.run(test())
"

# 3. 품질 점수 계산 테스트
python -c "
from app.services.ai_commentary import AICommentaryService

svc = AICommentaryService.__new__(AICommentaryService)
score = svc._calculate_quality_score(
    content='통계적으로 분석합니다. 본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다.' * 5,
    retry_count=0,
    is_fallback=False
)
assert score >= 80, f'정상 해설 점수가 너무 낮음: {score}'
print(f'품질 점수: {score} — OK')
"
```
