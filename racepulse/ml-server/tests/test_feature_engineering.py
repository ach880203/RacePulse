# -*- coding: utf-8 -*-
# =============================================================================
# test_feature_engineering.py — 피처 엔지니어링 단위 테스트
# =============================================================================
# 테스트 구성:
#   1. _safe_rate() — 순수 함수. DB 없이 바로 호출합니다.
#   2. 인코딩 딕셔너리 — 값이 맞는지 확인합니다.
#   3. calculate_jockey/trainer_features(None) — DB 호출 없이 기본값 반환
#   4. calculate_race_features(entry=None) — DB Mock 사용
#   5. calculate_horse_features(신마) — DB Mock + 빈 이력
#   6. calculate_horse_features(경력마) — DB Mock + 실제 이력
#
# Mock(목)이란?
#   실제 DB 대신 "원하는 값을 미리 지정해두면 그걸 돌려주는 가짜 객체"입니다.
#   DB 없이도 DB 연동 코드를 테스트할 수 있습니다.
# =============================================================================

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta

# 테스트 대상 임포트
from app.services.feature_engineering import (
    FeatureEngineeringService,
    _safe_rate,
    CLASS_CHANGE_ENCODE,
    DISTANCE_CHANGE_ENCODE,
)


# =============================================================================
# 섹션 1: _safe_rate() — 순수 함수 테스트 (DB 불필요)
# =============================================================================
# 순수 함수 = 입력이 같으면 항상 같은 출력, 외부 상태를 바꾸지 않음
# DB도, Mock도 필요 없습니다. 그냥 호출하면 됩니다.
# =============================================================================

class TestSafeRate:

    def test_정상_승률_계산(self):
        # 10번 출전, 3번 1위 → 0.3
        assert _safe_rate(3, 10) == 0.3

    def test_출전_기록_없을때_None_반환(self):
        # total=0 이면 ZeroDivisionError 대신 None 반환해야 합니다.
        # 신마(첫 출전)나 데이터 없는 말의 경우입니다.
        assert _safe_rate(0, 0) is None

    def test_승리_없는_말(self):
        # 10번 출전, 0번 1위 → 0.0
        assert _safe_rate(0, 10) == 0.0

    def test_전승(self):
        # 5번 출전, 5번 1위 → 1.0
        assert _safe_rate(5, 5) == 1.0

    def test_소수점_4자리_반올림(self):
        # 1/3 = 0.3333... → 반올림해서 0.3333
        result = _safe_rate(1, 3)
        assert result == 0.3333

    def test_승수가_total보다_클수없음(self):
        # 방어 테스트: 혹시 wins > total 이상한 데이터가 와도 계산은 됨
        result = _safe_rate(5, 3)  # 잘못된 데이터지만 계산 자체는 돼야 함
        assert result is not None


# =============================================================================
# 섹션 2: 인코딩 딕셔너리 — 값 검증
# =============================================================================
# CLASS_CHANGE_ENCODE, DISTANCE_CHANGE_ENCODE 의 값이
# 정확히 -1/0/1 인지 확인합니다.
# ML 모델 입력에 잘못된 값이 들어가면 예측 결과가 완전히 틀릴 수 있습니다.
# =============================================================================

class TestEncodingDicts:

    def test_class_change_encode_값(self):
        assert CLASS_CHANGE_ENCODE["UP"]   ==  1
        assert CLASS_CHANGE_ENCODE["SAME"] ==  0
        assert CLASS_CHANGE_ENCODE["DOWN"] == -1

    def test_distance_change_encode_값(self):
        assert DISTANCE_CHANGE_ENCODE["UP"]   ==  1
        assert DISTANCE_CHANGE_ENCODE["SAME"] ==  0
        assert DISTANCE_CHANGE_ENCODE["DOWN"] == -1

    def test_class_change_encode_키_3개만_존재(self):
        # 예상치 못한 키가 추가되면 테스트가 실패합니다.
        assert set(CLASS_CHANGE_ENCODE.keys()) == {"UP", "SAME", "DOWN"}

    def test_distance_change_encode_키_3개만_존재(self):
        assert set(DISTANCE_CHANGE_ENCODE.keys()) == {"UP", "SAME", "DOWN"}


# =============================================================================
# 섹션 3: calculate_jockey_features(jockey_id=None)
# =============================================================================
# 기수 정보가 없을 때 (기수변경 직후 등) None을 올바르게 반환하는지 검증합니다.
# jockey_id=None 이면 DB 조회를 시도하지 않고 바로 None 딕셔너리를 반환합니다.
# =============================================================================

class TestJockeyFeaturesNone:

    @pytest.fixture
    def service(self):
        # AsyncMock = async def 메서드를 가짜로 만드는 Mock 클래스입니다.
        mock_db = AsyncMock()
        return FeatureEngineeringService(db=mock_db)

    @pytest.mark.asyncio
    async def test_기수_없을때_None_딕셔너리_반환(self, service):
        result = await service.calculate_jockey_features(
            jockey_id=None,  # 기수 정보 없음
            horse_id=1,
        )

        # 세 피처 모두 None 이어야 합니다.
        assert result["jockey_win_rate_total"]  is None
        assert result["jockey_win_rate_recent"] is None
        assert result["jockey_horse_win_rate"]  is None

    @pytest.mark.asyncio
    async def test_기수_없을때_키_3개_존재(self, service):
        result = await service.calculate_jockey_features(jockey_id=None, horse_id=1)
        assert set(result.keys()) == {
            "jockey_win_rate_total",
            "jockey_win_rate_recent",
            "jockey_horse_win_rate",
        }


# =============================================================================
# 섹션 4: calculate_trainer_features(trainer_id=None)
# =============================================================================

class TestTrainerFeaturesNone:

    @pytest.fixture
    def service(self):
        return FeatureEngineeringService(db=AsyncMock())

    @pytest.mark.asyncio
    async def test_조교사_없을때_None_딕셔너리_반환(self, service):
        result = await service.calculate_trainer_features(
            trainer_id=None,
            horse_id=1,
        )

        assert result["trainer_win_rate_total"] is None
        assert result["trainer_horse_win_rate"] is None

    @pytest.mark.asyncio
    async def test_조교사_없을때_키_2개_존재(self, service):
        result = await service.calculate_trainer_features(trainer_id=None, horse_id=1)
        assert set(result.keys()) == {
            "trainer_win_rate_total",
            "trainer_horse_win_rate",
        }


# =============================================================================
# 섹션 5: calculate_race_features — DB에서 entry가 None으로 반환될 때
# =============================================================================
# DB에서 출전표를 못 찾는 경우 (데이터 수집 실패 등)
# None 대신 에러가 터지면 안 됩니다.
# =============================================================================

class TestRaceFeaturesEntryNone:

    @pytest.fixture
    def service_with_none_entry(self):
        mock_db = AsyncMock()
        # db.get()이 None을 반환하도록 설정합니다.
        mock_db.get.return_value = None
        return FeatureEngineeringService(db=mock_db)

    @pytest.mark.asyncio
    async def test_entry_없을때_None_딕셔너리_반환(self, service_with_none_entry):
        result = await service_with_none_entry.calculate_race_features(
            race_entry_id=999  # 존재하지 않는 ID
        )

        assert result["gate_no"]       is None
        assert result["burden_weight"] is None
        assert result["odds_win"]      is None

    @pytest.mark.asyncio
    async def test_entry_없을때_키_3개_존재(self, service_with_none_entry):
        result = await service_with_none_entry.calculate_race_features(race_entry_id=999)
        assert set(result.keys()) == {"gate_no", "burden_weight", "odds_win"}


# =============================================================================
# 섹션 6: calculate_horse_features — 신마(첫 출전) 케이스
# =============================================================================
# 신마 = 이전 경주 기록이 없는 말입니다.
# 이 경우 승률 계산에서 ZeroDivisionError가 나면 안 됩니다.
# 승률 관련 피처는 None, is_debut=1 이어야 합니다.
# =============================================================================

class TestHorseFeaturesDebut:

    @pytest.fixture
    def service_with_debut_horse(self):
        """신마 출전 상황을 시뮬레이션하는 Mock DB를 가진 서비스."""
        mock_db = AsyncMock()

        # 출전표 Mock 생성
        mock_entry = MagicMock()
        mock_entry.horse_weight      = 450
        mock_entry.horse_weight_diff = 0
        mock_entry.rest_days         = None   # 신마는 휴식일 없음
        mock_entry.is_debut          = True   # 데뷔전
        mock_entry.is_comeback       = False
        mock_entry.class_change      = None   # 첫 출전이라 클래스 변동 없음
        mock_entry.distance_change   = None

        # db.scalar()가 mock_entry를 반환하도록 설정
        mock_db.scalar.return_value = mock_entry

        # _get_horse_history()는 이 서비스의 내부 메서드입니다.
        # 빈 리스트를 반환하도록 AsyncMock으로 교체합니다.
        service = FeatureEngineeringService(db=mock_db)
        service._get_horse_history = AsyncMock(return_value=[])  # 이력 없음

        return service

    @pytest.mark.asyncio
    async def test_신마_통산승률_None(self, service_with_debut_horse):
        result = await service_with_debut_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 출전 기록이 없으므로 승률은 None이어야 합니다.
        assert result["horse_win_rate_total"]  is None
        assert result["horse_win_rate_recent"] is None
        assert result["horse_place_rate"]      is None

    @pytest.mark.asyncio
    async def test_신마_최근5경주_통계_None(self, service_with_debut_horse):
        result = await service_with_debut_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 이력이 없으므로 None
        assert result["avg_rank_last5"]  is None
        assert result["best_rank_last5"] is None

    @pytest.mark.asyncio
    async def test_신마_데뷔_플래그_1(self, service_with_debut_horse):
        result = await service_with_debut_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # is_debut=True → int(True) = 1
        assert result["is_debut"]    == 1
        assert result["is_comeback"] == 0

    @pytest.mark.asyncio
    async def test_신마_피처_키_12개_존재(self, service_with_debut_horse):
        result = await service_with_debut_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        expected_keys = {
            "horse_win_rate_total",
            "horse_win_rate_recent",
            "horse_place_rate",
            "horse_weight",
            "horse_weight_diff",
            "days_since_last_race",
            "avg_rank_last5",
            "best_rank_last5",
            "is_debut",
            "is_comeback",
            "class_change",
            "distance_change",
        }
        assert set(result.keys()) == expected_keys


# =============================================================================
# 섹션 7: calculate_horse_features — 경력마 케이스
# =============================================================================
# 과거 경주 이력이 있는 말의 피처 계산이 정확한지 검증합니다.
# =============================================================================

def _make_race_result(rank: int, days_ago: int) -> MagicMock:
    """테스트용 RaceResult Mock을 생성하는 헬퍼 함수."""
    result = MagicMock()
    result.rank = rank

    mock_race = MagicMock()
    mock_race.rc_date = date.today() - timedelta(days=days_ago)
    result.race = mock_race

    return result


class TestHorseFeaturesVeteran:

    @pytest.fixture
    def service_with_veteran_horse(self):
        """경력마 출전 상황을 시뮬레이션하는 서비스."""
        mock_db = AsyncMock()

        # 출전표 Mock
        mock_entry = MagicMock()
        mock_entry.horse_weight      = 480
        mock_entry.horse_weight_diff = -2
        mock_entry.rest_days         = 14
        mock_entry.is_debut          = False
        mock_entry.is_comeback       = False
        mock_entry.class_change      = None
        mock_entry.distance_change   = None
        mock_db.scalar.return_value  = mock_entry

        # 이력: 최근 7경주 (1위 2번, 2위 1번, 나머지 하위)
        history = [
            _make_race_result(rank=1, days_ago=14),   # 최근 1경주: 1위
            _make_race_result(rank=3, days_ago=30),   # 최근 2경주: 3위
            _make_race_result(rank=2, days_ago=50),   # 최근 3경주: 2위
            _make_race_result(rank=1, days_ago=70),   # 최근 4경주: 1위
            _make_race_result(rank=4, days_ago=90),   # 최근 5경주: 4위
            _make_race_result(rank=5, days_ago=200),  # 6경주 전
            _make_race_result(rank=3, days_ago=300),  # 7경주 전
        ]

        service = FeatureEngineeringService(db=mock_db)
        service._get_horse_history = AsyncMock(return_value=history)
        return service

    @pytest.mark.asyncio
    async def test_통산_승률_정확(self, service_with_veteran_horse):
        result = await service_with_veteran_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 7경주 중 1위 2번 → 2/7 = 0.2857
        assert result["horse_win_rate_total"] == pytest.approx(0.2857, abs=0.001)

    @pytest.mark.asyncio
    async def test_최근5경주_평균착순_정확(self, service_with_veteran_horse):
        result = await service_with_veteran_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 최근 5경주: [1, 3, 2, 1, 4] → 평균 = 11/5 = 2.2
        assert result["avg_rank_last5"] == pytest.approx(2.2, abs=0.01)

    @pytest.mark.asyncio
    async def test_최근5경주_최고착순_정확(self, service_with_veteran_horse):
        result = await service_with_veteran_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 최근 5경주 중 최고: 1위
        assert result["best_rank_last5"] == 1

    @pytest.mark.asyncio
    async def test_연대율_정확(self, service_with_veteran_horse):
        result = await service_with_veteran_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 7경주 중 2위 이내: 1위×2 + 2위×1 = 3번 → 3/7 = 0.4286
        assert result["horse_place_rate"] == pytest.approx(0.4286, abs=0.001)

    @pytest.mark.asyncio
    async def test_승률값_0에서1_사이(self, service_with_veteran_horse):
        result = await service_with_veteran_horse.calculate_horse_features(
            horse_id=1, race_id=100
        )
        # 승률은 항상 0.0 ~ 1.0 사이여야 합니다.
        for key in ["horse_win_rate_total", "horse_win_rate_recent", "horse_place_rate"]:
            val = result[key]
            if val is not None:
                assert 0.0 <= val <= 1.0, f"{key} = {val} 는 0~1 범위를 벗어남"
