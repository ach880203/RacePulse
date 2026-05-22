# -*- coding: utf-8 -*-
# =============================================================================
# change_detector.py — 경주 변경사항 감지 5종
# =============================================================================
# 출전표가 확정된 이후에도 아래와 같은 변경이 발생할 수 있습니다.
# 이 모듈은 30분마다 마사회 API 최신값과 DB 저장값을 비교해 변경을 감지합니다.
#
# 감지 5종:
#   1. 기수 변경 (🔴 빨강) — 가장 영향이 크고 자주 발생
#   2. 출전 취소 (⚫ 회색) — 말이 출전 목록에서 사라짐
#   3. 조교사 변경 (🟠 주황) — 훈련 환경 변화
#   4. 장비 변경 (🟡 노랑) — 블링커 등 장비 교체
#   5. 트랙 상태 급변 (🔵 파랑) — 날씨로 인해 트랙 등급이 1단계 이상 변화
#
# 감지 후 처리:
#   - DB (trainer_changes / equipment_changes) 에 이력 저장
#   - Redis Pub/Sub 'racepulse:changes' 채널에 이벤트 발행 (BE Spring Boot가 구독)
#   - AI 해설 캐시 무효화 (기수/조교사/장비 변경 시)
#   - MC 재시뮬레이션 트리거
# =============================================================================

# logging = 서버 로그를 기록하는 표준 라이브러리입니다.
import logging
# json = Redis에 저장할 딕셔너리를 JSON 문자열로 변환합니다.
import json
# dataclasses = 데이터만 담는 클래스를 간단하게 선언하는 도구입니다.
from dataclasses import dataclass, field, asdict
# datetime = 이벤트 발생 시각을 기록합니다.
from datetime import datetime, date, time, timedelta
# Optional = 값이 없을 수도 있는 타입 힌트입니다.
from typing import Optional

# SQLAlchemy 비동기 세션 — DB 조회에 사용합니다.
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession

# 내부 모듈
from app.core.redis_client import get_redis_client
from app.models.race import Race, RaceEntry, TrackConditionEnum, DataStatusEnum
from app.models.master import Horse, Jockey, Trainer
from app.services.kra_api import KRAApiService

logger = logging.getLogger(__name__)

# =============================================================================
# 트랙 상태 등급 순서 (낮을수록 건조, 높을수록 포화)
# 급변 기준: 1단계 이상 차이가 날 때 (예: DRY→HUMID = 2단계 차이 → 급변)
# =============================================================================
TRACK_LEVEL = {
    TrackConditionEnum.DRY: 0,       # 건조 (良)
    TrackConditionEnum.WET: 1,       # 습윤 (稍重)
    TrackConditionEnum.HUMID: 2,     # 다습 (重)
    TrackConditionEnum.SATURATED: 3, # 포화 (不良)
}

# =============================================================================
# ChangeEvent 데이터 클래스
# =============================================================================
# @dataclass 데코레이터 = 클래스에 __init__, __repr__ 등을 자동으로 만들어줍니다.
# 데이터만 담는 클래스를 선언할 때 코드를 줄이는 데 유용합니다.
@dataclass
class ChangeEvent:
    """하나의 변경사항을 담는 데이터 클래스입니다."""
    # 변경 종류: JOCKEY / SCRATCH / TRAINER / EQUIPMENT / TRACK
    type: str
    # FE에 표시될 뱃지 이모지
    badge: str
    # 영향도: VERY_HIGH / HIGH / MEDIUM / LOW
    impact: str
    # 어느 경주에서 발생한 변경인지 (출전 취소/트랙은 race_id만, 나머지는 horse_id도)
    race_id: int
    # 어느 말에서 발생한 변경인지 (트랙 변경은 None)
    horse_id: Optional[int]
    # 변경 전 값 (예: "박기수", "블링커 없음")
    old_value: Optional[str]
    # 변경 후 값 (예: "김기수", "블링커 착용")
    new_value: str
    # 감지 시각
    detected_at: datetime = field(default_factory=datetime.now)
    # AI 해설 캐시를 무효화해야 하는지 여부
    # 기수/조교사/장비 변경은 해설 내용에 직접 영향을 주므로 True
    affects_commentary: bool = False


# =============================================================================
# ChangeDetector 메인 클래스
# =============================================================================

class ChangeDetector:
    """
    경주 변경사항을 감지하고 이벤트를 발행하는 서비스입니다.

    사용 흐름:
      detector = ChangeDetector(session, kra_api)
      changes = await detector.detect_all(rc_date="20260607")
    """

    def __init__(self, session: AsyncSession, kra: KRAApiService) -> None:
        # session = PostgreSQL DB와 연결된 비동기 세션입니다.
        self.session = session
        # kra = 마사회 API를 호출하는 서비스 객체입니다.
        self.kra = kra
        # redis = Pub/Sub 이벤트 발행과 캐시 무효화에 사용합니다.
        self.redis = get_redis_client()

    # =========================================================================
    # 메인 진입점
    # =========================================================================

    async def detect_all(self, rc_date: str, race_no: Optional[int] = None) -> list[ChangeEvent]:
        """
        5종 변경 감지를 모두 실행합니다.
        APScheduler가 30분마다 이 메서드를 호출합니다.

        @param rc_date  경주 날짜 (YYYYMMDD 형식, 예: '20260607')
        @param race_no  특정 경주만 검사할 경우 지정. None이면 전체 경주 검사.
        @return 감지된 변경 이벤트 목록
        """
        all_changes: list[ChangeEvent] = []

        # 날짜 형식: 마사회 API는 YYYYMMDD, date 객체는 변환 필요
        rc_date_obj = datetime.strptime(rc_date, "%Y%m%d").date()

        try:
            # 1. 기수 변경 감지
            jockey_changes = await self.detect_jockey_changes(rc_date, race_no)
            all_changes.extend(jockey_changes)

            # 2. 출전 취소 감지
            scratch_changes = await self.detect_scratches(rc_date, race_no)
            all_changes.extend(scratch_changes)

            # 3. 조교사 변경 감지
            trainer_changes = await self.detect_trainer_changes(rc_date, race_no)
            all_changes.extend(trainer_changes)

            # 4. 장비 변경 감지
            equip_changes = await self.detect_equipment_changes(rc_date, race_no)
            all_changes.extend(equip_changes)

            # 5. 트랙 상태 급변 감지 (경주 단위가 아닌 날짜 단위)
            track_changes = await self.detect_track_condition_change(rc_date_obj, race_no)
            all_changes.extend(track_changes)

        except Exception as exc:
            logger.exception("[변경감지] detect_all 오류: %s", exc)
            return all_changes

        # 감지된 이벤트 처리
        for change in all_changes:
            await self._save_to_db(change)
            await self._publish_to_redis(change)
            if change.affects_commentary:
                await self._invalidate_commentary_cache(change.race_id)
            await self._trigger_mc_resimulation(change.race_id)

        if all_changes:
            logger.info("[변경감지] %d건 감지 완료 (rc_date=%s)", len(all_changes), rc_date)

        return all_changes

    # =========================================================================
    # 1. 기수 변경 감지 (🔴)
    # =========================================================================

    async def detect_jockey_changes(
        self, rc_date: str, race_no: Optional[int] = None
    ) -> list[ChangeEvent]:
        """
        마사회 API 최신 출전표와 DB 저장값을 비교해 기수 변경을 감지합니다.

        기수 변경은 예측 정확도에 가장 큰 영향을 줍니다.
        (기수의 기술, 말과의 호흡, 과거 궁합 등이 예측 모델에 반영되어 있기 때문)
        """
        changes: list[ChangeEvent] = []

        # DB에서 해당 날짜/경주의 출전 엔트리를 조회합니다.
        entries = await self._get_db_entries(rc_date, race_no)
        if not entries:
            return changes

        for entry in entries:
            try:
                # 마사회 API에서 해당 출전마의 현재 기수 ID를 조회합니다.
                api_data = await self.kra.fetch_entry_info(
                    meet_code=entry.race.meet_code,
                    rc_date=rc_date,
                    race_no=entry.race.race_no,
                    horse_no=entry.gate_no,
                )
                if not api_data:
                    continue

                api_jockey_id = api_data.get("jockey_id")

                # DB 저장값과 API 현재값이 다르면 변경된 것입니다.
                if api_jockey_id and entry.jockey_id and int(api_jockey_id) != entry.jockey_id:
                    # 기수 이름 조회 (ChangeEvent의 old_value/new_value에 사용)
                    old_jockey_name = await self._get_jockey_name(entry.jockey_id)
                    new_jockey_name = await self._get_jockey_name(int(api_jockey_id))

                    # DB 업데이트: race_entries.jockey_id와 data_status를 갱신합니다.
                    await self.session.execute(
                        update(RaceEntry)
                        .where(RaceEntry.id == entry.id)
                        .values(
                            jockey_id=int(api_jockey_id),
                            data_status=DataStatusEnum.JOCKEY_CHANGED,
                            last_updated=datetime.now(),
                        )
                    )
                    await self.session.commit()

                    changes.append(ChangeEvent(
                        type="JOCKEY",
                        badge="🔴",
                        impact="VERY_HIGH",
                        race_id=entry.race_id,
                        horse_id=entry.horse_id,
                        old_value=old_jockey_name,
                        new_value=new_jockey_name,
                        # 기수가 바뀌면 해설의 "이 기수의 특성상" 같은 내용도 달라져야 합니다.
                        affects_commentary=True,
                    ))
                    logger.info(
                        "[기수변경] race_id=%d horse_id=%d %s → %s",
                        entry.race_id, entry.horse_id, old_jockey_name, new_jockey_name
                    )

            except Exception as exc:
                logger.error(
                    "[기수변경] 감지 오류 entry_id=%d: %s", entry.id, exc
                )

        return changes

    # =========================================================================
    # 2. 출전 취소 감지 (⚫)
    # =========================================================================

    async def detect_scratches(
        self, rc_date: str, race_no: Optional[int] = None
    ) -> list[ChangeEvent]:
        """
        마사회 API 현재 출전 목록에서 사라진 말을 감지합니다.

        출전 취소는 MC 시뮬레이션의 출전마 수가 바뀌므로 즉시 재시뮬레이션이 필요합니다.
        """
        changes: list[ChangeEvent] = []

        db_entries = await self._get_db_entries(rc_date, race_no)
        if not db_entries:
            return changes

        # DB 엔트리를 경주별로 그룹화합니다.
        race_groups: dict[int, list] = {}
        for entry in db_entries:
            race_groups.setdefault(entry.race_id, []).append(entry)

        for race_id, entries in race_groups.items():
            if not entries:
                continue

            race = entries[0].race
            try:
                # 마사회 API에서 현재 출전 목록을 가져옵니다.
                api_entries = await self.kra.fetch_entry_list(
                    meet_code=race.meet_code,
                    rc_date=rc_date,
                    race_no=race.race_no,
                )
                if api_entries is None:
                    continue

                # API에 있는 horse_id 집합
                api_horse_ids = {int(e["horse_id"]) for e in api_entries if e.get("horse_id")}

                for entry in entries:
                    # DB에는 있지만 API 현재 목록에 없으면 출전 취소된 것입니다.
                    if entry.horse_id not in api_horse_ids:
                        horse_name = await self._get_horse_name(entry.horse_id)

                        changes.append(ChangeEvent(
                            type="SCRATCH",
                            badge="⚫",
                            impact="VERY_HIGH",
                            race_id=race_id,
                            horse_id=entry.horse_id,
                            old_value=horse_name,
                            new_value="출전 취소",
                            # 출전 취소는 해설의 "출전마 분석" 부분이 달라집니다.
                            affects_commentary=True,
                        ))
                        logger.info(
                            "[출전취소] race_id=%d horse_id=%d (%s)",
                            race_id, entry.horse_id, horse_name
                        )

            except Exception as exc:
                logger.error("[출전취소] 감지 오류 race_id=%d: %s", race_id, exc)

        return changes

    # =========================================================================
    # 3. 조교사 변경 감지 (🟠)
    # =========================================================================

    async def detect_trainer_changes(
        self, rc_date: str, race_no: Optional[int] = None
    ) -> list[ChangeEvent]:
        """
        마사회 API와 DB를 비교해 조교사 변경을 감지합니다.

        조교사는 훈련 환경에 영향을 줍니다.
        - 조교사가 갑자기 바뀌면 말이 낯선 환경에서 훈련받은 것이므로 컨디션 불확실성 증가
        - Bayesian prior도 자동으로 하향 조정됩니다 (prompt-30 연동)
        """
        changes: list[ChangeEvent] = []

        entries = await self._get_db_entries(rc_date, race_no)
        if not entries:
            return changes

        for entry in entries:
            try:
                api_data = await self.kra.fetch_entry_info(
                    meet_code=entry.race.meet_code,
                    rc_date=rc_date,
                    race_no=entry.race.race_no,
                    horse_no=entry.gate_no,
                )
                if not api_data:
                    continue

                api_trainer_id = api_data.get("trainer_id")
                if api_trainer_id and entry.trainer_id and int(api_trainer_id) != entry.trainer_id:
                    old_trainer_name = await self._get_trainer_name(entry.trainer_id)
                    new_trainer_name = await self._get_trainer_name(int(api_trainer_id))

                    # trainer_changes 테이블에 이력 저장 (V13에서 생성)
                    # DB 직접 INSERT는 _save_to_db()에서 처리합니다.

                    # race_entries의 trainer_id도 업데이트합니다.
                    await self.session.execute(
                        update(RaceEntry)
                        .where(RaceEntry.id == entry.id)
                        .values(
                            trainer_id=int(api_trainer_id),
                            last_updated=datetime.now(),
                        )
                    )
                    await self.session.commit()

                    changes.append(ChangeEvent(
                        type="TRAINER",
                        badge="🟠",
                        impact="MEDIUM",
                        race_id=entry.race_id,
                        horse_id=entry.horse_id,
                        old_value=old_trainer_name,
                        new_value=new_trainer_name,
                        affects_commentary=True,
                    ))
                    logger.info(
                        "[조교사변경] race_id=%d horse_id=%d %s → %s",
                        entry.race_id, entry.horse_id, old_trainer_name, new_trainer_name
                    )

            except Exception as exc:
                logger.error("[조교사변경] 감지 오류 entry_id=%d: %s", entry.id, exc)

        return changes

    # =========================================================================
    # 4. 장비 변경 감지 (🟡)
    # =========================================================================

    async def detect_equipment_changes(
        self, rc_date: str, race_no: Optional[int] = None
    ) -> list[ChangeEvent]:
        """
        블링커 등 장비 변경을 감지합니다.

        블링커란?
        - 말의 시야를 좌우로 제한하는 장비 (눈가리개)
        - 집중력을 높이는 효과가 있어 착용 첫 경주에 성적이 오르는 경향이 있습니다.
        - blinker_first_time: 처음 착용하면 ML 피처에서 별도 처리합니다.
        """
        changes: list[ChangeEvent] = []

        entries = await self._get_db_entries(rc_date, race_no)
        if not entries:
            return changes

        for entry in entries:
            try:
                api_data = await self.kra.fetch_entry_info(
                    meet_code=entry.race.meet_code,
                    rc_date=rc_date,
                    race_no=entry.race.race_no,
                    horse_no=entry.gate_no,
                )
                if not api_data:
                    continue

                # 마사회 API에서 장비 정보를 가져옵니다.
                api_blinker = api_data.get("blinker", "")
                # DB에서 이전 장비 기록을 조회합니다 (equipment_changes 테이블)
                old_blinker = await self._get_last_equipment(entry.horse_id, "BLINKER")

                # 장비 값이 달라졌으면 변경된 것입니다.
                if api_blinker != old_blinker:
                    # 블링커 최초 착용 여부: 이전 기록이 없으면(None) 첫 착용입니다.
                    blinker_first_time = (old_blinker is None and api_blinker != "")

                    # ChangeEvent에 블링커 최초 착용 여부를 new_value에 포함합니다.
                    new_value_str = api_blinker or "제거"
                    if blinker_first_time:
                        new_value_str += " (첫 착용)"

                    changes.append(ChangeEvent(
                        type="EQUIPMENT",
                        badge="🟡",
                        impact="MEDIUM",
                        race_id=entry.race_id,
                        horse_id=entry.horse_id,
                        old_value=old_blinker or "없음",
                        new_value=new_value_str,
                        affects_commentary=True,
                    ))
                    logger.info(
                        "[장비변경] race_id=%d horse_id=%d 블링커: %s → %s (첫착용=%s)",
                        entry.race_id, entry.horse_id,
                        old_blinker or "없음", api_blinker or "제거", blinker_first_time
                    )

            except Exception as exc:
                logger.error("[장비변경] 감지 오류 entry_id=%d: %s", entry.id, exc)

        return changes

    # =========================================================================
    # 5. 트랙 상태 급변 감지 (🔵)
    # =========================================================================

    async def detect_track_condition_change(
        self, rc_date: date, race_no: Optional[int] = None
    ) -> list[ChangeEvent]:
        """
        트랙 상태가 1단계 이상 바뀌었을 때 감지합니다.

        트랙 등급:
          DRY(良, 0) → WET(稍重, 1) → HUMID(重, 2) → SATURATED(不良, 3)

        급변 기준: 1단계 이상 (예: DRY→WET도 급변, DRY→HUMID는 2단계 급변)
        영향: 선행마 vs 추입마 유리/불리가 달라짐 → MC 재시뮬레이션 필요
        """
        changes: list[ChangeEvent] = []

        rc_date_str = rc_date.strftime("%Y%m%d")

        # 해당 날짜의 경주 목록을 조회합니다.
        stmt = select(Race).where(Race.rc_date == rc_date)
        if race_no:
            stmt = stmt.where(Race.race_no == race_no)

        result = await self.session.execute(stmt)
        races = result.scalars().all()

        for race in races:
            try:
                # 마사회 API에서 현재 트랙 상태를 가져옵니다.
                api_track_raw = await self.kra.fetch_track_condition(
                    meet_code=race.meet_code,
                    rc_date=rc_date_str,
                    race_no=race.race_no,
                )
                if not api_track_raw:
                    continue

                # API 값을 TrackConditionEnum으로 변환합니다.
                api_track = self._parse_track_condition(api_track_raw)
                if not api_track:
                    continue

                db_track = race.track_condition

                if db_track and api_track != db_track:
                    # 트랙 등급 차이 계산
                    db_level = TRACK_LEVEL.get(db_track, 0)
                    api_level = TRACK_LEVEL.get(api_track, 0)
                    level_diff = abs(api_level - db_level)

                    # 1단계 이상 차이나면 급변으로 판단합니다.
                    if level_diff >= 1:
                        # DB Race 테이블의 track_condition도 업데이트합니다.
                        await self.session.execute(
                            update(Race)
                            .where(Race.id == race.id)
                            .values(track_condition=api_track)
                        )
                        await self.session.commit()

                        changes.append(ChangeEvent(
                            type="TRACK",
                            badge="🔵",
                            # 2단계 이상 급변이면 HIGH, 1단계면 MEDIUM
                            impact="HIGH" if level_diff >= 2 else "MEDIUM",
                            race_id=race.id,
                            horse_id=None,  # 트랙 변경은 특정 말이 아닌 경주 전체에 영향
                            old_value=db_track.value if db_track else "미정",
                            new_value=api_track.value,
                            # 트랙 변경은 해설의 "오늘 트랙 상태는" 부분에 영향을 줍니다.
                            affects_commentary=(level_diff >= 2),
                        ))
                        logger.info(
                            "[트랙급변] race_id=%d %s → %s (차이=%d단계)",
                            race.id, db_track, api_track, level_diff
                        )

            except Exception as exc:
                logger.error("[트랙급변] 감지 오류 race_id=%d: %s", race.id, exc)

        return changes

    # =========================================================================
    # 내부 처리 메서드
    # =========================================================================

    async def _save_to_db(self, change: ChangeEvent) -> None:
        """
        변경 이벤트를 DB 이력 테이블에 저장합니다.

        - TRAINER → trainer_changes 테이블 INSERT
        - EQUIPMENT → equipment_changes 테이블 INSERT
        - 나머지 (JOCKEY/SCRATCH/TRACK) → DB에 별도 이력 테이블 없이 로그만 기록
          (기수변경은 race_entries.jockey_id 업데이트로 이미 반영됨)
        """
        try:
            if change.type == "TRAINER":
                # trainer_changes 테이블에 이력 INSERT (V13에서 생성된 테이블)
                await self.session.execute(
                    """
                    INSERT INTO trainer_changes
                        (horse_id, race_id, old_trainer_id, new_trainer_id, detected_at, change_date)
                    VALUES
                        (:horse_id, :race_id,
                         (SELECT trainer_id FROM race_entries WHERE race_id = :race_id AND horse_id = :horse_id LIMIT 1),
                         (SELECT id FROM trainers WHERE name = :new_value LIMIT 1),
                         :detected_at, :change_date)
                    """,
                    {
                        "horse_id": change.horse_id,
                        "race_id": change.race_id,
                        "new_value": change.new_value,
                        "detected_at": change.detected_at,
                        "change_date": change.detected_at.date(),
                    }
                )
                await self.session.commit()

            elif change.type == "EQUIPMENT":
                # equipment_changes 테이블에 이력 INSERT (V13에서 생성된 테이블)
                blinker_first_time = "(첫 착용)" in change.new_value
                await self.session.execute(
                    """
                    INSERT INTO equipment_changes
                        (horse_id, race_id, equipment_type, old_value, new_value,
                         detected_at, change_date, blinker_first_time)
                    VALUES
                        (:horse_id, :race_id, 'BLINKER', :old_value, :new_value,
                         :detected_at, :change_date, :blinker_first_time)
                    """,
                    {
                        "horse_id": change.horse_id,
                        "race_id": change.race_id,
                        "old_value": change.old_value,
                        "new_value": change.new_value,
                        "detected_at": change.detected_at,
                        "change_date": change.detected_at.date(),
                        "blinker_first_time": blinker_first_time,
                    }
                )
                await self.session.commit()

        except Exception as exc:
            logger.error("[DB저장] 이벤트 저장 실패 type=%s: %s", change.type, exc)

    async def _publish_to_redis(self, change: ChangeEvent) -> None:
        """
        감지된 변경 이벤트를 Redis Pub/Sub 채널에 발행합니다.

        Pub/Sub(발행-구독) 패턴이란?
          발행자(ML FastAPI)가 채널에 메시지를 보내면,
          구독자(BE Spring Boot)가 자동으로 받아서 처리합니다.
          직접 HTTP 호출 없이 느슨하게 연결하는 방법입니다.

        채널: 'racepulse:changes'
        구독자: Spring Boot ChangeEventSubscriber.java (prompt-34에서 구현)
        """
        try:
            payload = json.dumps({
                "type": change.type,
                "badge": change.badge,
                "impact": change.impact,
                "race_id": change.race_id,
                "horse_id": change.horse_id,
                "old_value": change.old_value,
                "new_value": change.new_value,
                "affects_commentary": change.affects_commentary,
                # ISO 8601 형식으로 직렬화합니다 (BE에서 파싱 용이)
                "detected_at": change.detected_at.isoformat(),
            }, ensure_ascii=False)

            await self.redis.publish("racepulse:changes", payload)
            logger.debug("[Redis Pub] 이벤트 발행: %s race_id=%d", change.type, change.race_id)

        except Exception as exc:
            logger.error("[Redis Pub] 발행 실패: %s", exc)

    async def _invalidate_commentary_cache(self, race_id: int) -> None:
        """
        AI 해설 캐시를 무효화합니다.

        기수/조교사/장비가 바뀌면 기존 해설이 잘못된 정보를 담고 있을 수 있습니다.
        캐시를 삭제하면 다음 조회 시 GPT가 새로 해설을 생성합니다.
        """
        try:
            pre_key = f"commentary:pre:{race_id}"
            post_key = f"commentary:post:{race_id}"
            deleted = await self.redis.delete(pre_key, post_key)
            if deleted:
                logger.info("[캐시무효화] race_id=%d 해설 캐시 삭제 (%d건)", race_id, deleted)
        except Exception as exc:
            logger.error("[캐시무효화] 실패 race_id=%d: %s", race_id, exc)

    async def _trigger_mc_resimulation(self, race_id: int) -> None:
        """
        MC 재시뮬레이션을 요청합니다.

        출전마 정보가 바뀌었으니 기존 시뮬레이션 결과도 더 이상 유효하지 않습니다.
        Redis 채널에 재시뮬레이션 요청을 발행하면
        ML 서버 내부에서 비동기로 MC를 다시 실행합니다.
        """
        try:
            await self.redis.publish(
                "racepulse:resimulate",
                json.dumps({"race_id": race_id})
            )
            logger.debug("[MC재시뮬] race_id=%d 요청 발행", race_id)
        except Exception as exc:
            logger.error("[MC재시뮬] 요청 실패 race_id=%d: %s", race_id, exc)

    # =========================================================================
    # DB 조회 헬퍼
    # =========================================================================

    async def _get_db_entries(
        self, rc_date: str, race_no: Optional[int] = None
    ) -> list[RaceEntry]:
        """해당 날짜/경주번호의 출전 엔트리를 DB에서 조회합니다."""
        rc_date_obj = datetime.strptime(rc_date, "%Y%m%d").date()

        stmt = (
            select(RaceEntry)
            .join(RaceEntry.race)
            .where(Race.rc_date == rc_date_obj)
        )
        if race_no:
            stmt = stmt.where(Race.race_no == race_no)

        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def _get_jockey_name(self, jockey_id: int) -> str:
        """jockey_id로 기수 이름을 조회합니다."""
        result = await self.session.execute(
            select(Jockey.name).where(Jockey.id == jockey_id)
        )
        return result.scalar_one_or_none() or f"기수#{jockey_id}"

    async def _get_trainer_name(self, trainer_id: int) -> str:
        """trainer_id로 조교사 이름을 조회합니다."""
        result = await self.session.execute(
            select(Trainer.name).where(Trainer.id == trainer_id)
        )
        return result.scalar_one_or_none() or f"조교사#{trainer_id}"

    async def _get_horse_name(self, horse_id: int) -> str:
        """horse_id로 말 이름을 조회합니다."""
        result = await self.session.execute(
            select(Horse.horse_nm).where(Horse.id == horse_id)
        )
        return result.scalar_one_or_none() or f"말#{horse_id}"

    async def _get_last_equipment(
        self, horse_id: int, equipment_type: str
    ) -> Optional[str]:
        """
        equipment_changes 테이블에서 가장 최근 장비 값을 조회합니다.
        기록이 없으면 None을 반환합니다 (= 장비 없음/첫 착용 가능성).
        """
        try:
            result = await self.session.execute(
                """
                SELECT new_value FROM equipment_changes
                WHERE horse_id = :horse_id AND equipment_type = :equipment_type
                ORDER BY detected_at DESC
                LIMIT 1
                """,
                {"horse_id": horse_id, "equipment_type": equipment_type}
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception:
            # 테이블이 없거나 조회 실패 시 None 반환
            return None

    @staticmethod
    def _parse_track_condition(raw: str) -> Optional[TrackConditionEnum]:
        """
        마사회 API 트랙 상태 코드를 TrackConditionEnum으로 변환합니다.

        마사회 API 코드:
          '1' 또는 '良' → DRY (건조)
          '2' 또는 '稍重' → WET (습윤)
          '3' 또는 '重' → HUMID (다습)
          '4' 또는 '不良' → SATURATED (포화)
        """
        mapping = {
            "1": TrackConditionEnum.DRY,
            "良": TrackConditionEnum.DRY,
            "2": TrackConditionEnum.WET,
            "稍重": TrackConditionEnum.WET,
            "3": TrackConditionEnum.HUMID,
            "重": TrackConditionEnum.HUMID,
            "4": TrackConditionEnum.SATURATED,
            "不良": TrackConditionEnum.SATURATED,
        }
        return mapping.get(str(raw).strip())
