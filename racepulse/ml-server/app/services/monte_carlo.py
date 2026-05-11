# -*- coding: utf-8 -*-
# =============================================================================
# monte_carlo.py - 예측 확률을 여러 번 다시 뽑아 순위 분포를 계산하는 서비스
# =============================================================================

from datetime import datetime, timezone
from typing import Any

import numpy as np
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


class MonteCarloService:
    """ML 예측값을 10,000번 반복 추첨해 각 말의 순위별 가능성을 계산합니다."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_simulation(self, race_id: int, n_simulations: int = 10_000) -> dict[str, Any]:
        rows = await self._load_prediction_rows(race_id)
        if not rows:
            raise ValueError("예측 결과가 없어 시뮬레이션을 실행할 수 없습니다.")

        probabilities = np.array([max(float(row["win_prob"] or 0), 0.0001) for row in rows], dtype=float)
        probabilities = probabilities / probabilities.sum()
        horse_count = len(rows)
        rank_counts = np.zeros((horse_count, horse_count), dtype=int)
        upset_wins = 0
        high_odds_indexes = {
            index
            for index, row in enumerate(rows)
            if row["odds_win"] is not None and float(row["odds_win"]) >= 10.0
        }

        for _ in range(n_simulations):
            # np.random.choice는 확률표를 기준으로 말을 한 번씩 뽑습니다. replace=False라서 같은 말이 두 번 나오지 않습니다.
            sampled_indexes = np.random.choice(horse_count, size=horse_count, replace=False, p=probabilities)
            for rank_index, horse_index in enumerate(sampled_indexes):
                rank_counts[horse_index][rank_index] += 1
            if int(sampled_indexes[0]) in high_odds_indexes:
                upset_wins += 1

        horses = []
        for index, row in enumerate(rows):
            rank_distribution = self.calculate_rank_distribution(rank_counts[index], n_simulations)
            expected_rank = sum((rank + 1) * count for rank, count in enumerate(rank_counts[index])) / n_simulations
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
            "n_simulations": n_simulations,
            "horses": horses,
            "upset_probability": round((upset_wins / n_simulations) * 100, 1),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.save_simulation_result(race_id, result)
        return result

    def calculate_rank_distribution(self, rank_counts: np.ndarray, n_simulations: int) -> dict[str, float]:
        first = round((rank_counts[0] / n_simulations) * 100, 1)
        second = round((rank_counts[1] / n_simulations) * 100, 1) if len(rank_counts) > 1 else 0.0
        third = round((rank_counts[2] / n_simulations) * 100, 1) if len(rank_counts) > 2 else 0.0
        fourth_or_lower = round(100.0 - first - second - third, 1)
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
        result = await self.db.execute(
            text(
                """
                SELECT
                    p.win_prob,
                    h.id AS horse_id,
                    h.name AS horse_name,
                    e.odds_win
                FROM predictions p
                JOIN race_entries e ON e.id = p.race_entry_id
                JOIN horses h ON h.id = e.horse_id
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

    def _json_dumps(self, value: dict[str, Any]) -> str:
        import json

        return json.dumps(value, ensure_ascii=False)
