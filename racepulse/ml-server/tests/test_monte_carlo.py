# -*- coding: utf-8 -*-
# =============================================================================
# test_monte_carlo.py — Monte Carlo 시뮬레이션 단위 테스트
# =============================================================================
# Monte Carlo란?
#   같은 상황을 수만 번 반복 시뮬레이션해서 확률 분포를 계산하는 방법입니다.
#   예: 주사위를 10,000번 던지면 각 눈이 나오는 비율이 ~16.7%에 수렴합니다.
#   RacePulse에서는 ML이 예측한 승률로 10,000번 경주를 시뮬레이션해
#   "이 말이 1위할 확률 34%, 2위할 확률 28%, ..." 를 계산합니다.
#
# 테스트 전략: 수학적 불변량 검증
#   시뮬레이션 횟수나 구현 방식이 달라져도 반드시 성립해야 하는 수학적 법칙을
#   검증합니다. 이 법칙이 깨지면 시뮬레이션 로직에 버그가 있는 것입니다.
#
# 테스트 구성:
#   1. calculate_rank_distribution() — 순수 메서드 (numpy 연산만)
#   2. run_simulation() — DB Mock 사용, 수학적 불변량 검증
#   3. 엣지 케이스 — 말 1마리, 동일 확률 등
# =============================================================================

import pytest
import pytest_asyncio
import numpy as np
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.monte_carlo import MonteCarloService


# =============================================================================
# 테스트용 예측 데이터 팩토리
# =============================================================================

def make_prediction_rows(win_probs: list[float], odds: list[float | None] = None) -> list[dict]:
    """테스트용 예측 행(row) 목록을 만드는 헬퍼 함수.

    Args:
        win_probs: 각 말의 ML 예측 승률 리스트. 합이 1.0일 필요 없음 (내부 정규화됨).
        odds:      각 말의 배당률. None이면 전부 5.0으로 채웁니다.
    """
    if odds is None:
        odds = [5.0] * len(win_probs)

    return [
        {
            "horse_id":   i + 1,
            "horse_name": f"말{i + 1}호",
            "win_prob":   prob,
            "odds_win":   odd,
        }
        for i, (prob, odd) in enumerate(zip(win_probs, odds))
    ]


@pytest.fixture
def service():
    """DB Mock을 주입한 MonteCarloService 픽스처."""
    mock_db = AsyncMock()
    return MonteCarloService(db=mock_db)


# =============================================================================
# 섹션 1: calculate_rank_distribution() — 순수 메서드
# =============================================================================
# numpy 배열을 받아서 퍼센트 딕셔너리를 반환합니다.
# DB 없이 직접 호출 가능합니다.
# =============================================================================

class TestCalculateRankDistribution:

    def test_정확한_퍼센트_계산(self, service):
        # 10,000번 중: 1위 6000번, 2위 3000번, 3위 1000번, 4위 이하 0번
        rank_counts = np.array([6000, 3000, 1000, 0])
        result = service.calculate_rank_distribution(rank_counts, n_simulations=10_000)

        assert result["1"]  == 60.0
        assert result["2"]  == 30.0
        assert result["3"]  == 10.0
        assert result["4+"] == 0.0

    def test_합계가_100_퍼센트(self, service):
        # 어떤 분포여도 합계는 반드시 100%
        rank_counts = np.array([3333, 3333, 3334])
        result = service.calculate_rank_distribution(rank_counts, n_simulations=10_000)

        total = result["1"] + result["2"] + result["3"] + result["4+"]
        assert abs(total - 100.0) < 0.2   # 반올림 오차 허용

    def test_말이_1마리일때(self, service):
        # 말이 1마리면 항상 1위 → 1위 = 100%, 나머지 = 0%
        rank_counts = np.array([10_000])
        result = service.calculate_rank_distribution(rank_counts, n_simulations=10_000)

        assert result["1"]  == 100.0
        assert result["2"]  == 0.0
        assert result["3"]  == 0.0
        assert result["4+"] == 0.0

    def test_반환_키_4개_존재(self, service):
        rank_counts = np.array([5000, 3000, 1500, 500])
        result = service.calculate_rank_distribution(rank_counts, n_simulations=10_000)

        assert set(result.keys()) == {"1", "2", "3", "4+"}

    def test_음수_없음(self, service):
        # 반올림 오차로 인해 "4+" 가 음수가 되면 안 됩니다.
        # 1+2+3이 100.0을 살짝 넘는 경우를 방어합니다.
        rank_counts = np.array([3334, 3333, 3333])
        result = service.calculate_rank_distribution(rank_counts, n_simulations=10_000)

        for key, val in result.items():
            assert val >= 0.0, f"'{key}' 값이 음수: {val}"


# =============================================================================
# 섹션 2: run_simulation() — 수학적 불변량 검증
# =============================================================================
# _load_prediction_rows()와 save_simulation_result()를 Mock으로 대체합니다.
# 시뮬레이션 결과의 수학적 성질만 검증합니다.
# =============================================================================

class TestRunSimulationMath:

    @pytest.fixture
    def service_with_mock(self):
        """_load_prediction_rows와 save_simulation_result를 Mock으로 교체한 서비스."""
        mock_db = AsyncMock()
        svc = MonteCarloService(db=mock_db)
        # save_simulation_result는 DB 저장이므로 아무것도 안 하도록 교체합니다.
        svc.save_simulation_result = AsyncMock(return_value=None)
        return svc

    @pytest.mark.asyncio
    async def test_모든말_1위확률_합이_100퍼센트(self, service_with_mock):
        """핵심 불변량: 경주에서 반드시 누군가 1위를 해야 합니다."""
        rows = make_prediction_rows([0.5, 0.3, 0.2])
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(42)  # 재현성을 위해 시드 고정
        result = await service_with_mock.run_simulation(race_id=1, n_simulations=10_000)

        total_first_place = sum(
            horse["rank_distribution"]["1"] for horse in result["horses"]
        )
        # 반올림 오차 허용 (±1.0%)
        assert abs(total_first_place - 100.0) < 1.0, \
            f"1위 확률 합계 = {total_first_place:.2f}% (100%여야 함)"

    @pytest.mark.asyncio
    async def test_각_말의_순위분포_합이_100퍼센트(self, service_with_mock):
        """각 말별로 1위+2위+3위+4이하 = 100% 이어야 합니다."""
        rows = make_prediction_rows([0.4, 0.35, 0.25])
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(42)
        result = await service_with_mock.run_simulation(race_id=1, n_simulations=10_000)

        for horse in result["horses"]:
            dist = horse["rank_distribution"]
            total = dist["1"] + dist["2"] + dist["3"] + dist["4+"]
            assert abs(total - 100.0) < 0.2, \
                f"{horse['horse_name']} 순위 분포 합 = {total:.2f}%"

    @pytest.mark.asyncio
    async def test_upset_probability_범위(self, service_with_mock):
        """이변 확률은 0 ~ 100 사이여야 합니다."""
        # 배당률 10.0 이상인 말이 있는 경우 (이변 후보)
        rows = make_prediction_rows(
            [0.6, 0.3, 0.1],
            odds=[3.0, 5.0, 15.0]  # 마지막 말이 고배당
        )
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(42)
        result = await service_with_mock.run_simulation(race_id=1, n_simulations=10_000)

        upset_prob = result["upset_probability"]
        assert 0.0 <= upset_prob <= 100.0, f"upset_probability = {upset_prob}"

    @pytest.mark.asyncio
    async def test_expected_rank_범위(self, service_with_mock):
        """예상 순위는 1 ~ 말 수 사이여야 합니다."""
        rows = make_prediction_rows([0.5, 0.3, 0.2])
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(42)
        result = await service_with_mock.run_simulation(race_id=1, n_simulations=10_000)

        n_horses = len(rows)
        for horse in result["horses"]:
            er = horse["expected_rank"]
            assert 1.0 <= er <= n_horses, \
                f"{horse['horse_name']} expected_rank = {er} (1~{n_horses} 범위 벗어남)"

    @pytest.mark.asyncio
    async def test_결과에_모든말_포함(self, service_with_mock):
        """입력한 말 수와 결과 말 수가 일치해야 합니다."""
        rows = make_prediction_rows([0.4, 0.3, 0.2, 0.1])
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        result = await service_with_mock.run_simulation(race_id=1, n_simulations=1_000)

        assert len(result["horses"]) == 4

    @pytest.mark.asyncio
    async def test_결과_필수_키_존재(self, service_with_mock):
        """반환 딕셔너리에 필수 키가 모두 있어야 합니다."""
        rows = make_prediction_rows([0.6, 0.4])
        service_with_mock._load_prediction_rows = AsyncMock(return_value=rows)

        result = await service_with_mock.run_simulation(race_id=1, n_simulations=1_000)

        assert "race_id"           in result
        assert "n_simulations"     in result
        assert "horses"            in result
        assert "upset_probability" in result
        assert "computed_at"       in result


# =============================================================================
# 섹션 3: 엣지 케이스
# =============================================================================

class TestRunSimulationEdgeCases:

    @pytest.fixture
    def service_edge(self):
        svc = MonteCarloService(db=AsyncMock())
        svc.save_simulation_result = AsyncMock(return_value=None)
        return svc

    @pytest.mark.asyncio
    async def test_말_1마리_1위확률_100퍼센트(self, service_edge):
        """말이 1마리뿐이면 무조건 1위입니다."""
        rows = make_prediction_rows([1.0])
        service_edge._load_prediction_rows = AsyncMock(return_value=rows)

        result = await service_edge.run_simulation(race_id=1, n_simulations=1_000)

        horse = result["horses"][0]
        assert horse["rank_distribution"]["1"] == 100.0
        assert horse["expected_rank"] == 1.0

    @pytest.mark.asyncio
    async def test_예측_데이터_없으면_ValueError(self, service_edge):
        """예측 결과가 없으면 ValueError가 발생해야 합니다."""
        service_edge._load_prediction_rows = AsyncMock(return_value=[])

        with pytest.raises(ValueError, match="예측 결과가 없어"):
            await service_edge.run_simulation(race_id=999, n_simulations=1_000)

    @pytest.mark.asyncio
    async def test_동일_시드_동일_결과(self, service_edge):
        """같은 시드로 실행하면 결과가 동일해야 합니다 (재현성)."""
        rows = make_prediction_rows([0.5, 0.3, 0.2])
        service_edge._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(77)
        result_a = await service_edge.run_simulation(race_id=1, n_simulations=1_000)

        service_edge._load_prediction_rows = AsyncMock(return_value=rows)
        np.random.seed(77)
        result_b = await service_edge.run_simulation(race_id=1, n_simulations=1_000)

        for ha, hb in zip(result_a["horses"], result_b["horses"]):
            assert ha["rank_distribution"] == hb["rank_distribution"]

    @pytest.mark.asyncio
    async def test_win_prob_0인_말_처리(self, service_edge):
        """win_prob=0인 말도 처리 가능해야 합니다 (내부에서 0.0001로 보정)."""
        rows = make_prediction_rows([0.9, 0.0])  # 두 번째 말 승률 0
        service_edge._load_prediction_rows = AsyncMock(return_value=rows)

        # 에러 없이 실행되어야 합니다
        result = await service_edge.run_simulation(race_id=1, n_simulations=1_000)
        assert len(result["horses"]) == 2

    @pytest.mark.asyncio
    async def test_높은승률_말이_낮은_expected_rank(self, service_edge):
        """승률이 높을수록 expected_rank(예상 순위)가 낮아야 합니다.
        (1위가 가장 낮은 숫자이므로, 강한 말일수록 expected_rank ≈ 1에 가까움)
        """
        # 말1이 압도적으로 강함
        rows = make_prediction_rows([0.9, 0.07, 0.03])
        service_edge._load_prediction_rows = AsyncMock(return_value=rows)

        np.random.seed(42)
        result = await service_edge.run_simulation(race_id=1, n_simulations=10_000)

        ranks = [h["expected_rank"] for h in result["horses"]]
        # 말1(인덱스 0)의 expected_rank가 가장 낮아야 함
        assert ranks[0] < ranks[1]
        assert ranks[0] < ranks[2]


# =============================================================================
# 섹션 4: 고도화 반환 필드 검증
# =============================================================================
# 프롬프트 21에서 추가된 QMC/적응형 수렴/신뢰도/게이트/스마트 머니 필드는
# API 응답을 보는 프론트엔드가 바로 사용할 값입니다.
# 그래서 정확한 확률값 하나를 고정하기보다 타입과 허용 범위를 먼저 검증합니다.
# =============================================================================

@pytest_asyncio.fixture
async def advanced_result():
    """고도화 필드 테스트에서 함께 쓰는 시뮬레이션 결과입니다."""
    svc = MonteCarloService(db=AsyncMock())
    svc.save_simulation_result = AsyncMock(return_value=None)
    svc._load_prediction_rows = AsyncMock(
        return_value=[
            {
                "horse_id": 1,
                "horse_name": "테스트말1",
                "win_prob": 0.5,
                "odds_win": 3.0,
                "gate_no": 1,
                "weather": "CLEAR",
                "opening_odds": 5.0,
                "final_odds": 4.0,
            },
            {
                "horse_id": 2,
                "horse_name": "테스트말2",
                "win_prob": 0.3,
                "odds_win": 8.0,
                "gate_no": 6,
                "weather": "CLEAR",
                "opening_odds": None,
                "final_odds": None,
            },
            {
                "horse_id": 3,
                "horse_name": "테스트말3",
                "win_prob": 0.2,
                "odds_win": 15.0,
                "gate_no": 12,
                "weather": "CLEAR",
                "opening_odds": None,
                "final_odds": None,
            },
        ]
    )
    return await svc.run_simulation(race_id=1, n_simulations=10_000)


def test_converged_is_bool(advanced_result):
    assert isinstance(advanced_result["converged"], bool)


def test_confidence_score_range(advanced_result):
    assert 0 <= advanced_result["confidence_score"] <= 100


def test_n_simulations_range(advanced_result):
    assert 10_000 <= advanced_result["n_simulations"] <= 100_000


def test_smart_money_detected_is_list(advanced_result):
    assert isinstance(advanced_result["smart_money_detected"], list)


def test_gate_bias_applied_is_bool(advanced_result):
    assert isinstance(advanced_result["gate_bias_applied"], bool)
