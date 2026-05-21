# -*- coding: utf-8 -*-
# =============================================================================
# bayesian_updater.py - 최근 경주 결과로 ML 승률 prior를 Bayesian 방식으로 보정하는 서비스
# =============================================================================

# datetime = DB에서 가져온 경주 날짜를 타입 힌트로 설명하기 위해 사용합니다.
from datetime import date
# typing.Any = SQLAlchemy row처럼 실행 시점에 실제 타입이 정해지는 값을 안전하게 표현합니다.
from typing import Any

# sqlalchemy.text = 직접 작성한 SQL을 AsyncSession에서 실행하기 위한 SQLAlchemy 도구입니다.
from sqlalchemy import text
# AsyncSession = FastAPI ML 서버에서 PostgreSQL을 비동기로 조회/저장하기 위한 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession


class BayesianUpdater:
    """Beta-Binomial 모델로 말의 ML 승률을 최근 성적에 맞춰 보정합니다."""

    def __init__(self, db_session: AsyncSession | None, prior_weight: float = 10.0, max_races: int = 5):
        # db_session = 최근 경주 결과와 로그 테이블을 조회/저장하는 DB 연결입니다. 단위 테스트에서는 None일 수 있습니다.
        self.db_session = db_session
        # prior_weight = ML 모델 예측을 몇 경기 분량의 근거로 볼지 정하는 값입니다. 클수록 ML 예측을 더 강하게 유지합니다.
        self.prior_weight = max(float(prior_weight), 0.0001)
        # max_races = 너무 오래된 성적이 현재 컨디션을 과하게 흔들지 않도록 최근 N경주만 반영합니다.
        self.max_races = max(int(max_races), 0)

    def update_single_horse(
        self,
        horse_id: int,
        prior_prob: float,
        recent_results: list[tuple[date | None, int | None]],
    ) -> float:
        """말 한 마리의 승률 prior를 최근 결과로 posterior 승률로 바꿉니다."""
        # Beta 분포는 0~1 사이 확률값을 표현하기 좋은 분포입니다.
        # 여기서는 "이 말이 1위할 확률"이라는 믿음을 alpha/beta 두 숫자로 표현합니다.
        safe_prior = min(max(float(prior_prob or 0.0), 0.0001), 0.9999)
        alpha = safe_prior * self.prior_weight
        beta = (1.0 - safe_prior) * self.prior_weight

        for index, (_race_date, position) in enumerate(recent_results[: self.max_races]):
            # 0.9 ** index = 오래된 경주일수록 영향력을 조금씩 줄이는 지수 감쇠값입니다.
            # 가장 최근 경주는 1.0, 그 다음은 0.9, 그 다음은 0.81처럼 반영됩니다.
            decay = 0.9 ** index
            if position == 1:
                # likelihood = 실제 관측 결과입니다. 1위는 성공으로 보고 alpha에 더합니다.
                alpha += 1.0 * decay
            else:
                # 1위가 아니면 실패로 보고 beta에 더합니다. 착순이 없거나 비정상이어도 보수적으로 실패 처리합니다.
                beta += 1.0 * decay

        # posterior mean = 업데이트된 Beta 분포의 기대값입니다.
        # alpha / (alpha + beta)는 "최근 결과까지 반영한 평균 승률"로 해석할 수 있습니다.
        posterior = alpha / (alpha + beta)
        return min(max(float(posterior), 0.0001), 0.9999)

    async def update_race_entries(
        self,
        race_id: int,
        entries_with_priors: dict[int, float],
    ) -> dict[int, float]:
        """경주에 출전하는 모든 말의 prior를 한 번에 posterior로 보정합니다."""
        updated_probabilities: dict[int, float] = {}

        for horse_id, prior_prob in entries_with_priors.items():
            # 신마처럼 과거 데이터가 없으면 recent_results가 빈 배열이 되고, ML prior가 그대로 유지됩니다.
            recent_results = await self.get_recent_results(horse_id)
            posterior_prob = self.update_single_horse(horse_id, prior_prob, recent_results)
            updated_probabilities[horse_id] = posterior_prob
            await self.store_bayesian_log(race_id, horse_id, prior_prob, posterior_prob)

        return updated_probabilities

    async def get_recent_results(self, horse_id: int) -> list[tuple[date | None, int | None]]:
        """race_results에서 특정 말의 최근 결과를 최신순으로 가져옵니다."""
        if self.db_session is None or self.max_races <= 0:
            return []

        result = await self.db_session.execute(
            text(
                """
                SELECT r.rc_date AS race_date, rr.rank AS position
                FROM race_results rr
                JOIN races r ON r.id = rr.race_id
                WHERE rr.horse_id = :horse_id
                  AND rr.rank IS NOT NULL
                ORDER BY r.rc_date DESC, rr.id DESC
                LIMIT :max_races
                """
            ),
            {"horse_id": horse_id, "max_races": self.max_races},
        )
        return [
            (row.get("race_date"), row.get("position"))
            for row in result.mappings().all()
        ]

    async def store_bayesian_log(
        self,
        race_id: int,
        horse_id: int,
        prior_prob: float,
        posterior_prob: float,
    ) -> None:
        """prediction_accuracy_logs 테이블이 있으면 Bayesian 보정 전후 값을 기록합니다."""
        if self.db_session is None:
            return

        if not await self._table_exists("prediction_accuracy_logs"):
            return

        # prediction_accuracy_logs는 기존 프로젝트에서 예측 품질 추적용으로 쓰는 테이블입니다.
        # 스키마가 환경마다 다를 수 있으므로 JSONB details 컬럼이 있을 때만 안전하게 기록합니다.
        if not await self._column_exists("prediction_accuracy_logs", "details"):
            return

        await self.db_session.execute(
            text(
                """
                INSERT INTO prediction_accuracy_logs (race_id, horse_id, details, created_at)
                VALUES (
                    :race_id,
                    :horse_id,
                    CAST(:details AS jsonb),
                    now()
                )
                """
            ),
            {
                "race_id": race_id,
                "horse_id": horse_id,
                "details": self._json_dumps(
                    {
                        "type": "BAYESIAN_UPDATE",
                        "prior_prob": prior_prob,
                        "posterior_prob": posterior_prob,
                        "delta": posterior_prob - prior_prob,
                    }
                ),
            },
        )

    async def _table_exists(self, table_name: str) -> bool:
        """선택 테이블이 없는 개발 DB에서도 기능이 실패하지 않도록 존재 여부를 확인합니다."""
        if self.db_session is None:
            return False

        row = (
            await self.db_session.execute(
                text("SELECT to_regclass(:table_name) IS NOT NULL AS exists"),
                {"table_name": table_name},
            )
        ).mappings().first()
        return bool(row and row["exists"])

    async def _column_exists(self, table_name: str, column_name: str) -> bool:
        """로그 테이블의 컬럼 구조가 다른 환경에서도 안전하게 건너뛰기 위한 확인 함수입니다."""
        if self.db_session is None:
            return False

        row = (
            await self.db_session.execute(
                text(
                    """
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_name = :table_name
                          AND column_name = :column_name
                    ) AS exists
                    """
                ),
                {"table_name": table_name, "column_name": column_name},
            )
        ).mappings().first()
        return bool(row and row["exists"])

    def _json_dumps(self, value: dict[str, Any]) -> str:
        # json = 한글이 깨지지 않도록 ensure_ascii=False로 JSON 문자열을 만드는 표준 라이브러리입니다.
        import json

        return json.dumps(value, ensure_ascii=False)
