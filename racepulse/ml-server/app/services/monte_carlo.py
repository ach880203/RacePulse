# -*- coding: utf-8 -*-
# =============================================================================
# monte_carlo.py - 예측 확률을 여러 번 다시 뽑아 순위 분포를 계산하는 서비스
# =============================================================================

# asyncio = FastAPI의 비동기 흐름 안에서 CPU 작업을 별도 실행자에게 맡길 때 쓰는 기본 도구입니다.
import asyncio
# ProcessPoolExecutor = 여러 작업자가 동시에 계산하게 만드는 도구입니다. 큰 시뮬레이션에서만 사용합니다.
from concurrent.futures import ProcessPoolExecutor
# dataclass = 시뮬레이션에 필요한 값을 이름 있는 묶음으로 전달해 실수를 줄이는 도구입니다.
from dataclasses import dataclass
# datetime/timezone = 결과가 언제 계산되었는지 UTC 기준 시각으로 남기기 위한 기본 도구입니다.
from datetime import datetime, timezone
# math = 배치 수, 신뢰구간 같은 작은 수학 계산에 쓰는 기본 도구입니다.
import math
# typing.Any = DB에서 온 값처럼 정확한 타입이 실행 시점에 정해지는 값을 설명할 때 사용합니다.
from typing import Any

# numpy = 많은 난수를 한 번에 계산해 Python 반복문보다 빠르게 시뮬레이션하기 위한 수치 계산 라이브러리입니다.
import numpy as np
# sqlalchemy.text = 직접 작성한 SQL 문자열을 SQLAlchemy 비동기 세션에서 실행하게 해주는 도구입니다.
# bindparam = IN (...) 조건에 파이썬 리스트를 안전하게 펼쳐 넣을 때 사용합니다.
from sqlalchemy import bindparam, text
# AsyncSession = FastAPI 서비스에서 DB를 비동기로 조회/저장하기 위한 SQLAlchemy 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# BayesianUpdater = 최근 경주 결과를 Beta-Binomial 방식으로 반영해 ML 승률 prior를 보정하는 Phase 3 서비스입니다.
from app.services.bayesian_updater import BayesianUpdater
# SequentialUpdater = 당일 앞 경주 결과를 Redis에서 읽어 뒷 경주 예측 확률을 미세 보정하는 Phase 3 서비스입니다.
from app.services.sequential_updater import SequentialUpdater

try:
    # qmc = Sobol 같은 고르게 퍼지는 난수열을 만들기 위한 scipy 도구입니다.
    # norm = 균등분포 난수를 정규분포 난수로 바꾸어 날씨/상관 노이즈를 만들 때 사용합니다.
    from scipy.stats import norm, qmc

    USE_QMC = True
except ImportError:
    # scipy가 없는 환경에서도 API가 죽지 않도록 numpy 난수로 자동 대체합니다.
    norm = None
    qmc = None
    USE_QMC = False


MIN_SIMULATIONS = 10_000
MAX_SIMULATIONS = 100_000
BATCH_SIZE = 1_000
CI_THRESHOLD = 0.01
MAX_WORKERS = 4
PARALLEL_SIMULATION_THRESHOLD = 30_000

DEFAULT_GATE_BIAS = {
    (1, 4): 0.03,
    (5, 8): 0.00,
    (9, 12): -0.02,
    (13, 99): -0.04,
}

WEATHER_SIGMA = {
    "CLEAR": 0.02,
    "CLOUDY": 0.03,
    "RAIN": 0.05,
    "HEAVY_RAIN": 0.05,
    None: 0.02,
}

COPULA_SIGMA = 0.03


@dataclass(frozen=True)
class SimulationContext:
    """작업자에게 넘길 값 묶음입니다. 딕셔너리보다 필드명이 고정되어 실수를 줄입니다."""

    probabilities: list[float]
    gate_numbers: list[int]
    odds_win: list[float | None]
    weather_sigma: float
    smart_money_indexes: list[int]
    horse_correlation_matrix: list[list[float]] | None
    copula_sigma: float
    n_simulations: int
    seed: int
    use_qmc: bool


def _normalize_probabilities(probabilities: np.ndarray) -> np.ndarray:
    """확률 합이 1이 되도록 보정합니다. 모든 값이 0이어도 균등 확률로 안전하게 복구합니다."""
    clipped = np.clip(probabilities.astype(float), 0.0001, None)
    total = float(clipped.sum())
    if total <= 0:
        return np.full(len(clipped), 1.0 / len(clipped), dtype=float)
    return clipped / total


def _gate_bias_for(gate_no: int) -> float:
    """게이트 번호가 안쪽/바깥쪽인지에 따라 기본 출발 이점을 반환합니다."""
    for (start, end), bias in DEFAULT_GATE_BIAS.items():
        if start <= gate_no <= end:
            return bias
    return 0.0


def _build_gate_correlation(gate_numbers: list[int]) -> np.ndarray:
    """가까운 게이트끼리 비슷한 흐름을 타도록 가우시안 상관 행렬을 만듭니다."""
    gates = np.array(gate_numbers, dtype=float)
    distance = gates[:, None] - gates[None, :]
    correlation = 0.3 * np.exp(-0.5 * (distance / 3.0) ** 2)
    np.fill_diagonal(correlation, 1.0)
    return correlation


def build_horse_correlation_matrix(
    entries: list[Any],
    db_session: Any | None = None,
    rival_correlations: dict[tuple[int, int], float] | None = None,
) -> np.ndarray:
    """말들 간의 Copula 상관계수 행렬을 만듭니다.

    Copula는 각 말의 예측 확률이라는 "악보"는 유지하면서,
    말들끼리 함께 움직이는 "하모니"를 추가하는 도구입니다.
    예를 들어 같은 조교사 밑의 말들은 훈련 환경, 마방 컨디션, 관리 리듬이 비슷해
    같이 좋은 날 또는 같이 나쁜 날이 생길 수 있습니다.
    """
    horse_count = len(entries)
    correlation_matrix = np.eye(horse_count, dtype=float)
    rival_correlations = rival_correlations or {}

    for left_index, left_entry in enumerate(entries):
        for right_index, right_entry in enumerate(entries):
            if left_index >= right_index:
                # 상관행렬은 대칭입니다.
                # A와 B의 상관이 0.2라면 B와 A의 상관도 똑같이 0.2이므로 한쪽만 계산합니다.
                continue

            rho = 0.0

            left_trainer_id = _entry_value(left_entry, "trainer_id")
            right_trainer_id = _entry_value(right_entry, "trainer_id")
            if left_trainer_id is not None and left_trainer_id == right_trainer_id:
                rho += 0.15

            left_father = _entry_value(left_entry, "father_horse_id") or _entry_value(left_entry, "sire_id") or _entry_value(left_entry, "father_name")
            right_father = _entry_value(right_entry, "father_horse_id") or _entry_value(right_entry, "sire_id") or _entry_value(right_entry, "father_name")
            if left_father is not None and left_father == right_father:
                rho += 0.10

            left_meet_code = _entry_value(left_entry, "meet_code")
            right_meet_code = _entry_value(right_entry, "meet_code")
            if left_meet_code is not None and left_meet_code == right_meet_code:
                rho += 0.05

            left_horse_id = int(_entry_value(left_entry, "horse_id"))
            right_horse_id = int(_entry_value(right_entry, "horse_id"))
            pair_key = _ordered_horse_pair(left_horse_id, right_horse_id)
            rho += rival_correlations.get(pair_key, _get_rival_correlation(left_horse_id, right_horse_id, db_session))

            correlation_matrix[left_index, right_index] = min(max(rho, 0.0), 0.8)
            correlation_matrix[right_index, left_index] = correlation_matrix[left_index, right_index]

    return _make_positive_definite(correlation_matrix)


def _get_rival_correlation(horse_id_1: int, horse_id_2: int, db_session: Any | None) -> float:
    """rival_records 직접 대결 기록을 상관계수로 변환합니다.

    평균 순위 차이가 작으면 두 말의 실력이 비슷하다고 보고 상관을 높입니다.
    다만 대결 횟수가 3회 미만이면 우연일 수 있으므로 보정하지 않습니다.
    """
    if db_session is None:
        return 0.0

    try:
        h1, h2 = _ordered_horse_pair(horse_id_1, horse_id_2)
        record = db_session.execute(
            text(
                """
                SELECT total_races, horse1_avg_position, horse2_avg_position
                FROM rival_records
                WHERE horse_id_1 = :h1 AND horse_id_2 = :h2
                ORDER BY total_races DESC, updated_at DESC NULLS LAST
                LIMIT 1
                """
            ),
            {"h1": h1, "h2": h2},
        ).fetchone()
    except Exception:
        return 0.0

    if not record or int(record.total_races or 0) < 3:
        return 0.0

    pos_diff = abs(float(record.horse1_avg_position or 5.0) - float(record.horse2_avg_position or 5.0))
    base_rho = max(0.0, 0.10 - pos_diff * 0.02)
    confidence = min(float(record.total_races or 0) / 10.0, 1.0)
    return base_rho * confidence


def _entry_value(entry: Any, key: str) -> Any:
    """dict와 객체를 같은 방식으로 읽기 위한 작은 도우미입니다."""
    if isinstance(entry, dict):
        return entry.get(key)
    return getattr(entry, key, None)


def _ordered_horse_pair(horse_id_1: int, horse_id_2: int) -> tuple[int, int]:
    """rival_records 테이블 제약조건에 맞춰 작은 horse_id가 먼저 오게 합니다."""
    return (horse_id_1, horse_id_2) if horse_id_1 < horse_id_2 else (horse_id_2, horse_id_1)


def _make_positive_definite(correlation_matrix: np.ndarray) -> np.ndarray:
    """Cholesky 분해가 가능하도록 수치적으로 안전한 양정치 행렬로 보정합니다."""
    safe_matrix = np.array(correlation_matrix, dtype=float)
    safe_matrix = (safe_matrix + safe_matrix.T) / 2.0
    np.fill_diagonal(safe_matrix, 1.0)

    # Cholesky 분해는 상관행렬을 난수에 입힐 수 있는 삼각행렬로 나누는 도구입니다.
    # 상관이 너무 강하거나 반올림 오차가 있으면 np.linalg.LinAlgError가 날 수 있어 작은 값을 대각선에 더합니다.
    jitter = 1e-8
    for _ in range(6):
        try:
            np.linalg.cholesky(safe_matrix)
            return safe_matrix
        except np.linalg.LinAlgError:
            safe_matrix = safe_matrix + np.eye(len(safe_matrix)) * jitter
            jitter *= 10
    return np.eye(len(correlation_matrix), dtype=float)


def _generate_uniform_samples(row_count: int, horse_count: int, seed: int, use_qmc: bool) -> np.ndarray:
    """Sobol QMC를 우선 사용하고, 불가능하면 numpy 난수로 균등분포 표본을 만듭니다."""
    if use_qmc and USE_QMC and qmc is not None:
        sampler = qmc.Sobol(d=horse_count, scramble=True, seed=seed)
        power = math.ceil(math.log2(max(row_count, 1)))
        samples = sampler.random_base2(power)
        return samples[:row_count]

    rng = np.random.default_rng(seed)
    return rng.random((row_count, horse_count))


def _simulate_chunk(context: SimulationContext) -> tuple[np.ndarray, int]:
    """동기 작업자 함수입니다. 비동기 DB 코드와 분리해야 프로세스 작업자가 실행할 수 있습니다."""
    probabilities = _normalize_probabilities(np.array(context.probabilities, dtype=float))
    horse_count = len(probabilities)
    rank_counts = np.zeros((horse_count, horse_count), dtype=np.int64)
    if horse_count == 1:
        rank_counts[0, 0] = context.n_simulations
        odds = context.odds_win[0]
        upset_wins = context.n_simulations if odds is not None and odds >= 10.0 else 0
        return rank_counts, upset_wins

    high_odds_indexes = {
        index
        for index, odds in enumerate(context.odds_win)
        if odds is not None and float(odds) >= 10.0
    }
    gate_biases = np.array([_gate_bias_for(gate_no) for gate_no in context.gate_numbers], dtype=float)
    smart_money_indexes = np.array(context.smart_money_indexes, dtype=int)
    horse_correlation_matrix = (
        np.array(context.horse_correlation_matrix, dtype=float)
        if context.horse_correlation_matrix is not None
        else None
    )

    for batch_start in range(0, context.n_simulations, BATCH_SIZE):
        batch_size = min(BATCH_SIZE, context.n_simulations - batch_start)
        seed = context.seed + batch_start
        uniforms = _generate_uniform_samples(batch_size, horse_count, seed, context.use_qmc)
        antithetic_uniforms = 1.0 - uniforms
        merged_uniforms = np.vstack([uniforms, antithetic_uniforms])[:batch_size]

        adjusted = np.tile(probabilities, (batch_size, 1))
        adjusted = adjusted * (1.0 + gate_biases)

        if smart_money_indexes.size > 0:
            adjusted[:, smart_money_indexes] *= 1.10

        if norm is not None and (context.weather_sigma > 0 or horse_correlation_matrix is not None):
            normal_noise = norm.ppf(np.clip(merged_uniforms, 0.000001, 0.999999))
            try:
                cholesky_matrix = np.linalg.cholesky(_build_gate_correlation(context.gate_numbers))
                correlated_noise = normal_noise @ cholesky_matrix.T
            except np.linalg.LinAlgError:
                # 상관 행렬이 수치적으로 불안정하면 독립 노이즈로 내려갑니다.
                correlated_noise = normal_noise
            adjusted = adjusted + (correlated_noise * context.weather_sigma)

            if horse_correlation_matrix is not None and context.copula_sigma > 0:
                try:
                    # norm.cdf(X)는 정규분포 누적분포함수입니다.
                    # 누적확률은 항상 0~1 사이이므로 "상관이 반영된 확률 흔들림"으로 쓰기 좋습니다.
                    horse_cholesky = np.linalg.cholesky(_make_positive_definite(horse_correlation_matrix))
                    copula_normal = normal_noise @ horse_cholesky.T
                    copula_uniform = norm.cdf(copula_normal)
                    copula_noise = copula_uniform - 0.5
                    adjusted = adjusted + (copula_noise * context.copula_sigma)
                except np.linalg.LinAlgError:
                    # 수치적으로 불안정하면 Copula만 건너뛰고 기존 게이트/날씨 시뮬레이션은 유지합니다.
                    pass

        adjusted = np.clip(adjusted, 0.0001, None)
        adjusted = adjusted / adjusted.sum(axis=1, keepdims=True)

        draw_uniforms = np.clip(_generate_uniform_samples(batch_size, horse_count, seed + 17, False), 0.000001, 0.999999)
        race_keys = -np.log(draw_uniforms) / adjusted
        sampled_orders = np.argsort(race_keys, axis=1)

        for rank_index in range(horse_count):
            winners_at_rank = sampled_orders[:, rank_index]
            rank_counts[:, rank_index] += np.bincount(winners_at_rank, minlength=horse_count)

    upset_wins = int(sum(rank_counts[index, 0] for index in high_odds_indexes))
    return rank_counts, upset_wins


class MonteCarloService:
    """ML 예측값을 반복 추첨해 각 말의 순위별 가능성을 계산합니다."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_simulation(
        self,
        race_id: int,
        n_simulations: int = 10_000,
        use_bayesian: bool = False,
        use_sequential: bool = False,
        use_copula: bool = False,
    ) -> dict[str, Any]:
        rows = await self._load_prediction_rows(race_id)
        if not rows:
            raise ValueError("예측 결과가 없어 시뮬레이션을 실행할 수 없습니다.")

        requested_simulations = max(int(n_simulations or MIN_SIMULATIONS), MIN_SIMULATIONS)
        target_simulations = min(requested_simulations, MAX_SIMULATIONS)
        bayesian_applied, bayesian_updated_count = await self._apply_bayesian_priors(race_id, rows, use_bayesian)
        sequential_applied, sequential_updated_count = await self._apply_sequential_priors(rows, use_sequential)
        probabilities = self._build_adjusted_probabilities(rows)
        gate_numbers = self._build_gate_numbers(rows)
        odds_win = [self._safe_float(row.get("odds_win")) for row in rows]
        weather_sigma = self._weather_sigma(rows[0].get("weather"))
        smart_money_indexes = self._detect_smart_money_indexes(rows)
        copula_matrix = await self._build_copula_matrix(rows, use_copula)
        copula_applied = copula_matrix is not None

        rank_counts = np.zeros((len(rows), len(rows)), dtype=np.int64)
        upset_wins = 0
        completed_simulations = 0
        converged = False

        seed_base = int(np.random.randint(0, 2**31 - 1))
        while completed_simulations < target_simulations:
            remaining = target_simulations - completed_simulations
            if target_simulations >= PARALLEL_SIMULATION_THRESHOLD:
                batch_target = min(PARALLEL_SIMULATION_THRESHOLD, remaining)
            else:
                batch_target = min(BATCH_SIZE * MAX_WORKERS, remaining)
            batch_counts, batch_upsets = await self._run_simulation_batch(
                probabilities=probabilities,
                gate_numbers=gate_numbers,
                odds_win=odds_win,
                weather_sigma=weather_sigma,
                smart_money_indexes=smart_money_indexes,
                horse_correlation_matrix=copula_matrix,
                n_simulations=batch_target,
                seed=seed_base + completed_simulations,
            )
            rank_counts += batch_counts
            upset_wins += batch_upsets
            completed_simulations += batch_target

            if completed_simulations >= MIN_SIMULATIONS:
                converged = self._has_converged(rank_counts[:, 0], completed_simulations)
                if converged:
                    break

        horses = []
        for index, row in enumerate(rows):
            rank_distribution = self.calculate_rank_distribution(rank_counts[index], completed_simulations)
            expected_rank = sum((rank + 1) * count for rank, count in enumerate(rank_counts[index])) / completed_simulations
            horses.append(
                {
                    "horse_id": row["horse_id"],
                    "horse_name": row["horse_name"],
                    "rank_distribution": rank_distribution,
                    "expected_rank": round(expected_rank, 2),
                }
            )

        result = {
            "race_id": race_id,
            "n_simulations": completed_simulations,
            "horses": horses,
            "upset_probability": round((upset_wins / completed_simulations) * 100, 1),
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "converged": converged,
            "confidence_score": self._calculate_confidence_score(
                converged=converged,
                n_simulations=completed_simulations,
                gate_bias_applied=True,
                weather_exists=rows[0].get("weather") is not None,
                smart_money_exists=any(row.get("opening") is not None for row in rows),
            ),
            "gate_bias_applied": True,
            "weather_uncertainty_sigma": weather_sigma,
            "smart_money_detected": [rows[index]["horse_id"] for index in smart_money_indexes],
            "bayesian_applied": bayesian_applied,
            "bayesian_updated_count": bayesian_updated_count,
            "sequential_applied": sequential_applied,
            "sequential_updated_count": sequential_updated_count,
            "copula_applied": copula_applied,
            "copula_sigma": COPULA_SIGMA if copula_applied else 0.0,
        }
        await self.save_simulation_result(race_id, result)
        return result

    async def _run_simulation_batch(
        self,
        probabilities: np.ndarray,
        gate_numbers: list[int],
        odds_win: list[float | None],
        weather_sigma: float,
        smart_money_indexes: list[int],
        horse_correlation_matrix: np.ndarray | None,
        n_simulations: int,
        seed: int,
    ) -> tuple[np.ndarray, int]:
        """작은 배치는 현재 프로세스에서, 큰 배치는 여러 프로세스에서 나누어 계산합니다."""
        if n_simulations < PARALLEL_SIMULATION_THRESHOLD or len(probabilities) <= 1:
            context = SimulationContext(
                probabilities=probabilities.tolist(),
                gate_numbers=gate_numbers,
                odds_win=odds_win,
                weather_sigma=weather_sigma,
                smart_money_indexes=smart_money_indexes,
                horse_correlation_matrix=horse_correlation_matrix.tolist() if horse_correlation_matrix is not None else None,
                copula_sigma=COPULA_SIGMA if horse_correlation_matrix is not None else 0.0,
                n_simulations=n_simulations,
                seed=seed,
                use_qmc=USE_QMC,
            )
            return _simulate_chunk(context)

        chunk_size = math.ceil(n_simulations / MAX_WORKERS)
        chunks = []
        for worker_index in range(MAX_WORKERS):
            start = worker_index * chunk_size
            chunk_n = min(chunk_size, n_simulations - start)
            if chunk_n <= 0:
                continue
            chunks.append(
                SimulationContext(
                    probabilities=probabilities.tolist(),
                    gate_numbers=gate_numbers,
                    odds_win=odds_win,
                    weather_sigma=weather_sigma,
                    smart_money_indexes=smart_money_indexes,
                    horse_correlation_matrix=horse_correlation_matrix.tolist() if horse_correlation_matrix is not None else None,
                    copula_sigma=COPULA_SIGMA if horse_correlation_matrix is not None else 0.0,
                    n_simulations=chunk_n,
                    seed=seed + start,
                    use_qmc=USE_QMC,
                )
            )

        loop = asyncio.get_running_loop()
        with ProcessPoolExecutor(max_workers=min(MAX_WORKERS, len(chunks))) as executor:
            partial_results = await asyncio.gather(
                *[loop.run_in_executor(executor, _simulate_chunk, chunk) for chunk in chunks]
            )

        rank_counts = np.zeros((len(probabilities), len(probabilities)), dtype=np.int64)
        upset_wins = 0
        for partial_counts, partial_upsets in partial_results:
            rank_counts += partial_counts
            upset_wins += partial_upsets
        return rank_counts, upset_wins

    def calculate_rank_distribution(self, rank_counts: np.ndarray, n_simulations: int) -> dict[str, float]:
        first = round((rank_counts[0] / n_simulations) * 100, 1)
        second = round((rank_counts[1] / n_simulations) * 100, 1) if len(rank_counts) > 1 else 0.0
        third = round((rank_counts[2] / n_simulations) * 100, 1) if len(rank_counts) > 2 else 0.0
        fourth_or_lower = max(round(100.0 - first - second - third, 1), 0.0)
        return {"1": first, "2": second, "3": third, "4+": fourth_or_lower}

    async def calculate_upset_probability(self, race_id: int) -> float:
        result = await self.get_simulation_result(race_id)
        if not result:
            result = await self.run_simulation(race_id)
        return float(result["upset_probability"])

    async def save_simulation_result(self, race_id: int, result: dict[str, Any]) -> None:
        await self._ensure_table()
        await self.db.execute(
            text(
                """
                INSERT INTO monte_carlo_simulations (race_id, n_simulations, result_json, computed_at)
                VALUES (:race_id, :n_simulations, CAST(:result_json AS jsonb), now())
                ON CONFLICT (race_id)
                DO UPDATE SET
                    n_simulations = EXCLUDED.n_simulations,
                    result_json = EXCLUDED.result_json,
                    computed_at = now()
                """
            ),
            {
                "race_id": race_id,
                "n_simulations": result["n_simulations"],
                "result_json": self._json_dumps(result),
            },
        )
        await self.db.commit()

    async def get_simulation_result(self, race_id: int) -> dict[str, Any] | None:
        await self._ensure_table()
        row = (
            await self.db.execute(
                text(
                    """
                    SELECT result_json
                    FROM monte_carlo_simulations
                    WHERE race_id = :race_id
                    """
                ),
                {"race_id": race_id},
            )
        ).mappings().first()
        return dict(row["result_json"]) if row else None

    async def _load_prediction_rows(self, race_id: int) -> list[dict[str, Any]]:
        odds_history_exists = await self._table_exists("odds_history")
        running_style_exists = await self._table_exists("horse_running_style")
        # DB 컬럼명: opening, final (V9 마이그레이션 기준)
        odds_select = "oh.opening, oh.final" if odds_history_exists else "NULL AS opening, NULL AS final"
        odds_join = (
            """
            LEFT JOIN LATERAL (
                SELECT opening, final
                FROM odds_history
                WHERE odds_history.race_entry_id = e.id
                ORDER BY recorded_at DESC NULLS LAST, id DESC
                LIMIT 1
            ) oh ON true
            """
            if odds_history_exists
            else ""
        )
        running_style_select = "hrs.style AS running_style" if running_style_exists else "NULL AS running_style"
        running_style_join = (
            """
            LEFT JOIN LATERAL (
                SELECT style
                FROM horse_running_style
                WHERE horse_running_style.horse_id = h.id
                ORDER BY updated_at DESC NULLS LAST, id DESC
                LIMIT 1
            ) hrs ON true
            """
            if running_style_exists
            else ""
        )

        result = await self.db.execute(
            text(
                f"""
                SELECT
                    p.win_prob,
                    h.id AS horse_id,
                    h.name AS horse_name,
                    h.father_name,
                    h.meet_code,
                    e.jockey_id,
                    e.trainer_id,
                    e.odds_win,
                    e.gate_no,
                    r.weather,
                    r.rc_date,
                    r.race_no,
                    {running_style_select},
                    {odds_select}
                FROM predictions p
                JOIN race_entries e ON e.id = p.race_entry_id
                JOIN horses h ON h.id = e.horse_id
                JOIN races r ON r.id = p.race_id
                {running_style_join}
                {odds_join}
                WHERE p.race_id = :race_id
                ORDER BY p.predicted_rank ASC NULLS LAST, p.win_prob DESC NULLS LAST
                """
            ),
            {"race_id": race_id},
        )
        return [dict(row) for row in result.mappings().all()]

    async def _ensure_table(self) -> None:
        await self.db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS monte_carlo_simulations (
                    id bigint generated by default as identity primary key,
                    race_id bigint not null unique references races(id) on delete cascade,
                    n_simulations integer not null,
                    result_json jsonb not null,
                    computed_at timestamp not null default current_timestamp
                )
                """
            )
        )
        await self.db.commit()

    async def _table_exists(self, table_name: str) -> bool:
        row = (
            await self.db.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL AS exists"),
                {"table_name": table_name},
            )
        ).mappings().first()
        return bool(row and row["exists"])

    def _build_adjusted_probabilities(self, rows: list[dict[str, Any]]) -> np.ndarray:
        probabilities = np.array([max(self._safe_float(row.get("win_prob")) or 0.0, 0.0001) for row in rows], dtype=float)
        gate_numbers = self._build_gate_numbers(rows)
        for index, gate_no in enumerate(gate_numbers):
            probabilities[index] *= 1.0 + _gate_bias_for(gate_no)

        for index in self._detect_smart_money_indexes(rows):
            probabilities[index] *= 1.10

        return _normalize_probabilities(probabilities)

    async def _apply_bayesian_priors(
        self,
        race_id: int,
        rows: list[dict[str, Any]],
        use_bayesian: bool,
    ) -> tuple[bool, int]:
        """Bayesian 옵션이 켜져 있으면 최근 결과를 반영한 posterior 승률을 rows에 주입합니다."""
        if not use_bayesian:
            return False, 0

        entries_with_priors = {
            int(row["horse_id"]): max(self._safe_float(row.get("win_prob")) or 0.0, 0.0001)
            for row in rows
        }
        if not entries_with_priors:
            return False, 0

        updater = BayesianUpdater(self.db)
        bayesian_priors = await updater.update_race_entries(race_id, entries_with_priors)
        updated_count = 0

        for row in rows:
            horse_id = int(row["horse_id"])
            posterior_prob = bayesian_priors.get(horse_id)
            if posterior_prob is None:
                continue

            # posterior = prior와 최근 경기 결과를 함께 본 뒤의 보정 승률입니다.
            # 이후 Phase 2의 QMC/Adaptive MC는 이 값을 시작 확률로 사용합니다.
            row["bayesian_prior_prob"] = row.get("win_prob")
            row["win_prob"] = posterior_prob
            updated_count += 1

        return updated_count > 0, updated_count

    async def _apply_sequential_priors(
        self,
        rows: list[dict[str, Any]],
        use_sequential: bool,
    ) -> tuple[bool, int]:
        """Sequential 옵션이 켜져 있으면 당일 앞 경주 결과를 반영해 rows의 win_prob를 보정합니다."""
        if not use_sequential or not rows:
            return False, 0

        rc_date = rows[0].get("rc_date")
        race_no = rows[0].get("race_no")
        if rc_date is None or race_no is None:
            return False, 0

        updater = SequentialUpdater()
        adjustments = await updater.get_sequential_adjustments_async(str(rc_date), int(race_no))
        if not adjustments.get("sequential_available"):
            return False, 0

        adjusted_rows = updater.apply_sequential_prior(rows, adjustments)
        updated_count = 0

        for row, adjusted_row in zip(rows, adjusted_rows):
            # Sequential prior = Bayesian까지 반영된 확률에 오늘 트랙/기수 흐름을 한 번 더 보정한 값입니다.
            # Redis 데이터는 자정에 사라지므로 다음 경주일 예측에는 영향을 주지 않습니다.
            row["sequential_prior_prob"] = adjusted_row.get("sequential_prior_prob")
            row["sequential_factor"] = adjusted_row.get("sequential_factor")
            row["sequential_reasons"] = adjusted_row.get("sequential_reasons", [])
            row["win_prob"] = adjusted_row["win_prob"]
            updated_count += 1

        return updated_count > 0, updated_count

    async def _build_copula_matrix(
        self,
        rows: list[dict[str, Any]],
        use_copula: bool,
    ) -> np.ndarray | None:
        """Copula 옵션이 켜져 있으면 말-말 상관행렬을 준비합니다."""
        if not use_copula or len(rows) <= 1 or norm is None:
            return None

        rival_correlations = await self._load_rival_correlations(rows)
        matrix = build_horse_correlation_matrix(rows, rival_correlations=rival_correlations)
        if len(matrix) <= 1:
            return None
        return matrix

    async def _load_rival_correlations(self, rows: list[dict[str, Any]]) -> dict[tuple[int, int], float]:
        """rival_records에서 이번 경주 출전마끼리의 직접 대결 상관값을 한 번에 가져옵니다."""
        if not await self._table_exists("rival_records"):
            return {}

        horse_ids = [int(row["horse_id"]) for row in rows]
        if len(horse_ids) <= 1:
            return {}

        result = await self.db.execute(
            text(
                """
                SELECT horse_id_1, horse_id_2, total_races, horse1_avg_position, horse2_avg_position
                FROM rival_records
                WHERE horse_id_1 IN :horse_ids
                  AND horse_id_2 IN :horse_ids
                """
            ).bindparams(bindparam("horse_ids", expanding=True)),
            {"horse_ids": horse_ids},
        )

        correlations: dict[tuple[int, int], float] = {}
        for row in result.mappings().all():
            total_races = int(row["total_races"] or 0)
            if total_races < 3:
                continue
            pos_diff = abs(float(row["horse1_avg_position"] or 5.0) - float(row["horse2_avg_position"] or 5.0))
            base_rho = max(0.0, 0.10 - pos_diff * 0.02)
            confidence = min(total_races / 10.0, 1.0)
            correlations[_ordered_horse_pair(int(row["horse_id_1"]), int(row["horse_id_2"]))] = base_rho * confidence

        return correlations

    def _build_gate_numbers(self, rows: list[dict[str, Any]]) -> list[int]:
        """게이트 번호가 비어 있으면 1번부터 차례대로 넣어 상관 계산이 멈추지 않게 합니다."""
        return [int(row.get("gate_no") or index + 1) for index, row in enumerate(rows)]

    def _detect_smart_money_indexes(self, rows: list[dict[str, Any]]) -> list[int]:
        """초기 배당보다 최종 배당이 15% 이상 내려간 말을 스마트 머니 대상으로 봅니다."""
        detected = []
        for index, row in enumerate(rows):
            opening = self._safe_float(row.get("opening"))
            final   = self._safe_float(row.get("final"))
            if opening is None or final is None or opening <= 0:
                continue
            if (opening - final) / opening >= 0.15:
                detected.append(index)
        return detected

    def _has_converged(self, first_rank_counts: np.ndarray, n_simulations: int) -> bool:
        """95% 신뢰구간 폭이 모든 말에서 1% 미만이면 더 돌려도 변화가 작다고 판단합니다."""
        probabilities = first_rank_counts / n_simulations
        ci_widths = 2 * 1.96 * np.sqrt((probabilities * (1.0 - probabilities)) / n_simulations)
        return bool(np.all(ci_widths < CI_THRESHOLD))

    def _calculate_confidence_score(
        self,
        converged: bool,
        n_simulations: int,
        gate_bias_applied: bool,
        weather_exists: bool,
        smart_money_exists: bool,
    ) -> float:
        """신뢰도 점수는 수렴 여부, 반복 횟수, 보정 데이터 유무를 더해 0~100으로 제한합니다."""
        score = 40 if converged else 0
        if n_simulations >= 100_000:
            score += 40
        elif n_simulations >= 50_000:
            score += 30
        elif n_simulations >= 30_000:
            score += 20
        elif n_simulations >= 10_000:
            score += 10
        if gate_bias_applied:
            score += 10
        if weather_exists:
            score += 5
        if smart_money_exists:
            score += 5
        return float(min(score, 100))

    def _weather_sigma(self, weather: Any) -> float:
        """DB 날씨 값이 한글/영문으로 들어와도 대표 코드로 맞춰 불확실성 크기를 정합니다."""
        if weather is None:
            return WEATHER_SIGMA[None]
        normalized = str(weather).strip().upper()
        if normalized in {"맑음", "SUNNY"}:
            normalized = "CLEAR"
        elif normalized in {"흐림", "구름많음"}:
            normalized = "CLOUDY"
        elif normalized in {"비", "RAINY"}:
            normalized = "RAIN"
        return WEATHER_SIGMA.get(normalized, WEATHER_SIGMA[None])

    def _safe_float(self, value: Any) -> float | None:
        """Decimal, 문자열, None이 섞여 와도 float 또는 None으로 조심스럽게 변환합니다."""
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _json_dumps(self, value: dict[str, Any]) -> str:
        # json = Python 딕셔너리를 PostgreSQL jsonb 문자열로 바꾸는 표준 라이브러리입니다.
        import json

        return json.dumps(value, ensure_ascii=False)
