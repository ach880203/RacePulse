# -*- coding: utf-8 -*-
# =============================================================================
# ai_commentary.py — GPT 기반 경주 해설 자동 생성 서비스
# =============================================================================
# OpenAI API 호출 구조 설명:
#   messages = [ {"role": "system", "content": "..."}, {"role": "user", "content": "..."} ]
#
#   role: "system"    = AI의 역할/성격/제약을 설정하는 초기 지시입니다.
#                       예: "너는 경마 데이터 분석가야. 절대 베팅을 추천하면 안 돼."
#   role: "user"      = 실제 사용자가 보내는 질문/요청입니다.
#                       예: "이번 서울 3경주 출전마 분석해줘."
#   role: "assistant" = GPT의 이전 답변입니다. (다중 턴 대화에 사용)
#
# 토큰(Token)이란?
#   GPT가 텍스트를 처리하는 기본 단위입니다.
#   한국어 1글자 ≈ 2~3토큰, 영어 단어 1개 ≈ 1~2토큰
#   gpt-4o-mini 기준 입력+출력 1,000토큰 = 약 $0.00015 (매우 저렴)
#
# Redis 캐시를 쓰는 이유:
#   같은 경주의 해설을 요청할 때마다 GPT를 새로 호출하면 비용이 배로 늘어납니다.
#   한 번 생성한 해설을 Redis에 저장해두면, 두 번째 요청부터는 GPT 호출 없이 바로 반환합니다.
#   경주당 최대 2회 호출(사전 1회 + 결과 1회)로 비용을 고정할 수 있습니다.
# =============================================================================

# logging = 서버 로그를 기록합니다.
import logging
# json = 파이썬 딕셔너리를 JSON 문자열로 변환하는 표준 라이브러리입니다.
import json
# datetime = 생성 시각 기록에 사용합니다.
from datetime import datetime, timedelta, date
# Optional = 값이 없을 수도 있는 타입 힌트입니다.
from typing import Optional, Any

# openai = GPT-4o-mini를 호출하는 OpenAI 공식 파이썬 SDK입니다.
from openai import AsyncOpenAI

# SQLAlchemy 도구들
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.core.config import settings
from app.core.redis_client import get_redis_client
from app.models.race import Race, RaceEntry, RaceResult
from app.models.master import Horse, Jockey
from app.models.ml import AICommentary

logger = logging.getLogger(__name__)

# =============================================================================
# 설정 상수
# =============================================================================
# 기본 GPT 모델 — 비용 효율이 좋은 gpt-4o-mini를 사용합니다.
DEFAULT_MODEL      = "gpt-4o-mini"
# 최대 출력 토큰 수 — 해설이 너무 길어지지 않게 제한합니다.
MAX_TOKENS         = 1200
# Redis 캐시 만료 시간 — 7일(초 단위). 오래된 경주 해설은 자동 삭제됩니다.
CACHE_TTL_SECONDS  = 7 * 24 * 60 * 60

# =============================================================================
# 사행성 방지 시스템 프롬프트 (모든 해설에 고정 적용)
# =============================================================================
# 시스템 프롬프트 = GPT에게 "너의 역할과 제약"을 설명하는 첫 번째 메시지입니다.
# 이 내용은 사용자 요청보다 우선순위가 높아, GPT가 이 규칙을 반드시 따르게 됩니다.
SYSTEM_PROMPT = """당신은 경마 데이터 분석 전문가입니다.
주어진 경주 데이터를 바탕으로 객관적이고 흥미로운 해설을 작성합니다.

[절대 금지 사항]
- "베팅 추천", "이 말에 투자", "확실한 1위" 같은 사행성 표현
- 특정 말이 반드시 이긴다는 단정적 표현
- 개인 의견으로 포장된 투자 조언

[필수 포함 사항]
- 모든 분석에 "데이터 기준", "통계적으로", "참고용 분석" 표현 포함
- 해설 하단에 반드시 면책 문구 포함:
  "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."

[작성 스타일]
- 한국어로 작성
- 흥미롭고 읽기 쉬운 문체
- 데이터와 통계에 근거한 객관적 분석
- 전문 용어는 쉬운 말로 설명"""


class AICommentaryService:
    """경주 사전/결과 해설을 GPT로 생성하고 Redis와 DB에 저장하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        # AsyncOpenAI = OpenAI API를 비동기 방식으로 호출하는 클라이언트입니다.
        # api_key = .env의 OPENAI_API_KEY 값을 자동으로 읽습니다.
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self.redis  = get_redis_client()

    # =========================================================================
    # 공개 메서드 — 해설 생성 진입점
    # =========================================================================

    async def generate_pre_race_commentary(self, race_id: int) -> dict[str, Any]:
        """경주 사전 해설을 생성합니다.

        캐시 → DB → GPT 순서로 조회합니다.
        이미 생성된 해설이 있으면 GPT를 호출하지 않고 바로 반환합니다.

        @param race_id  해설을 생성할 경주 ID
        @return 생성된 해설 정보 딕셔너리
        """
        race_data = await self._get_race_data(race_id)
        if not race_data:
            raise ValueError(f"경주 정보를 찾을 수 없습니다: race_id={race_id}")

        race   = race_data["race"]
        entries = race_data["entries"]
        cache_key = self._make_cache_key(
            "pre_race", race.meet_code, str(race.rc_date), race.race_no
        )

        # 1. Redis 캐시 먼저 확인 (GPT 호출 없이 즉시 반환)
        cached = await self.get_from_cache(cache_key)
        if cached:
            logger.info("[AI 해설] 캐시 히트. cache_key=%s", cache_key)
            return {"content": cached, "source": "cache", "cache_key": cache_key}

        # 2. DB에서 기존 해설 조회 (Redis가 만료됐을 때 복구용)
        existing = await self._get_from_db(race_id, "PRE")
        if existing:
            await self.save_to_cache(cache_key, existing.content)
            return {"content": existing.content, "source": "db", "cache_key": cache_key}

        # 3. GPT로 새 해설 생성
        prompt = self.build_pre_race_prompt(race_data)
        content, usage = await self._call_gpt(prompt)

        # 4. Redis 캐시에 저장
        await self.save_to_cache(cache_key, content)

        # 5. DB에 영구 저장
        record = await self.save_to_db(
            race_id=race_id,
            commentary_type="PRE",
            content=content,
            cache_key=cache_key,
            model_used=DEFAULT_MODEL,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

        logger.info("[AI 해설] 사전 해설 생성 완료. race_id=%d, 토큰=%s", race_id, usage)
        return {
            "content": content,
            "source": "gpt",
            "cache_key": cache_key,
            "usage": usage,
        }

    async def generate_post_race_commentary(self, race_id: int) -> dict[str, Any]:
        """경주 결과 해설을 생성합니다.

        @param race_id  해설을 생성할 경주 ID
        """
        race_data   = await self._get_race_data(race_id)
        result_data = await self._get_result_data(race_id)
        if not race_data:
            raise ValueError(f"경주 정보를 찾을 수 없습니다: race_id={race_id}")

        race = race_data["race"]
        cache_key = self._make_cache_key(
            "post_race", race.meet_code, str(race.rc_date), race.race_no
        )

        cached = await self.get_from_cache(cache_key)
        if cached:
            return {"content": cached, "source": "cache", "cache_key": cache_key}

        existing = await self._get_from_db(race_id, "POST")
        if existing:
            await self.save_to_cache(cache_key, existing.content)
            return {"content": existing.content, "source": "db", "cache_key": cache_key}

        prompt = self.build_post_race_prompt(race_data, result_data)
        content, usage = await self._call_gpt(prompt)

        await self.save_to_cache(cache_key, content)
        await self.save_to_db(
            race_id=race_id,
            commentary_type="POST",
            content=content,
            cache_key=cache_key,
            model_used=DEFAULT_MODEL,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
        )

        logger.info("[AI 해설] 결과 해설 생성 완료. race_id=%d", race_id)
        return {"content": content, "source": "gpt", "cache_key": cache_key, "usage": usage}

    # =========================================================================
    # 프롬프트 조립 메서드
    # =========================================================================

    def build_pre_race_prompt(self, race_data: dict[str, Any]) -> str:
        """사전 해설 유저 프롬프트를 조립합니다.

        유저 프롬프트 = 실제 분석 요청입니다.
        시스템 프롬프트에서 정한 규칙 안에서 이 내용을 GPT가 처리합니다.
        """
        race    = race_data["race"]
        entries = race_data["entries"]

        entries_text = "\n".join(
            f"  - {e['gate_no']}번 {e['horse_name']} | 기수: {e['jockey_name'] or '미정'}"
            f" | 마체중: {e['horse_weight'] or '?'}kg"
            f" | 배당: {e['odds_win'] or '?'}"
            for e in entries
        )

        return f"""다음 경주의 사전 해설을 작성해주세요.

[경주 정보]
- 경주명: {race.race_name}
- 경마장: {race.meet_code} | 날짜: {race.rc_date} | 거리: {race.distance}m
- 트랙 상태: {race.track_condition or '미정'} | 날씨: {race.weather or '미정'}
- 출발 시각: {race.start_time or '미정'}

[출전마 목록]
{entries_text}

[요청 구성 — 600~1000자로 작성]
1. 오늘의 핵심 변수 (트랙/날씨/거리 영향 분석)
2. 주목할 출전마 프로필 (강점/약점, 최근 폼, 컨디션 등급)
3. 5대 궁금증 해소 (트랙 적합성, 기수-말 궁합, 다크호스)
4. 관전 포인트 + 이변 가능성

모든 분석은 데이터 기준으로, 사행성 표현 없이 작성하세요.
하단에 면책 문구를 반드시 포함하세요."""

    def build_post_race_prompt(
        self,
        race_data: dict[str, Any],
        result_data: list[dict[str, Any]],
    ) -> str:
        """결과 해설 유저 프롬프트를 조립합니다."""
        race = race_data["race"]

        results_text = "\n".join(
            f"  {r['rank']}위: {r['horse_name']} (배당 {r['final_odds'] or '?'}, 기록 {r['record_time'] or '?'})"
            for r in sorted(result_data, key=lambda x: x.get("rank") or 99)
            if r.get("rank")
        ) or "  결과 데이터 없음"

        return f"""다음 경주의 결과 해설을 작성해주세요.

[경주 정보]
- 경주명: {race.race_name}
- 경마장: {race.meet_code} | 날짜: {race.rc_date} | 거리: {race.distance}m

[경주 결과]
{results_text}

[요청 구성 — 800~1200자로 작성]
1. 이변 지수 (배당률 기반 — 1위 배당이 높을수록 이변)
2. 경기 하이라이트 + 결정적 구간 분석
3. 통계적 의미 분석 (역대 기록과 비교)
4. 카운터팩추얼 분석 ("만약 다른 조건이었다면?")
5. 라이벌 구도 업데이트
6. 다음 주 예고

모든 분석은 데이터 기준으로, 사행성 표현 없이 작성하세요.
하단에 면책 문구를 반드시 포함하세요."""

    # =========================================================================
    # 캐시 관리 메서드
    # =========================================================================

    async def get_from_cache(self, cache_key: str) -> Optional[str]:
        """Redis에서 해설 캐시를 조회합니다.

        캐시가 있으면 GPT를 호출하지 않으므로 비용이 0원입니다.
        """
        try:
            return await self.redis.get(f"commentary:{cache_key}")
        except Exception as exc:
            logger.warning("[캐시] 조회 실패: %s", exc)
            return None

    async def save_to_cache(self, cache_key: str, content: str) -> None:
        """Redis에 해설을 저장합니다. 7일 후 자동 삭제됩니다."""
        try:
            await self.redis.set(
                f"commentary:{cache_key}",
                content,
                ex=CACHE_TTL_SECONDS,
            )
            logger.debug("[캐시] 저장 완료. key=%s", cache_key)
        except Exception as exc:
            logger.warning("[캐시] 저장 실패: %s", exc)

    # =========================================================================
    # DB 저장 메서드
    # =========================================================================

    async def save_to_db(
        self,
        race_id: int,
        commentary_type: str,
        content: str,
        cache_key: str,
        model_used: str = DEFAULT_MODEL,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
    ) -> AICommentary:
        """해설을 ai_commentary 테이블에 저장합니다.

        같은 경주의 같은 타입 해설이 이미 있으면 내용을 업데이트합니다.
        """
        existing = await self._get_from_db(race_id, commentary_type)
        if existing:
            # 기존 해설 업데이트
            existing.content           = content
            existing.model_used        = model_used
            existing.cache_key         = cache_key
            existing.prompt_tokens     = prompt_tokens
            existing.completion_tokens = completion_tokens
            existing.generated_at      = datetime.now()
            await self.db.commit()
            return existing

        record = AICommentary(
            race_id           = race_id,
            type              = commentary_type,
            content           = content,
            model_used        = model_used,
            cache_key         = cache_key,
            prompt_tokens     = prompt_tokens,
            completion_tokens = completion_tokens,
        )
        self.db.add(record)
        await self.db.commit()
        return record

    # =========================================================================
    # 내부 헬퍼 메서드
    # =========================================================================

    async def _call_gpt(self, user_prompt: str) -> tuple[str, dict]:
        """OpenAI API를 호출하여 해설 텍스트를 생성합니다.

        messages 구조:
          [{"role": "system", "content": 시스템 프롬프트},
           {"role": "user",   "content": 유저 프롬프트}]

        system 메시지 = AI의 페르소나와 제약을 정의 (항상 첫 번째)
        user 메시지   = 실제 분석 요청 내용
        """
        response = await self.openai.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_prompt},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.7,  # 0 = 항상 같은 답, 1 = 창의적인 답. 0.7 = 균형
        )

        content = response.choices[0].message.content or ""
        usage   = {
            "prompt_tokens":     response.usage.prompt_tokens     if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
        }
        return content, usage

    async def _get_race_data(self, race_id: int) -> Optional[dict[str, Any]]:
        """경주와 출전마 정보를 한꺼번에 조회합니다."""
        from sqlalchemy.orm import selectinload

        race = await self.db.get(Race, race_id)
        if not race:
            return None

        entries_stmt = (
            select(RaceEntry)
            .options(selectinload(RaceEntry.horse), selectinload(RaceEntry.jockey))
            .where(RaceEntry.race_id == race_id)
            .order_by(RaceEntry.gate_no)
        )
        entries = list((await self.db.scalars(entries_stmt)).all())

        entries_info = [
            {
                "gate_no":      e.gate_no,
                "horse_name":   e.horse.name if e.horse else "?",
                "jockey_name":  e.jockey.name if e.jockey else None,
                "horse_weight": e.horse_weight,
                "odds_win":     float(e.odds_win) if e.odds_win else None,
            }
            for e in entries
        ]

        return {"race": race, "entries": entries_info}

    async def _get_result_data(self, race_id: int) -> list[dict[str, Any]]:
        """경주 결과 정보를 조회합니다."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(RaceResult)
            .options(selectinload(RaceResult.horse))
            .where(RaceResult.race_id == race_id)
        )
        results = list((await self.db.scalars(stmt)).all())

        return [
            {
                "rank":        r.rank,
                "horse_name":  r.horse.name if r.horse else "?",
                "record_time": r.record_time,
                "final_odds":  None,  # TODO: race_entry에서 최종 배당 조회
            }
            for r in results
        ]

    async def _get_from_db(
        self, race_id: int, commentary_type: str
    ) -> Optional[AICommentary]:
        """DB에서 기존 해설을 조회합니다."""
        stmt = select(AICommentary).where(
            and_(
                AICommentary.race_id == race_id,
                AICommentary.type == commentary_type,
            )
        )
        return await self.db.scalar(stmt)

    @staticmethod
    def _make_cache_key(
        prefix: str, meet_code: str, rc_date: str, race_no: int
    ) -> str:
        """Redis 캐시 키를 만듭니다.
        형식: pre_race:SC:20260508:1
        """
        date_compact = rc_date.replace("-", "")
        return f"{prefix}:{meet_code}:{date_compact}:{race_no}"
