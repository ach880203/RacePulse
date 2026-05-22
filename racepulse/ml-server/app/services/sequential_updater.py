# -*- coding: utf-8 -*-
"""
sequential_updater.py — Sequential Race Dynamics
=================================================
같은 날 앞 경주 결과가 뒷 경주 예측에 영향을 줍니다.
Redis에 당일 경주 결과를 임시 저장하고,
뒷 경주 예측 시 트랙 컨디션·기수 폼 등을 자동 반영합니다.

[Redis Key 구조]
race:today:{rc_date}:{race_no}:result     → 완료된 경주 착순 데이터
race:today:{rc_date}:track_condition      → 당일 트랙 상태 실황
race:today:{rc_date}:{jockey_id}:form     → 기수 당일 폼 (금일 성적)

[TTL]
자정(00:00) 자동 만료 → 다음 날 데이터에 영향 없음
"""

# asyncio = 비동기 Redis 클라이언트를 동기 테스트에서도 실행할 때 사용하는 표준 도구입니다.
import asyncio
# inspect = Redis 호출 결과가 await가 필요한 코루틴인지 확인할 때 사용합니다.
import inspect
# json = Python dict/list를 Redis에 저장 가능한 문자열로 바꾸고, 다시 되돌릴 때 사용합니다.
import json
# datetime/time/timedelta = KST 기준 자정까지 남은 TTL을 계산할 때 사용합니다.
from datetime import datetime, time, timedelta
# Any = Redis나 DB에서 들어오는 다양한 타입을 안전하게 설명하기 위한 타입 힌트입니다.
from typing import Any
# ZoneInfo = 한국 경마 날짜는 한국 시간 기준이므로 KST 시간대를 명시할 때 사용합니다.
from zoneinfo import ZoneInfo

# text = 직접 작성한 SQL을 SQLAlchemy 비동기 세션에서 실행하게 해주는 도구입니다.
from sqlalchemy import text
# AsyncSession = FastAPI 서비스에서 DB를 비동기로 조회하기 위한 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# get_redis_client = 앱 전체에서 공유하는 Redis 연결을 가져오는 함수입니다.
from app.core.redis_client import get_redis_client


KST = ZoneInfo("Asia/Seoul")


class SequentialUpdater:
    """당일 앞 경주 결과를 Redis에 저장하고 뒤 경주 예측 확률을 미세 보정합니다."""

    def __init__(self, redis: Any | None = None, db_session: AsyncSession | None = None) -> None:
        # redis를 직접 넣으면 테스트에서 가짜 Redis를 사용할 수 있습니다.
        # 직접 넣지 않으면 운영 Redis 연결을 가져옵니다.
        self.redis = redis if redis is not None else get_redis_client()
        # db_session은 API에서 실제 경주 결과를 DB에서 읽어올 때만 사용합니다.
        self.db = db_session

    def store_race_result(self, rc_date: str, race_no: int, result_data: dict[str, Any]) -> None:
        """동기 테스트용 래퍼입니다. 운영 API에서는 async 버전을 사용합니다."""
        self._run_blocking(self.store_race_result_async(rc_date, race_no, result_data))

    async def store_race_result_async(self, rc_date: str, race_no: int, result_data: dict[str, Any]) -> None:
        """경주 완료 시 착순, 트랙 상태, 기수 당일 폼을 Redis에 저장합니다."""
        ttl_seconds = self.seconds_until_midnight()
        result_key = self._race_result_key(rc_date, race_no)

        # Redis는 문자열 중심 저장소입니다.
        # 그래서 dict/list를 그대로 넣지 않고 json.dumps로 문자열로 바꿉니다.
        # ensure_ascii=False를 쓰면 한글 "착순", "습윤"이 깨지지 않고 저장됩니다.
        await self._call_redis(
            "setex",
            result_key,
            ttl_seconds,
            json.dumps(result_data, ensure_ascii=False),
        )

        track_condition = self._extract_track_condition(result_data)
        if track_condition is not None:
            # setex = set + expire의 줄임말입니다.
            # 값을 저장하면서 동시에 만료 시간을 걸어두기 때문에 당일 데이터가 다음 날까지 남지 않습니다.
            await self._call_redis(
                "setex",
                self._track_condition_key(rc_date),
                ttl_seconds,
                str(track_condition),
            )

        # 기수 폼은 날짜마다 달라지는 컨디션입니다.
        # 그래서 과거 전체 성적이 아니라 "오늘 앞 경주에서 몇 번 탔고 몇 번 이겼는지"만 Redis에 저장합니다.
        for horse_result in self._extract_finish_order(result_data):
            jockey_id = self._safe_int(horse_result.get("jockey_id"))
            position = self._safe_int(horse_result.get("position") or horse_result.get("rank"))
            if jockey_id is None or position is None:
                continue
            await self._update_jockey_form_async(rc_date, jockey_id, position)

    def get_sequential_adjustments(self, rc_date: str, target_race_no: int) -> dict[str, Any]:
        """동기 테스트용 조정값 조회 래퍼입니다."""
        return self._run_blocking(self.get_sequential_adjustments_async(rc_date, target_race_no))

    async def get_sequential_adjustments_async(self, rc_date: str, target_race_no: int) -> dict[str, Any]:
        """목표 경주 이전에 끝난 경주들을 바탕으로 Sequential 조정값을 계산합니다."""
        completed_races = await self._get_completed_race_numbers(rc_date, target_race_no)
        track_condition = await self._call_redis("get", self._track_condition_key(rc_date))
        jockey_forms = await self._get_all_jockey_forms(rc_date)
        normalized_track = self._normalize_track_condition(track_condition)

        return {
            "track_condition": track_condition,
            # track_bias는 추입마(CLOSER)에 더해지는 방향성입니다.
            # 습윤/다습에서는 선두가 체력 소모를 크게 겪어 뒤에서 따라오는 말이 유리해질 수 있습니다.
            "track_bias": self._track_bias_for_closer(normalized_track),
            "track_uncertainty": 0.08 if normalized_track == "SATURATED" else 0.0,
            "jockey_forms": jockey_forms,
            "completed_races": completed_races,
            "sequential_available": bool(completed_races or track_condition or jockey_forms),
        }

    def apply_sequential_prior(
        self,
        entries: list[dict[str, Any]],
        adjustments: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """각 말의 예측 확률에 트랙 상태와 기수 당일 폼을 반영합니다."""
        if not entries:
            return []

        normalized_track = self._normalize_track_condition(adjustments.get("track_condition"))
        jockey_forms = adjustments.get("jockey_forms") or {}
        adjusted_entries: list[dict[str, Any]] = []

        for entry in entries:
            copied = dict(entry)
            original_prob = self._safe_float(copied.get("win_prob")) or 0.0001
            running_style = str(
                copied.get("running_style") or copied.get("style") or ""
            ).upper()
            jockey_id = self._safe_int(copied.get("jockey_id"))
            factor = 1.0
            reasons: list[str] = []

            # 트랙 상태는 말의 주행 스타일과 맞물립니다.
            # 건조하면 앞에서 빠르게 달리는 선행마가 유리하고,
            # 습윤/다습이면 페이스가 무너지기 쉬워 추입마가 유리해질 수 있습니다.
            if normalized_track == "DRY" and running_style == "LEADER":
                factor *= 1.05
                reasons.append("건조 트랙 선행마 보정 +5%")
            elif normalized_track in {"WET", "HUMID"} and running_style == "CLOSER":
                factor *= 1.10
                reasons.append("습윤/다습 트랙 추입마 보정 +10%")
            elif normalized_track == "SATURATED":
                factor *= 0.97
                reasons.append("포화 트랙 불확실성 보정 -3%")

            jockey_form = jockey_forms.get(str(jockey_id)) if jockey_id is not None else None
            if jockey_form is not None:
                # 오늘 2승 이상이면 컨디션이 좋은 신호로 보고 소폭 상향합니다.
                # 반대로 3회 이상 탔는데 0승이면 당일 흐름이 좋지 않은 신호로 보고 소폭 하향합니다.
                if jockey_form.get("today_win", 0) >= 2:
                    factor *= 1.03
                    reasons.append("기수 당일 2승 이상 보정 +3%")
                elif jockey_form.get("today_win", 0) == 0 and jockey_form.get("today_race", 0) >= 3:
                    factor *= 0.97
                    reasons.append("기수 당일 0승 3경주 이상 보정 -3%")

            copied["sequential_prior_prob"] = original_prob
            copied["win_prob"] = max(original_prob * factor, 0.0001)
            copied["sequential_factor"] = round(factor, 4)
            copied["sequential_reasons"] = reasons
            adjusted_entries.append(copied)

        return self._normalize_entry_probabilities(adjusted_entries)

    async def load_completed_race_result(self, rc_date: str, completed_race_no: int) -> dict[str, Any] | None:
        """DB에 저장된 완료 경주 결과를 Redis 저장 형식으로 변환합니다."""
        if self.db is None:
            return None

        row = (
            await self.db.execute(
                text(
                    """
                    SELECT id, track_condition
                    FROM races
                    WHERE rc_date = CAST(:rc_date AS date)
                      AND race_no = :race_no
                    ORDER BY meet_code ASC
                    LIMIT 1
                    """
                ),
                {"rc_date": rc_date, "race_no": completed_race_no},
            )
        ).mappings().first()
        if row is None:
            return None

        result_rows = (
            await self.db.execute(
                text(
                    """
                    SELECT
                        rr.horse_id,
                        rr.rank AS position,
                        rr.record_time AS time,
                        re.jockey_id
                    FROM race_results rr
                    LEFT JOIN race_entries re ON re.id = rr.race_entry_id
                    WHERE rr.race_id = :race_id
                    ORDER BY rr.rank ASC NULLS LAST, rr.id ASC
                    """
                ),
                {"race_id": row["id"]},
            )
        ).mappings().all()

        return {
            "착순": [dict(result_row) for result_row in result_rows],
            "track_condition": row["track_condition"],
        }

    async def find_next_race_id(self, rc_date: str, completed_race_no: int) -> int | None:
        """완료된 경주 바로 다음 경주의 race_id를 조회합니다."""
        if self.db is None:
            return None
        row = (
            await self.db.execute(
                text(
                    """
                    SELECT id
                    FROM races
                    WHERE rc_date = CAST(:rc_date AS date)
                      AND race_no > :race_no
                    ORDER BY race_no ASC, meet_code ASC
                    LIMIT 1
                    """
                ),
                {"rc_date": rc_date, "race_no": completed_race_no},
            )
        ).mappings().first()
        return int(row["id"]) if row else None

    async def get_status_async(self, rc_date: str) -> dict[str, Any]:
        """FE에서 '몇 경주까지 반영됐는지' 표시할 수 있도록 Redis 상태를 조회합니다."""
        completed_races = await self._get_completed_race_numbers(rc_date, target_race_no=999)
        track_condition = await self._call_redis("get", self._track_condition_key(rc_date))
        return {
            "rc_date": rc_date,
            "completed_races": completed_races,
            "track_condition": track_condition,
            "jockey_forms": await self._get_all_jockey_forms(rc_date),
            "message": self._build_status_message(completed_races, track_condition),
        }

    @staticmethod
    def seconds_until_midnight() -> int:
        """KST 기준 자정까지 남은 초를 계산합니다."""
        # 경마 일정과 경주일(rc_date)은 한국 시간 기준입니다.
        # 서버가 UTC로 떠 있어도 TTL은 KST 자정에 맞춰야 다음 날 경주에 오늘 결과가 섞이지 않습니다.
        now = datetime.now(KST)
        next_midnight = datetime.combine(now.date() + timedelta(days=1), time.min, tzinfo=KST)
        return max(1, int((next_midnight - now).total_seconds()))

    async def _update_jockey_form_async(self, rc_date: str, jockey_id: int, position: int) -> None:
        """기수별 오늘 출전 수와 우승 수를 Redis에 누적 저장합니다."""
        key = self._jockey_form_key(rc_date, jockey_id)
        ttl_seconds = self.seconds_until_midnight()
        raw = await self._call_redis("get", key)
        form = json.loads(raw) if raw else {"today_win": 0, "today_race": 0}

        form["today_race"] = int(form.get("today_race", 0)) + 1
        if position == 1:
            form["today_win"] = int(form.get("today_win", 0)) + 1

        race_count = max(int(form.get("today_race", 0)), 1)
        form["form_factor"] = round(1.0 + min(form.get("today_win", 0), 3) * 0.1, 2)
        form["today_win_rate"] = round(form.get("today_win", 0) / race_count, 4)
        await self._call_redis("setex", key, ttl_seconds, json.dumps(form, ensure_ascii=False))

    async def _get_completed_race_numbers(self, rc_date: str, target_race_no: int) -> list[int]:
        """target_race_no보다 앞에 있는 완료 경주 번호를 Redis 키에서 찾습니다."""
        prefix = f"race:today:{rc_date}:"
        suffix = ":result"
        race_numbers: list[int] = []

        keys = await self._find_keys(f"{prefix}*{suffix}")
        for key in keys:
            key_text = self._decode_if_bytes(key)
            if not key_text.startswith(prefix) or not key_text.endswith(suffix):
                continue
            middle = key_text[len(prefix):-len(suffix)]
            race_no = self._safe_int(middle)
            if race_no is not None and race_no < target_race_no:
                race_numbers.append(race_no)
        return sorted(set(race_numbers))

    async def _get_all_jockey_forms(self, rc_date: str) -> dict[str, dict[str, Any]]:
        """오늘 저장된 모든 기수 폼을 Redis에서 모아 반환합니다."""
        prefix = f"race:today:{rc_date}:"
        suffix = ":form"
        forms: dict[str, dict[str, Any]] = {}

        keys = await self._find_keys(f"{prefix}*{suffix}")
        for key in keys:
            key_text = self._decode_if_bytes(key)
            jockey_id = key_text[len(prefix):-len(suffix)]
            raw = await self._call_redis("get", key_text)
            if raw:
                forms[str(jockey_id)] = json.loads(raw)
        return forms

    async def _find_keys(self, pattern: str) -> list[Any]:
        """Redis 구현체별로 keys 또는 scan_iter를 사용해 키 목록을 찾습니다."""
        if hasattr(self.redis, "scan_iter"):
            result: list[Any] = []
            iterator = self.redis.scan_iter(match=pattern)
            if hasattr(iterator, "__aiter__"):
                async for key in iterator:
                    result.append(key)
            else:
                for key in iterator:
                    result.append(key)
            return result
        return list(await self._call_redis("keys", pattern))

    async def _call_redis(self, method_name: str, *args: Any, **kwargs: Any) -> Any:
        """동기/비동기 Redis 클라이언트 차이를 흡수해 호출합니다."""
        method = getattr(self.redis, method_name)
        result = method(*args, **kwargs)
        if inspect.isawaitable(result):
            return await result
        return result

    def _run_blocking(self, awaitable: Any) -> Any:
        """동기 테스트에서 async 메서드를 실행합니다."""
        if not inspect.isawaitable(awaitable):
            return awaitable
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(awaitable)
        raise RuntimeError("이미 실행 중인 이벤트 루프에서는 async 메서드를 직접 await 해주세요.")

    def _normalize_entry_probabilities(self, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Sequential 보정 후 확률 합이 1이 되도록 다시 정규화합니다."""
        total = sum(max(self._safe_float(entry.get("win_prob")) or 0.0, 0.0001) for entry in entries)
        if total <= 0:
            even_prob = 1.0 / len(entries)
            for entry in entries:
                entry["win_prob"] = even_prob
            return entries

        for entry in entries:
            entry["win_prob"] = max(self._safe_float(entry.get("win_prob")) or 0.0, 0.0001) / total
        return entries

    @staticmethod
    def _extract_finish_order(result_data: dict[str, Any]) -> list[dict[str, Any]]:
        return list(result_data.get("착순") or result_data.get("finish_order") or [])

    @staticmethod
    def _extract_track_condition(result_data: dict[str, Any]) -> Any:
        return result_data.get("track_condition") or result_data.get("트랙상태")

    @staticmethod
    def _normalize_track_condition(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip().upper()
        mapping = {
            "건조": "DRY",
            "良": "DRY",
            "DRY": "DRY",
            "습윤": "WET",
            "稍重": "WET",
            "WET": "WET",
            "다습": "HUMID",
            "重": "HUMID",
            "HUMID": "HUMID",
            "포화": "SATURATED",
            "不良": "SATURATED",
            "SATURATED": "SATURATED",
        }
        return mapping.get(normalized, normalized)

    @staticmethod
    def _track_bias_for_closer(normalized_track: str | None) -> float:
        if normalized_track in {"WET", "HUMID"}:
            return 0.10
        if normalized_track == "DRY":
            return -0.05
        return 0.0

    @staticmethod
    def _build_status_message(completed_races: list[int], track_condition: Any) -> str:
        if not completed_races:
            return "아직 반영된 앞 경주 결과가 없습니다."
        last_race_no = max(completed_races)
        if track_condition:
            return f"{last_race_no}경주 결과 반영 완료 — 현재 트랙 상태 {track_condition}"
        return f"{last_race_no}경주 결과 반영 완료"

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _decode_if_bytes(value: Any) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)

    @staticmethod
    def _race_result_key(rc_date: str, race_no: int) -> str:
        return f"race:today:{rc_date}:{race_no}:result"

    @staticmethod
    def _track_condition_key(rc_date: str) -> str:
        return f"race:today:{rc_date}:track_condition"

    @staticmethod
    def _jockey_form_key(rc_date: str, jockey_id: int) -> str:
        return f"race:today:{rc_date}:{jockey_id}:form"
