# -*- coding: utf-8 -*-
# =============================================================================
# test_copula_monte_carlo.py - Copula 상관행렬 단위 테스트
# =============================================================================

# numpy = 상관행렬의 대각선, 대칭성, Cholesky 가능 여부를 확인하는 수치 계산 도구입니다.
import numpy as np
# pytest = 비동기 테스트를 실행하기 위한 테스트 도구입니다.
import pytest
# AsyncMock = DB 저장처럼 테스트 대상이 아닌 비동기 동작을 가짜로 대체할 때 사용합니다.
from unittest.mock import AsyncMock

# build_horse_correlation_matrix = 말-말 상관관계를 만드는 Copula 빌더입니다.
from app.services.monte_carlo import MonteCarloService, build_horse_correlation_matrix


class FakeEntry:
    """프롬프트 완료 기준과 같은 형태의 테스트용 출전마 객체입니다."""

    def __init__(self, horse_id, trainer_id, father_horse_id, meet_code):
        self.horse_id = horse_id
        self.trainer_id = trainer_id
        self.father_horse_id = father_horse_id
        self.meet_code = meet_code


def test_build_horse_correlation_matrix_reflects_trainer_bloodline_and_meet():
    """같은 조교사·부마·경마장인 말 쌍은 상관계수가 높아야 합니다."""
    entries = [
        FakeEntry(1, 100, 10, "KSB"),
        FakeEntry(2, 100, 10, "KSB"),
        FakeEntry(3, 200, 20, "GJA"),
    ]

    matrix = build_horse_correlation_matrix(entries, db_session=None)

    assert matrix[0, 1] >= 0.20
    assert matrix[0, 2] <= 0.10
    assert np.allclose(matrix, matrix.T)
    assert np.allclose(np.diag(matrix), np.ones(3))
    np.linalg.cholesky(matrix)


def test_build_horse_correlation_matrix_uses_rival_correlation():
    """직접 대결 상관값이 있으면 기본 상관행렬에 더해져야 합니다."""
    entries = [
        FakeEntry(1, 100, 10, "KSB"),
        FakeEntry(2, 200, 20, "GJA"),
    ]

    matrix = build_horse_correlation_matrix(
        entries,
        db_session=None,
        rival_correlations={(1, 2): 0.08},
    )

    assert matrix[0, 1] == pytest.approx(0.08)
    assert matrix[1, 0] == pytest.approx(0.08)


@pytest.mark.asyncio
async def test_monte_carlo_returns_copula_fields():
    """use_copula=True이면 결과에 Copula 적용 여부와 sigma가 포함되어야 합니다."""
    service = MonteCarloService(db=AsyncMock())
    service.save_simulation_result = AsyncMock(return_value=None)
    service._load_rival_correlations = AsyncMock(return_value={(1, 2): 0.05})
    service._load_prediction_rows = AsyncMock(
        return_value=[
            {
                "horse_id": 1,
                "horse_name": "테스트말1",
                "win_prob": 0.55,
                "odds_win": 3.0,
                "gate_no": 1,
                "weather": "CLEAR",
                "trainer_id": 100,
                "father_name": "부마A",
                "meet_code": "SC",
            },
            {
                "horse_id": 2,
                "horse_name": "테스트말2",
                "win_prob": 0.45,
                "odds_win": 4.0,
                "gate_no": 2,
                "weather": "CLEAR",
                "trainer_id": 100,
                "father_name": "부마A",
                "meet_code": "SC",
            },
        ]
    )

    result = await service.run_simulation(race_id=1, n_simulations=1_000, use_copula=True)

    assert result["copula_applied"] is True
    assert result["copula_sigma"] > 0
    assert len(result["horses"]) == 2
