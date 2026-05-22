# -*- coding: utf-8 -*-
# =============================================================================
# test_sequential_updater.py - SequentialUpdater 단위 테스트
# =============================================================================

# json = 가짜 Redis에 저장된 문자열 값을 검증할 때 사용합니다.
import json

# pytest = 비동기 테스트와 근사값 검증을 위한 테스트 도구입니다.
import pytest

# SequentialUpdater = 당일 앞 경주 결과를 뒷 경주 예측에 반영하는 Phase 3 서비스입니다.
from app.services.sequential_updater import SequentialUpdater
# MonteCarloService = Sequential 보정값이 Monte Carlo 시작 확률에 주입되는지 확인합니다.
from app.services.monte_carlo import MonteCarloService


class FakeRedis:
    """테스트에서 실제 Redis 서버 없이 값을 저장하기 위한 아주 작은 가짜 Redis입니다."""

    def __init__(self):
        self.storage = {}

    def setex(self, key, ttl, value):
        self.storage[key] = {"ttl": ttl, "value": value}
        return True

    def get(self, key):
        record = self.storage.get(key)
        if record is None:
            return None
        return record["value"]

    def keys(self, pattern):
        # 테스트에서는 race:today:YYYY-MM-DD:*:result/form 형태만 쓰므로 간단한 포함 조건으로 충분합니다.
        prefix, suffix = pattern.split("*")
        return [
            key
            for key in self.storage
            if key.startswith(prefix) and key.endswith(suffix)
        ]


def test_store_race_result_saves_result_track_and_jockey_form():
    """경주 결과 저장 시 착순, 트랙 상태, 기수 폼이 Redis에 함께 저장되어야 합니다."""
    redis = FakeRedis()
    updater = SequentialUpdater(redis=redis)

    updater.store_race_result(
        rc_date="2026-06-07",
        race_no=1,
        result_data={
            "착순": [
                {"horse_id": 1, "position": 1, "jockey_id": 10},
                {"horse_id": 2, "position": 2, "jockey_id": 11},
            ],
            "track_condition": "습윤",
        },
    )

    result_raw = redis.get("race:today:2026-06-07:1:result")
    assert json.loads(result_raw)["track_condition"] == "습윤"
    assert redis.get("race:today:2026-06-07:track_condition") == "습윤"

    jockey_form = json.loads(redis.get("race:today:2026-06-07:10:form"))
    assert jockey_form["today_win"] == 1
    assert jockey_form["today_race"] == 1


def test_get_sequential_adjustments_returns_track_bias():
    """앞 경주가 습윤 트랙이면 추입마 보정값이 양수로 계산되어야 합니다."""
    updater = SequentialUpdater(redis=FakeRedis())
    updater.store_race_result(
        rc_date="2026-06-07",
        race_no=1,
        result_data={
            "착순": [{"horse_id": 1, "position": 1, "jockey_id": 10}],
            "track_condition": "습윤",
        },
    )

    adjustments = updater.get_sequential_adjustments("2026-06-07", target_race_no=2)

    assert adjustments["track_condition"] == "습윤"
    assert adjustments["track_bias"] == pytest.approx(0.10)
    assert adjustments["completed_races"] == [1]
    assert adjustments["sequential_available"] is True


def test_apply_sequential_prior_adjusts_track_and_jockey_form():
    """트랙과 기수 당일 폼에 따라 확률이 보정되고 합계는 다시 1이 되어야 합니다."""
    updater = SequentialUpdater(redis=FakeRedis())
    entries = [
        {"horse_id": 1, "jockey_id": 10, "running_style": "CLOSER", "win_prob": 0.30},
        {"horse_id": 2, "jockey_id": 20, "running_style": "LEADER", "win_prob": 0.30},
    ]
    adjustments = {
        "track_condition": "습윤",
        "jockey_forms": {
            "10": {"today_win": 2, "today_race": 3, "form_factor": 1.2},
            "20": {"today_win": 0, "today_race": 3, "form_factor": 1.0},
        },
    }

    adjusted = updater.apply_sequential_prior(entries, adjustments)

    assert adjusted[0]["win_prob"] > adjusted[1]["win_prob"]
    assert sum(entry["win_prob"] for entry in adjusted) == pytest.approx(1.0)
    assert adjusted[0]["sequential_factor"] > 1.0
    assert adjusted[1]["sequential_factor"] < 1.0


@pytest.mark.asyncio
async def test_monte_carlo_applies_sequential_priors(monkeypatch):
    """use_sequential=True이면 Redis 조정값이 rows의 win_prob로 주입되어야 합니다."""

    class FakeSequentialUpdater:
        """Redis 없이 Sequential 보정 결과를 고정 반환하는 테스트 전용 대역입니다."""

        async def get_sequential_adjustments_async(self, rc_date, target_race_no):
            assert rc_date == "2026-06-07"
            assert target_race_no == 2
            return {
                "sequential_available": True,
                "track_condition": "습윤",
                "jockey_forms": {"10": {"today_win": 2, "today_race": 3}},
            }

        def apply_sequential_prior(self, entries, adjustments):
            copied = [dict(entry) for entry in entries]
            copied[0]["sequential_prior_prob"] = 0.30
            copied[0]["sequential_factor"] = 1.13
            copied[0]["sequential_reasons"] = ["테스트 보정"]
            copied[0]["win_prob"] = 0.60
            copied[1]["sequential_prior_prob"] = 0.30
            copied[1]["sequential_factor"] = 0.97
            copied[1]["sequential_reasons"] = []
            copied[1]["win_prob"] = 0.40
            return copied

    from app.services import monte_carlo

    monkeypatch.setattr(monte_carlo, "SequentialUpdater", FakeSequentialUpdater)

    rows = [
        {
            "horse_id": 1,
            "horse_name": "테스트말1",
            "win_prob": 0.30,
            "rc_date": "2026-06-07",
            "race_no": 2,
        },
        {
            "horse_id": 2,
            "horse_name": "테스트말2",
            "win_prob": 0.30,
            "rc_date": "2026-06-07",
            "race_no": 2,
        },
    ]
    service = MonteCarloService(db=None)

    applied, updated_count = await service._apply_sequential_priors(rows, use_sequential=True)

    assert applied is True
    assert updated_count == 2
    assert rows[0]["sequential_prior_prob"] == 0.30
    assert rows[0]["win_prob"] == 0.60
