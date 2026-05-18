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
from sqlalchemy import text
# AsyncSession = FastAPI 서비스에서 DB를 비동기로 조회/저장하기 위한 SQLAlchemy 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

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


@dataclass(frozen=True)
class SimulationContext:
    """작업자에게 넘길 값 묶음입니다. 딕셔너리보다 필드명이 고정되어 실수를 줄입니다."""

    probabilities: list[float]
    gate_numbers: list[int]
    odds_win: list[float | None]
    weather_sigma: float
    smart_money_indexes: list[int]
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

        if norm is not None and context.weather_sigma > 0:
            normal_noise = norm.ppf(np.clip(merged_uniforms, 0.000001, 0.999999))
            try:
                cholesky_matrix = np.linalg.cholesky(_build_gate_correlation(context.gate_numbers))
                correlated_noise = normal_noise @ cholesky_matrix.T
            except np.linalg.LinAlgError:
                # 상관 행렬이 수치적으로 불안정하면 독립 노이즈로 내려갑니다.
                correlated_noise = normal_noise
            adjusted = adjusted + (correlated_noise * context.weather_sigma)

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

    async def run_simulation(self, race_id: int, n_simulations: int = 10_000) -> dict[str, Any]:
        rows = await self._load_prediction_rows(race_id)
        if not rows:
            raise ValueError("예측 결과가 없어 시뮬레이션을 실행할 수 없습니다.")

        requested_simulations = max(int(n_simulations or MIN_SIMULATIONS), MIN_SIMULATIONS)
        target_simulations = min(requested_simulations, MAX_SIMULATIONS)
        probabilities = self._build_adjusted_probabilities(rows)
        gate_numbers = self._build_gate_numbers(rows)
        odds_win = [self._safe_float(row.get("odds_win")) for row in rows]
        weather_sigma = self._weather_sigma(rows[0].get("weather"))
        smart_money_indexes = self._detect_smart_money_indexes(rows)

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

        result = await self.db.execute(
            text(
                f"""
                SELECT
                    p.win_prob,
                    h.id AS horse_id,
                    h.name AS horse_name,
                    e.odds_win,
                    e.gate_no,
                    r.weather,
                    {odds_select}
                FROM predictions p
                JOIN race_entries e ON e.id = p.race_entry_id
                JOIN horses h ON h.id = e.horse_id
                JOIN races r ON r.id = p.race_id
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
