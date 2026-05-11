# 13. RacePulse AI 해설 생성 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
GPT-4o-mini를 이용해 경주 사전 해설(금요일)과 결과 해설(월요일)을 자동 생성합니다.
Redis 캐싱으로 비용을 최소화하고 APScheduler로 자동화합니다.

---

## 프로젝트 환경
- Python 3.13
- FastAPI 0.115.12
- OpenAI SDK 1.x
- LangChain (선택적 활용)
- Redis (캐싱)
- APScheduler
- 포트: 8000

---

## 해설 생성 규칙

### 사전 해설 (금요일 08:00 자동 생성)
생성 시점: 출전표 확정 후 자동
분량: 600~1000자
캐시 키: `pre_race:{meet_code}:{rc_date}:{race_no}`

구성:
```
1. 오늘의 핵심 변수 (트랙/날씨/거리)
2. 말별 심층 프로필
   - 강점/약점
   - 기수 콤비 히스토리
   - 컨디션 등급 (최하/하/중/상/최상)
   - 예상 기록 범위
   - "이길 수 있는 시나리오"
3. 5대 궁금증 해소
   - 트랙 적합성 / 기수-말 궁합 / 최근 폼 / 역사적 패턴 / 다크호스
4. 관전 포인트 + 이변 가능성
```

### 결과 해설 (월요일 14:00 자동 생성)
생성 시점: 경기 결과 수집 후 자동
분량: 800~1200자
캐시 키: `post_race:{meet_code}:{rc_date}:{race_no}`

구성:
```
1. 이변 지수 (Upset Meter) - 배당률 기반 수치화
2. 경기 하이라이트 + 결정적 구간 분석
3. ML 예측 vs 실제 결과 복기 (솔직하게)
4. 역대 기록과 비교
5. 카운터팩추얼 분석 ("만약 기수 변경이 없었다면?")
6. 라이벌 구도 업데이트
7. 다음 주 예고
```

---

## 사행성 방지 시스템 프롬프트 (고정)
```
절대 금지:
- "베팅 추천", "이 말에 투자", "확실한 1위"
- 특정 말이 반드시 이긴다는 표현

필수 포함:
- "데이터 기준", "통계적으로", "참고용 분석"

하단 고정 면책 문구:
"본 해설은 순수 데이터 분석 목적이며,
베팅 등 사행 행위와 무관합니다."
```

---

## 구현 파일 목록

### 1. AI 해설 서비스
`app/services/ai_commentary.py`

구현 메서드:
- `generate_pre_race_commentary(race_id)` → 사전 해설 생성
- `generate_post_race_commentary(race_id)` → 결과 해설 생성
- `build_pre_race_prompt(race_data)` → 사전 해설 프롬프트 조립
- `build_post_race_prompt(race_data, result_data)` → 결과 해설 프롬프트 조립
- `get_from_cache(cache_key)` → Redis 캐시 조회
- `save_to_cache(cache_key, content)` → Redis 캐시 저장
- `save_to_db(race_id, type, content)` → ai_commentary 테이블 저장

### 2. ai_commentary 모델
`app/models/ml.py` 에 추가:
- `AICommentary` 클래스 → ai_commentary 테이블
```
id, race_id(FK), type(PRE/POST),
content(TEXT), model_used,
cache_key, generated_at
```

### 3. 스케줄러 추가
`app/scheduler/scheduler.py` 에 추가:
```
금요일 08:00 → generate_all_pre_race_commentary()
월요일 14:00 → generate_all_post_race_commentary()
```

### 4. API 엔드포인트
Spring Boot `commentary` 관련 (FastAPI에서 생성 후 Spring Boot가 제공):
- `GET /api/v1/commentary/{raceId}/pre` → 사전 해설 조회
- `GET /api/v1/commentary/{raceId}/post` → 결과 해설 조회
- `POST /admin/commentary/regenerate` → 수동 재생성 (관리자)

---

## 비용 관리
```
모델: gpt-4o-mini (기본)
캐싱: Redis에 영구 저장 (경주당 최대 2회 호출로 고정)
경주당 최대 GPT 호출: 2회 (사전 1회 + 결과 1회)
품질 기준: 부족 시 gpt-4o로 업그레이드 검토
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- OpenAI API 호출 방법 설명 (messages 구조, role: system/user/assistant)
- 시스템 프롬프트와 유저 프롬프트 차이 설명
- Redis 캐시를 쓰는 이유 설명 (비용 절감)
- 토큰(token)이 무엇인지 설명
- LangChain을 선택적으로 쓰는 경우 체인 개념 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- GPT 응답 한글이 깨지지 않도록 확인

---

## 완료 기준
1. `POST http://localhost:8000/admin/commentary/generate/pre/1` 실행 시 GPT 해설 생성
2. `ai_commentary` 테이블에 해설 저장 확인
3. Redis에 캐시 저장 확인 (`pre_race:SC:20260508:1`)
4. Spring Boot `/api/v1/commentary/1/pre` 에서 해설 조회 성공
5. 면책 문구 포함 확인
6. 사행성 표현 없음 확인
