# -*- coding: utf-8 -*-
# =============================================================================
# test_bayesian_updater.py - BayesianUpdater 단위 테스트
# =============================================================================

# pytest = 예외와 비동기 테스트를 간단하게 검증하기 위한 테스트 도구입니다.
import pytest

# BayesianUpdater = 최근 성적을 Beta-Binomial 방식으로 반영하는 Phase 3 서비스입니다.
from app.services.bayesian_updater import BayesianUpdater
# MonteCarloService = Bayesian posterior가 Monte Carlo 시작 확률로 주입되는지 확인합니다.
from app.services.monte_carlo import MonteCarloService


def test_update_single_horse_reflects_recent_wins():
    """최근 1위가 많은 말은 prior보다 posterior 승률이 올라가야 합니다."""
    updater = BayesianUpdater(db_session=None, prior_weight=10.0)

    result = updater.update_single_horse(
        horse_id=1,
        prior_prob=0.30,
        recent_results=[(None, 1), (None, 2), (None, 1)],
    )

    assert 0.35 < result < 0.42


def test_update_single_horse_keeps_prior_for_debut_horse():
    """데뷔마처럼 과거 성적이 없으면 ML prior만 사용합니다."""
    updater = BayesianUpdater(db_session=None, prior_weight=10.0)

    result = updater.update_single_horse(
        horse_id=1,
        prior_prob=0.30,
        recent_results=[],
    )

    assert result == pytest.approx(0.30)


@pytest.mark.asyncio
async def test_monte_carlo_applies_bayesian_priors(monkeypatch):
    """use_bayesian=True이면 Bayesian posterior가 rows의 win_prob로 주입되어야 합니다."""

    class FakeBayesianUpdater:
        """DB 없이 posterior 값을 고정 반환하는 테스트 전용 대역입니다."""

        def __init__(self, db_session):
            self.db_session = db_session

        async def update_race_entries(self, race_id, entries_with_priors):
            assert race_id == 7
            assert entries_with_priors == {1: 0.3, 2: 0.2}
            return {1: 0.45, 2: 0.15}

    from app.services import monte_carlo

    monkeypatch.setattr(monte_carlo, "BayesianUpdater", FakeBayesianUpdater)

    rows = [
        {"horse_id": 1, "horse_name": "테스트말1", "win_prob": 0.3},
        {"horse_id": 2, "horse_name": "테스트말2", "win_prob": 0.2},
    ]
    service = MonteCarloService(db=None)

    applied, updated_count = await service._apply_bayesian_priors(7, rows, use_bayesian=True)

    assert applied is True
    assert updated_count == 2
    assert rows[0]["bayesian_prior_prob"] == 0.3
    assert rows[0]["win_prob"] == 0.45
    assert rows[1]["win_prob"] == 0.15
