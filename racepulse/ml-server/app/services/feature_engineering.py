# -*- coding: utf-8 -*-
# =============================================================================
# feature_engineering.py — ML 피처 계산 서비스
# =============================================================================
# 피처 엔지니어링(Feature Engineering)이란?
#   원시 데이터(날짜, 이름, 착순 기록)를 ML 모델이 이해할 수 있는
#   숫자로 변환하고 가공하는 과정입니다.
#
#   예시:
#     원시 데이터: [1등, 3등, 2등, 1등, 4등]  ← 최근 5경주 기록
#     피처:        avg_rank_last5 = 2.2        ← 평균 착순
#                  best_rank_last5 = 1         ← 최고 착순
#
# 승률 계산 공식:
#   승률 = (1등 횟수) / (전체 출전 횟수)
#   예: 10번 출전, 3번 1등 → 승률 = 3/10 = 0.30 (30%)
#
# 왜 피처를 미리 계산해서 저장하는가?
#   실시간 예측 요청 시마다 수십 개의 복잡한 쿼리를 실행하면
#   응답 시간이 수 초가 걸립니다.
#   피처를 미리 계산해서 ml_feature_store에 저장해두면
#   예측 시 JSON 한 번만 읽으면 되므로 응답이 0.01초 이내입니다.
# =============================================================================

# logging = 서버 로그를 기록하는 표준 라이브러리입니다.
import logging
# datetime/date/timedelta = 날짜 계산에 사용합니다.
from datetime import date, datetime, timedelta
# Any/Optional = 타입 힌트입니다.
from typing import Any, Optional

# SQLAlchemy 쿼리 도구들
from sqlalchemy import select, func, and_
# AsyncSession = 비동기 DB 세션 타입입니다.
from sqlalchemy.ext.asyncio import AsyncSession

# ORM 모델들
from app.models.race import Race, RaceEntry, RaceResult
from app.models.master import Horse, Jockey, Trainer
from app.models.ml import MLFeatureStore

logger = logging.getLogger(__name__)

# 현재 피처 계산 로직 버전. 로직이 바뀌면 이 값을 올려서 재계산을 트리거합니다.
FEATURE_VERSION = "v1.0"

# 클래스 변동을 숫자로 인코딩하는 딕셔너리입니다.
# ML 모델은 문자열("UP")을 이해하지 못하므로 숫자(-1, 0, 1)로 변환합니다.
CLASS_CHANGE_ENCODE = {"UP": 1, "SAME": 0, "DOWN": -1}
DISTANCE_CHANGE_ENCODE = {"UP": 1, "SAME": 0, "DOWN": -1}


class FeatureEngineeringService:
    """경주 출전마 1마리의 ML 피처를 계산하고 저장하는 서비스입니다."""

    def __init__(self, db: AsyncSession) -> None:
        # db = 비동기 DB 세션입니다. 외부에서 주입받습니다.
        self.db = db

    # =========================================================================
    # 공개 메서드 (외부에서 호출하는 진입점)
    # =========================================================================

    async def build_feature_vector(self, race_entry_id: int) -> dict[str, Any]:
        """출전마 1마리의 전체 피처 벡터를 생성합니다.

        피처 벡터(Feature Vector)란?
          말 1마리에 대한 모든 피처를 하나의 딕셔너리로 모아놓은 것입니다.
          예: { "horse_win_rate_total": 0.25, "jockey_win_rate_total": 0.18, ... }
          ML 모델은 이 딕셔너리의 값들을 숫자 배열로 변환해서 입력으로 씁니다.

        @param race_entry_id  피처를 계산할 출전마 레코드 ID
        @return 피처 이름 → 피처 값 딕셔너리
        """
        # 출전표 기본 정보를 가져옵니다 (말/기수/조교사/경주 정보 포함)
        entry = await self._get_entry_with_relations(race_entry_id)
        if entry is None:
            raise ValueError(f"출전 정보를 찾을 수 없습니다: race_entry_id={race_entry_id}")

        horse_id    = entry.horse_id
        jockey_id   = entry.jockey_id
        trainer_id  = entry.trainer_id
        race        = entry.race
        meet_code   = race.meet_code
        distance    = race.distance
        track_cond  = race.track_condition.value if race.track_condition else None

        # ─── 각 카테고리별 피처 계산 ───────────────────────────────────────
        horse_features  = await self.calculate_horse_features(horse_id, race.id)
        jockey_features = await self.calculate_jockey_features(jockey_id, horse_id)
        trainer_features = await self.calculate_trainer_features(trainer_id, horse_id)
        race_features   = await self.calculate_race_features(race_entry_id)

        # ─── 경주 조건 기반 추가 피처 ─────────────────────────────────────
        context_features = await self._calculate_context_features(
            horse_id, meet_code, distance, track_cond
        )

        # 모든 피처를 하나의 딕셔너리로 합칩니다.
        # ** 연산자 = 딕셔너리를 펼쳐서 합치는 파이썬 문법입니다.
        features: dict[str, Any] = {
            **horse_features,
            **jockey_features,
            **trainer_features,
            **race_features,
            **context_features,
        }

        logger.info(
            "[피처 계산] race_entry_id=%d, 피처 개수=%d",
            race_entry_id, len(features)
        )
        return features

    async def save_to_feature_store(
        self,
        race_entry_id: int,
        race_id: int,
        features: dict[str, Any],
    ) -> MLFeatureStore:
        """계산된 피처 벡터를 ml_feature_store 테이블에 저장합니다.

        upsert = 이미 같은 (race_entry_id, feature_version) 레코드가 있으면 업데이트,
                 없으면 새로 삽입합니다.
        """
        # 기존 레코드 조회
        stmt = select(MLFeatureStore).where(
            and_(
                MLFeatureStore.race_entry_id == race_entry_id,
                MLFeatureStore.feature_version == FEATURE_VERSION,
            )
        )
        existing = await self.db.scalar(stmt)

        if existing:
            # 이미 있으면 피처 값만 업데이트합니다.
            existing.features = features
            existing.calculated_at = datetime.now()
            record = existing
        else:
            # 없으면 새로 만듭니다.
            record = MLFeatureStore(
                race_entry_id=race_entry_id,
                race_id=race_id,
                features=features,
                feature_version=FEATURE_VERSION,
            )
            self.db.add(record)

        await self.db.commit()
        logger.info("[피처 저장] race_entry_id=%d 저장 완료", race_entry_id)
        return record

    # =========================================================================
    # 말 관련 피처 계산
    # =========================================================================

    async def calculate_horse_features(
        self, horse_id: int, race_id: int
    ) -> dict[str, Any]:
        """말 관련 피처 14개를 계산합니다."""

        # 출전표에서 직접 읽을 수 있는 피처들
        entry_stmt = select(RaceEntry).where(
            and_(RaceEntry.horse_id == horse_id, RaceEntry.race_id == race_id)
        )
        entry = await self.db.scalar(entry_stmt)

        # 과거 결과 이력 조회 (이 경주 이전의 결과만 사용)
        history = await self._get_horse_history(horse_id, race_id)
        recent5 = history[:5]  # 최근 5경주

        # 통산 승률: 전체 이력에서 1위 횟수 / 전체 횟수
        total_races = len(history)
        total_wins  = sum(1 for r in history if r.rank == 1)
        horse_win_rate_total = _safe_rate(total_wins, total_races)

        # 최근 1년 승률
        one_year_ago = date.today() - timedelta(days=365)
        recent_history = [
            r for r in history
            if r.race and r.race.rc_date and r.race.rc_date >= one_year_ago
        ]
        recent_wins = sum(1 for r in recent_history if r.rank == 1)
        horse_win_rate_recent = _safe_rate(recent_wins, len(recent_history))

        # 연대율 (2위 이내 비율)
        place_count = sum(1 for r in history if r.rank is not None and r.rank <= 2)
        horse_place_rate = _safe_rate(place_count, total_races)

        # 최근 5경주 착순 통계
        ranks5 = [r.rank for r in recent5 if r.rank is not None]
        avg_rank_last5  = round(sum(ranks5) / len(ranks5), 2) if ranks5 else None
        best_rank_last5 = min(ranks5) if ranks5 else None

        return {
            # ── 말 직접 정보 ─────────────────────────────────────────────
            "horse_win_rate_total":  horse_win_rate_total,
            "horse_win_rate_recent": horse_win_rate_recent,
            "horse_place_rate":      horse_place_rate,
            "horse_weight":          entry.horse_weight if entry else None,
            "horse_weight_diff":     entry.horse_weight_diff if entry else None,
            # rest_days = 직전 경주로부터 경과일 (데뷔전이면 None)
            "days_since_last_race":  entry.rest_days if entry else None,
            # ── 최근 경주 성적 ───────────────────────────────────────────
            "avg_rank_last5":  avg_rank_last5,
            "best_rank_last5": best_rank_last5,
            # ── 출전 플래그 ──────────────────────────────────────────────
            "is_debut":    int(entry.is_debut)    if entry else 0,
            "is_comeback": int(entry.is_comeback) if entry else 0,
            # ── 클래스/거리 변동 (-1=하향, 0=유지, 1=상향) ───────────────
            "class_change":    CLASS_CHANGE_ENCODE.get(
                entry.class_change.value if entry and entry.class_change else "SAME", 0
            ),
            "distance_change": DISTANCE_CHANGE_ENCODE.get(
                entry.distance_change.value if entry and entry.distance_change else "SAME", 0
            ),
        }

    # =========================================================================
    # 기수 관련 피처 계산
    # =========================================================================

    async def calculate_jockey_features(
        self,
        jockey_id: Optional[int],
        horse_id: int,
    ) -> dict[str, Any]:
        """기수 관련 피처 3개를 계산합니다."""
        if jockey_id is None:
            # 기수 정보가 없으면 None으로 채웁니다.
            return {
                "jockey_win_rate_total":  None,
                "jockey_win_rate_recent": None,
                "jockey_horse_win_rate":  None,
            }

        # 기수 마스터 정보 조회
        jockey = await self.db.get(Jockey, jockey_id)

        # 이 기수 + 이 말 조합의 과거 승률 계산
        combo_stmt = (
            select(RaceResult)
            .join(RaceEntry, RaceResult.race_entry_id == RaceEntry.id)
            .where(
                and_(
                    RaceEntry.jockey_id == jockey_id,
                    RaceEntry.horse_id == horse_id,
                )
            )
        )
        combo_results = list((await self.db.scalars(combo_stmt)).all())
        combo_wins = sum(1 for r in combo_results if r.rank == 1)
        jockey_horse_win_rate = _safe_rate(combo_wins, len(combo_results))

        return {
            "jockey_win_rate_total":  float(jockey.win_rate_total)  if jockey and jockey.win_rate_total  else None,
            "jockey_win_rate_recent": float(jockey.win_rate_recent) if jockey and jockey.win_rate_recent else None,
            "jockey_horse_win_rate":  jockey_horse_win_rate,
        }

    # =========================================================================
    # 조교사 관련 피처 계산
    # =========================================================================

    async def calculate_trainer_features(
        self,
        trainer_id: Optional[int],
        horse_id: int,
    ) -> dict[str, Any]:
        """조교사 관련 피처 2개를 계산합니다."""
        if trainer_id is None:
            return {
                "trainer_win_rate_total": None,
                "trainer_horse_win_rate": None,
            }

        trainer = await self.db.get(Trainer, trainer_id)

        # 이 조교사 + 이 말 조합의 과거 승률
        combo_stmt = (
            select(RaceResult)
            .join(RaceEntry, RaceResult.race_entry_id == RaceEntry.id)
            .where(
                and_(
                    RaceEntry.trainer_id == trainer_id,
                    RaceEntry.horse_id == horse_id,
                )
            )
        )
        combo_results = list((await self.db.scalars(combo_stmt)).all())
        combo_wins = sum(1 for r in combo_results if r.rank == 1)
        trainer_horse_win_rate = _safe_rate(combo_wins, len(combo_results))

        return {
            "trainer_win_rate_total": float(trainer.win_rate_total) if trainer and trainer.win_rate_total else None,
            "trainer_horse_win_rate": trainer_horse_win_rate,
        }

    # =========================================================================
    # 경주 조건 피처 계산
    # =========================================================================

    async def calculate_race_features(self, race_entry_id: int) -> dict[str, Any]:
        """경주 출전 조건 피처 3개를 계산합니다 (게이트, 부담중량, 배당)."""
        entry = await self.db.get(RaceEntry, race_entry_id)
        if entry is None:
            return {
                "gate_no":       None,
                "burden_weight": None,
                "odds_win":      None,
            }

        return {
            "gate_no":       entry.gate_no,
            "burden_weight": float(entry.burden_weight) if entry.burden_weight else None,
            "odds_win":      float(entry.odds_win)      if entry.odds_win      else None,
        }

    # =========================================================================
    # 경주 컨텍스트 피처 계산 (경마장/거리/트랙 상태별 승률)
    # =========================================================================

    async def _calculate_context_features(
        self,
        horse_id: int,
        meet_code: str,
        distance: Optional[int],
        track_condition: Optional[str],
    ) -> dict[str, Any]:
        """해당 경마장·거리·트랙 상태에서의 말 성적 기반 피처 3개를 계산합니다."""

        # 같은 경마장에서의 기록
        course_results = await self._get_horse_results_by_condition(
            horse_id, meet_code=meet_code
        )
        course_wins = sum(1 for r in course_results if r.rank == 1)
        course_win_rate = _safe_rate(course_wins, len(course_results))

        # 같은 거리에서의 기록
        distance_results = await self._get_horse_results_by_condition(
            horse_id, distance=distance
        )
        distance_wins = sum(1 for r in distance_results if r.rank == 1)
        distance_win_rate = _safe_rate(distance_wins, len(distance_results))

        # 같은 트랙 상태에서의 기록
        condition_results = await self._get_horse_results_by_condition(
            horse_id, track_condition=track_condition
        )
        condition_wins = sum(1 for r in condition_results if r.rank == 1)
        condition_win_rate = _safe_rate(condition_wins, len(condition_results))

        # 게이트 번호별 승률 (경마장 + 거리 조건)
        # TODO: [Phase 2] gate_win_rate = 특정 게이트+경마장+거리 조합 승률 추가
        gate_win_rate = None  # 데이터 축적 후 구현 예정

        return {
            "course_win_rate":    course_win_rate,
            "distance_win_rate":  distance_win_rate,
            "condition_win_rate": condition_win_rate,
            "gate_win_rate":      gate_win_rate,
        }

    # =========================================================================
    # 내부 DB 조회 헬퍼 메서드
    # =========================================================================

    async def _get_entry_with_relations(
        self, race_entry_id: int
    ) -> Optional[RaceEntry]:
        """출전표와 연관 데이터(race, horse, jockey, trainer)를 함께 조회합니다."""
        from sqlalchemy.orm import selectinload

        stmt = (
            select(RaceEntry)
            .options(
                selectinload(RaceEntry.race),
                selectinload(RaceEntry.horse),
                selectinload(RaceEntry.jockey),
                selectinload(RaceEntry.trainer),
            )
            .where(RaceEntry.id == race_entry_id)
        )
        return await self.db.scalar(stmt)

    async def _get_horse_history(
        self, horse_id: int, current_race_id: int
    ) -> list[RaceResult]:
        """특정 말의 과거 경주 결과 이력을 날짜 내림차순으로 조회합니다.

        current_race_id 경주보다 이전 경주의 결과만 가져옵니다.
        미래 데이터가 섞이면 "미래를 보고 과거를 예측하는" 데이터 누수가 발생합니다.
        """
        from sqlalchemy.orm import selectinload

        stmt = (
            select(RaceResult)
            .join(Race, RaceResult.race_id == Race.id)
            .options(selectinload(RaceResult.race))
            .where(
                and_(
                    RaceResult.horse_id == horse_id,
                    # 현재 경주보다 ID가 작은 과거 경주만 사용합니다.
                    RaceResult.race_id < current_race_id,
                )
            )
            .order_by(RaceResult.race_id.desc())
            .limit(50)  # 최대 50경주 이력만 조회 (성능 제한)
        )
        return list((await self.db.scalars(stmt)).all())

    async def _get_horse_results_by_condition(
        self,
        horse_id: int,
        meet_code: Optional[str] = None,
        distance: Optional[int] = None,
        track_condition: Optional[str] = None,
    ) -> list[RaceResult]:
        """특정 조건(경마장/거리/트랙 상태)에서의 말 경주 결과를 조회합니다."""
        conditions = [RaceResult.horse_id == horse_id]

        if meet_code:
            conditions.append(Race.meet_code == meet_code)
        if distance:
            # 거리는 ±100m 오차 범위로 유사 거리도 포함합니다.
            conditions.append(
                and_(Race.distance >= distance - 100, Race.distance <= distance + 100)
            )
        if track_condition:
            conditions.append(Race.track_condition == track_condition)

        stmt = (
            select(RaceResult)
            .join(Race, RaceResult.race_id == Race.id)
            .where(and_(*conditions))
            .limit(100)
        )
        return list((await self.db.scalars(stmt)).all())


# =============================================================================
# 유틸리티 함수
# =============================================================================

def _safe_rate(wins: int, total: int) -> Optional[float]:
    """0으로 나누기를 방지하며 승률을 계산합니다.

    출전 기록이 없으면 None을 반환합니다.
    None은 "모름"을 나타내고, ML 모델이 이를 별도로 처리합니다.
    """
    if total == 0:
        return None
    return round(wins / total, 4)
