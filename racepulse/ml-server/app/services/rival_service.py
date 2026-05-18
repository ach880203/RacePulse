# -*- coding: utf-8 -*-
# =============================================================================
# rival_service.py — 말 간 직접 대결 이력(rival_records) 배치 계산 서비스
# =============================================================================
# 직접 대결(Head-to-Head)이란?
#   같은 경주에 두 말이 함께 출전했을 때 누가 더 좋은 순위를 기록했는지의 이력입니다.
#   예: 투어킹 vs 피엔에스트윈 — 3번 맞붙어 투어킹이 2번, 피엔에스트윈이 1번 이김
#
# 왜 ML 피처로 유용한가?
#   오늘 경주에 두 말이 함께 출전했다면, 과거 대결 이력이 예측의 단서가 됩니다.
#   "이 두 말이 3번 붙었는데 항상 A가 이겼다" → A의 당첨 확률 상향 보정
# =============================================================================

import logging
from datetime import datetime
from typing import Any

# SQLAlchemy text = 순수 SQL을 직접 실행할 때 사용합니다.
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RivalService:
    """기존 race_results 데이터에서 라이벌 대결 이력을 계산하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def calculate_all_rivals(self) -> dict[str, Any]:
        """race_results 전체 데이터에서 말 간 직접 대결 이력을 배치 계산합니다.

        같은 경주에 함께 출전한 모든 말 쌍에 대해:
        - 총 대결 횟수
        - 각 말의 승리 횟수 (더 낮은 순위 = 승리)
        - 각 말의 평균 착순
        - 마지막 대결 경주 정보
        를 rival_records 테이블에 UPSERT합니다.

        Python 루프 대신 SQL 배치로 처리하므로 수만 건도 빠르게 계산됩니다.
        """
        logger.info("[라이벌] 직접 대결 이력 배치 계산 시작")

        # ─── UPSERT SQL ───────────────────────────────────────────────────────
        # 같은 경주에 출전한 두 말을 쌍으로 만들고 (horse_id_1 < horse_id_2 조건으로 중복 제거)
        # 각 쌍의 통계를 집계한 뒤 rival_records에 저장합니다.
        upsert_sql = text("""
            INSERT INTO rival_records (
                horse_id_1, horse_id_2,
                meet_code, distance,
                total_races,
                horse1_wins, horse2_wins,
                horse1_avg_position, horse2_avg_position,
                last_race_id, last_race_date,
                updated_at
            )
            SELECT
                LEAST(rr1.horse_id, rr2.horse_id)    AS horse_id_1,
                GREATEST(rr1.horse_id, rr2.horse_id) AS horse_id_2,
                r.meet_code,
                r.distance,
                COUNT(*)                             AS total_races,

                -- horse_id_1(작은 쪽)이 더 좋은 순위(낮은 숫자)일 때 horse1 승리
                SUM(CASE
                    WHEN rr1.horse_id < rr2.horse_id AND rr1.rank < rr2.rank THEN 1
                    WHEN rr1.horse_id > rr2.horse_id AND rr2.rank < rr1.rank THEN 1
                    ELSE 0
                END)                                 AS horse1_wins,

                -- horse_id_2(큰 쪽)이 더 좋은 순위일 때 horse2 승리
                SUM(CASE
                    WHEN rr1.horse_id > rr2.horse_id AND rr1.rank < rr2.rank THEN 1
                    WHEN rr1.horse_id < rr2.horse_id AND rr2.rank < rr1.rank THEN 1
                    ELSE 0
                END)                                 AS horse2_wins,

                -- horse_id_1의 평균 착순
                AVG(CASE
                    WHEN rr1.horse_id < rr2.horse_id THEN rr1.rank
                    ELSE rr2.rank
                END)                                 AS horse1_avg_position,

                -- horse_id_2의 평균 착순
                AVG(CASE
                    WHEN rr1.horse_id > rr2.horse_id THEN rr1.rank
                    ELSE rr2.rank
                END)                                 AS horse2_avg_position,

                -- 가장 최근 대결 경주 ID (두 말이 함께 출전한 경주 중 ID 최대값)
                MAX(rr1.race_id)                     AS last_race_id,
                MAX(r.rc_date)                       AS last_race_date,
                NOW()                                AS updated_at

            FROM race_results rr1
            JOIN race_results rr2
                ON rr1.race_id = rr2.race_id
               AND rr1.horse_id != rr2.horse_id
               AND rr1.horse_id < rr2.horse_id   -- 양방향 중복 방지
            JOIN races r ON rr1.race_id = r.id

            -- 비정상 착순(실격 등) 제외
            WHERE rr1.rank BETWEEN 1 AND 20
              AND rr2.rank BETWEEN 1 AND 20

            GROUP BY
                LEAST(rr1.horse_id, rr2.horse_id),
                GREATEST(rr1.horse_id, rr2.horse_id),
                r.meet_code,
                r.distance

            ON CONFLICT (horse_id_1, horse_id_2, meet_code, distance)
            DO UPDATE SET
                total_races         = EXCLUDED.total_races,
                horse1_wins         = EXCLUDED.horse1_wins,
                horse2_wins         = EXCLUDED.horse2_wins,
                horse1_avg_position = EXCLUDED.horse1_avg_position,
                horse2_avg_position = EXCLUDED.horse2_avg_position,
                last_race_id        = EXCLUDED.last_race_id,
                last_race_date      = EXCLUDED.last_race_date,
                updated_at          = NOW()
        """)

        result = await self.db.execute(upsert_sql)
        await self.db.commit()

        rows_affected = result.rowcount
        logger.info("[라이벌] 배치 계산 완료. 저장된 대결 쌍: %d", rows_affected)
        return {"rival_pairs_saved": rows_affected, "computed_at": datetime.now().isoformat()}

    async def get_h2h_stats(
        self, horse_id_a: int, horse_id_b: int
    ) -> dict[str, Any] | None:
        """두 말의 직접 대결 통계를 조회합니다. FE 라이벌 섹션에서 사용합니다."""
        # horse_id_1 < horse_id_2 제약에 맞게 순서를 자동으로 조정합니다.
        h1 = min(horse_id_a, horse_id_b)
        h2 = max(horse_id_a, horse_id_b)

        row = (await self.db.execute(
            text("""
                SELECT rr.*, h1.name AS horse1_name, h2.name AS horse2_name
                FROM rival_records rr
                JOIN horses h1 ON h1.id = rr.horse_id_1
                JOIN horses h2 ON h2.id = rr.horse_id_2
                WHERE rr.horse_id_1 = :h1 AND rr.horse_id_2 = :h2
                ORDER BY rr.total_races DESC
                LIMIT 1
            """),
            {"h1": h1, "h2": h2},
        )).mappings().first()

        if not row:
            return None

        # 쿼리 시 입력한 말이 horse_id_1인지 horse_id_2인지에 따라 승리 수를 맞춰서 반환합니다.
        a_is_horse1 = (horse_id_a == h1)
        return {
            "horse_a_id":      horse_id_a,
            "horse_a_name":    row["horse1_name"] if a_is_horse1 else row["horse2_name"],
            "horse_b_id":      horse_id_b,
            "horse_b_name":    row["horse2_name"] if a_is_horse1 else row["horse1_name"],
            "total_races":     row["total_races"],
            "horse_a_wins":    row["horse1_wins"] if a_is_horse1 else row["horse2_wins"],
            "horse_b_wins":    row["horse2_wins"] if a_is_horse1 else row["horse1_wins"],
            "horse_a_avg_pos": float(row["horse1_avg_position"] or 0) if a_is_horse1
                               else float(row["horse2_avg_position"] or 0),
            "last_race_date":  row["last_race_date"].isoformat() if row["last_race_date"] else None,
        }
