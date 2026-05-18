# -*- coding: utf-8 -*-
# =============================================================================
# running_style_service.py — 말별 주행 스타일 분류 서비스
# =============================================================================
# 주행 스타일(Running Style)이란?
#   말이 경주에서 주로 어느 위치에서 달리는지를 나타내는 성향입니다.
#
#   LEADER  : 선행마 — 앞에서 레이스를 이끌 때 잘하는 말 (낮은 게이트에서 성적 좋음)
#   CLOSER  : 추입마 — 뒤에서 따라오다 막판에 추월하는 말 (높은 게이트에서도 잘함)
#   STALKER : 중간 추적마 — 2~3위를 유지하다 막판 이벤트를 기다리는 말
#
# 어떻게 분류하는가?
#   게이트 번호(gate_no)와 착순(rank)의 상관관계를 분석합니다.
#   - 내측 게이트(1~4)에서 성적이 좋고 외측(9+)에서 나쁘면 → LEADER
#   - 내측에서 나쁘고 외측에서 좋으면 → CLOSER
#   - 비슷하면 → STALKER
#
# FE에서의 활용:
#   "이번 경주 선행마 3마리 vs 추입마 4마리 — 앞이 혼잡할 것으로 예상"
#   각 말 카드에 스타일 아이콘 표시 (선행 🏃, 추입 🔄)
# =============================================================================

import logging
from datetime import datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RunningStyleService:
    """race_results + race_entries 데이터에서 말의 주행 스타일을 분류하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def calculate_all_styles(self) -> dict[str, Any]:
        """race_results 전체 데이터에서 모든 말의 주행 스타일을 배치 분류합니다.

        분류 기준:
        - 내측 게이트(1~4)에서의 평균 착순 vs 외측 게이트(9+)에서의 평균 착순
        - 내측 성적이 외측보다 1.5순위 이상 좋으면 → LEADER
        - 외측 성적이 내측보다 1.5순위 이상 좋으면 → CLOSER
        - 그 외 → STALKER
        - 최소 3경주 이상 데이터가 있는 말만 분류
        """
        logger.info("[주행스타일] 배치 분류 시작")

        upsert_sql = text("""
            INSERT INTO horse_running_style (
                horse_id, style, track_type, distance_category,
                confidence_score, race_count,
                avg_gate_no, avg_inner_rank, avg_outer_rank,
                updated_at
            )
            WITH horse_gate_stats AS (
                SELECT
                    re.horse_id,
                    COUNT(*)                                         AS race_count,
                    AVG(re.gate_no)                                  AS avg_gate_no,

                    -- 내측 게이트(1~4)에서의 평균 착순
                    AVG(CASE WHEN re.gate_no BETWEEN 1 AND 4
                             THEN rr.rank END)                       AS avg_inner_rank,

                    -- 외측 게이트(9 이상)에서의 평균 착순
                    AVG(CASE WHEN re.gate_no >= 9
                             THEN rr.rank END)                       AS avg_outer_rank,

                    -- 내측에서 뛴 경주 수
                    COUNT(CASE WHEN re.gate_no BETWEEN 1 AND 4
                               THEN 1 END)                           AS inner_races,

                    -- 외측에서 뛴 경주 수
                    COUNT(CASE WHEN re.gate_no >= 9
                               THEN 1 END)                           AS outer_races

                FROM race_results rr
                JOIN race_entries re ON rr.race_entry_id = re.id
                WHERE rr.rank BETWEEN 1 AND 20   -- 비정상 착순 제외
                GROUP BY re.horse_id
                HAVING COUNT(*) >= 3             -- 최소 3경주 이상만 분류
            )
            SELECT
                horse_id,

                -- 스타일 분류 로직
                CASE
                    -- 내외측 모두 데이터가 있고 내측 성적이 확연히 좋으면 LEADER
                    WHEN avg_inner_rank IS NOT NULL
                         AND avg_outer_rank IS NOT NULL
                         AND avg_inner_rank < avg_outer_rank - 1.5
                    THEN 'LEADER'

                    -- 외측 성적이 확연히 좋으면 CLOSER
                    WHEN avg_inner_rank IS NOT NULL
                         AND avg_outer_rank IS NOT NULL
                         AND avg_outer_rank < avg_inner_rank - 1.5
                    THEN 'CLOSER'

                    -- 그 외는 STALKER (중간 전략)
                    ELSE 'STALKER'
                END                              AS style,

                'ALL'                            AS track_type,
                'ALL'                            AS distance_category,

                -- 신뢰도: 내외측 모두 데이터가 있으면 높음
                CASE
                    WHEN inner_races >= 3 AND outer_races >= 3 THEN 0.8
                    WHEN inner_races >= 2 OR  outer_races >= 2 THEN 0.5
                    ELSE 0.3
                END                              AS confidence_score,

                race_count,
                avg_gate_no,
                avg_inner_rank,
                avg_outer_rank,
                NOW()                            AS updated_at

            FROM horse_gate_stats

            ON CONFLICT (horse_id, track_type, distance_category)
            DO UPDATE SET
                style             = EXCLUDED.style,
                confidence_score  = EXCLUDED.confidence_score,
                race_count        = EXCLUDED.race_count,
                avg_gate_no       = EXCLUDED.avg_gate_no,
                avg_inner_rank    = EXCLUDED.avg_inner_rank,
                avg_outer_rank    = EXCLUDED.avg_outer_rank,
                updated_at        = NOW()
        """)

        result = await self.db.execute(upsert_sql)
        await self.db.commit()

        rows_affected = result.rowcount

        # 스타일별 분포 집계
        dist = (await self.db.execute(text("""
            SELECT style, COUNT(*) AS cnt
            FROM horse_running_style
            WHERE track_type = 'ALL'
            GROUP BY style
            ORDER BY cnt DESC
        """))).all()

        distribution = {row[0]: row[1] for row in dist}
        logger.info("[주행스타일] 배치 분류 완료. 말 수: %d | 분포: %s", rows_affected, distribution)

        return {
            "horses_classified": rows_affected,
            "distribution":      distribution,
            "computed_at":       datetime.now().isoformat(),
        }

    async def get_race_style_summary(self, race_id: int) -> list[dict[str, Any]]:
        """경주에 출전한 말들의 주행 스타일을 한 번에 조회합니다. FE 경주 분석 카드에서 사용합니다."""
        rows = (await self.db.execute(text("""
            SELECT
                h.id   AS horse_id,
                h.name AS horse_name,
                hrs.style,
                hrs.confidence_score,
                hrs.race_count,
                hrs.avg_inner_rank,
                hrs.avg_outer_rank
            FROM race_entries re
            JOIN horses h ON h.id = re.horse_id
            LEFT JOIN horse_running_style hrs
                ON hrs.horse_id = re.horse_id AND hrs.track_type = 'ALL'
            WHERE re.race_id = :race_id
            ORDER BY re.gate_no
        """), {"race_id": race_id})).mappings().all()

        return [
            {
                "horse_id":        row["horse_id"],
                "horse_name":      row["horse_name"],
                "style":           row["style"] or "UNKNOWN",
                "confidence":      float(row["confidence_score"] or 0),
                "race_count":      row["race_count"] or 0,
                "avg_inner_rank":  float(row["avg_inner_rank"]) if row["avg_inner_rank"] else None,
                "avg_outer_rank":  float(row["avg_outer_rank"]) if row["avg_outer_rank"] else None,
            }
            for row in rows
        ]
