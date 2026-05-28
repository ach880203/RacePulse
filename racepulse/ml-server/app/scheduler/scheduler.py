# -*- coding: utf-8 -*-
# =============================================================================
# scheduler.py — APScheduler 자동 수집 파이프라인 (완성본)
# =============================================================================
# APScheduler란?
#   "특정 시간이 되면 자동으로 함수를 실행해주는" 일정 관리 도구입니다.
#   스마트폰 알람처럼 생각하면 쉽습니다.
#
# 크론(Cron) 표현식이란?
#   날짜/시간을 달력처럼 지정하는 방식입니다.
#   예: day_of_week='mon', hour=14, minute=0 → 매주 월요일 14:00
#   예: hour=6, minute=30 → 매일 오전 6:30
#   예: day=1, hour=5 → 매월 1일 오전 5:00
#
# 이 스케줄러에서 관리하는 작업 목록:
#   - 경주 결과 수집 (월요일 14:00, 화요일 09:00)
#   - 출전표 수집 (목요일 10:00 / 17:30, 금요일 08:00)
#   - 당일 정보 수집 (토/일/월 09:05)
#   - 마스터 데이터 수집 (매주 화요일 06:00, 매월 1일 05:00)
#   - 날씨 수집 (매일 06:00, 06:30, 18:30)
#   - Rate Limit 카운터 리셋 (매일 00:00)
# =============================================================================

# logging = 서버 로그(정보/경고/오류)를 기록하는 표준 라이브러리입니다.
import logging
# date/datetime/timedelta = 수집 대상 날짜를 계산할 때 사용합니다.
from datetime import date, datetime, timedelta

# AsyncIOScheduler = FastAPI 같은 asyncio 앱 안에서 비동기 스케줄을 돌리는 스케줄러입니다.
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# AsyncSessionLocal = 스케줄 작업마다 독립적인 DB 세션을 열기 위한 팩토리입니다.
from app.core.database import AsyncSessionLocal
# settings = 스케줄러 시간대 같은 공통 설정 객체입니다.
from app.core.config import settings
# redis_client 모듈의 함수들 — Rate Limit 카운터, 락, 체크포인트 관리
import app.core.redis_client as redis_svc
# DataService = KRA API 호출 + DB 저장을 담당하는 서비스입니다.
from app.services.data_service import DataService
# KRAApiService = 실제 마사회 API HTTP 요청을 담당합니다.
from app.services.kra_api import KRAApiService, KRARateLimitExceededError
# WeatherApiService = 기상청 API 호출 및 날씨 데이터 저장을 담당합니다.
from app.services.weather_api import WeatherApiService

logger = logging.getLogger(__name__)

# 모든 경마장 코드 목록
ALL_MEET_CODES: tuple[str, ...] = ("SC", "BU", "JJ")


class CollectionScheduler:
    """APScheduler 래퍼 클래스. 모든 자동 수집 스케줄을 여기서 등록합니다."""

    def __init__(self) -> None:
        # timezone = 스케줄러가 시간을 어떤 기준으로 해석할지 설정합니다.
        # Asia/Seoul = 한국 표준시(KST, UTC+9)를 기준으로 합니다.
        self.scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

    async def start(self) -> None:
        """스케줄러를 시작합니다. 이미 실행 중이면 중복 시작하지 않습니다."""
        if not self.scheduler.running:
            self._register_jobs()
            self.scheduler.start()
            logger.info("[스케줄러] 시작 완료. 등록된 작업: %d개", len(self.scheduler.get_jobs()))

    async def shutdown(self) -> None:
        """스케줄러를 종료합니다."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("[스케줄러] 종료 완료.")

    def get_jobs_info(self) -> list[dict]:
        """현재 등록된 모든 스케줄 정보를 반환합니다. (관리자 API에서 사용)"""
        result = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            result.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
            })
        return result

    # =========================================================================
    # 스케줄 등록
    # =========================================================================

    def _register_jobs(self) -> None:
        """모든 수집 작업을 APScheduler에 등록합니다.

        cron 트리거 파라미터 설명:
          day_of_week = 요일 (mon/tue/wed/thu/fri/sat/sun)
          day         = 월의 날짜 (1~31)
          hour        = 시 (0~23)
          minute      = 분 (0~59)
          replace_existing=True = 서버 재시작 시 같은 id 작업이 있으면 덮어씁니다.
        """
        s = self.scheduler  # 짧은 별칭

        # -----------------------------------------------------------------------
        # 경주 결과 수집
        # 경주가 끝난 다음 영업일에 결과를 수집합니다.
        # 주말(토/일) 경기 → 월요일 14:00 / 월요일 경기 → 화요일 09:00
        # -----------------------------------------------------------------------
        s.add_job(self.collect_weekend_results,
                  "cron", day_of_week="mon", hour=14, minute=0,
                  id="collect_weekend_results", replace_existing=True)

        s.add_job(self.collect_monday_results,
                  "cron", day_of_week="tue", hour=9, minute=0,
                  id="collect_monday_results", replace_existing=True)

        # -----------------------------------------------------------------------
        # 출전표 수집
        # 경주 전 출전마/기수/부담중량 정보를 수집합니다.
        # -----------------------------------------------------------------------
        # 목요일 10:00 → 이번 주말 출전표 초안 수집
        s.add_job(self.collect_initial_weekend_entries,
                  "cron", day_of_week="thu", hour=10, minute=0,
                  id="collect_initial_weekend_entries", replace_existing=True)

        # 목요일 17:30 → 출전표 변경사항 업데이트 확인
        s.add_job(self.collect_updated_weekend_entries,
                  "cron", day_of_week="thu", hour=17, minute=30,
                  id="collect_updated_weekend_entries", replace_existing=True)

        # 금요일 08:00 → 출전표 확정본 수집
        s.add_job(self.collect_friday_final_entries,
                  "cron", day_of_week="fri", hour=8, minute=0,
                  id="collect_friday_final_entries", replace_existing=True)

        # -----------------------------------------------------------------------
        # 당일 정보 수집 (경주 당일 마체중/기수 변경/트랙 상태 업데이트)
        # 경마 당일 오전에 최신 정보로 업데이트합니다.
        # -----------------------------------------------------------------------
        for day, job_id in [("sat", "collect_saturday_updates"),
                             ("sun", "collect_sunday_updates"),
                             ("mon", "collect_monday_updates")]:
            s.add_job(self.collect_daily_info,
                      "cron", day_of_week=day, hour=9, minute=5,
                      id=job_id, replace_existing=True)

        # -----------------------------------------------------------------------
        # 마스터 데이터 수집
        # 경주마 목록, 기수, 조교사 정보처럼 자주 바뀌지 않는 기준 데이터입니다.
        # -----------------------------------------------------------------------
        # 매주 화요일 06:00 → 경주마 명단, 레이팅 최신화
        s.add_job(self.collect_weekly,
                  "cron", day_of_week="tue", hour=6, minute=0,
                  id="collect_weekly", replace_existing=True)

        # 매월 1일 05:00 → 기수/조교사/마필 전체 갱신
        s.add_job(self.collect_monthly,
                  "cron", day=1, hour=5, minute=0,
                  id="collect_monthly", replace_existing=True)

        # -----------------------------------------------------------------------
        # 날씨 수집
        # 기상청 단기예보(오늘~3일)와 중기예보(3~10일)를 수집합니다.
        # -----------------------------------------------------------------------
        # 매일 06:00 → 중기예보 수집 (기상청 첫 발표 직후)
        s.add_job(self.collect_weather_mid,
                  "cron", hour=6, minute=0,
                  id="weather_mid_morning", replace_existing=True)

        # 매일 06:30 → 단기예보 수집
        s.add_job(self.collect_weather_short,
                  "cron", hour=6, minute=30,
                  id="weather_short_morning", replace_existing=True)

        # 매일 18:30 → 단기예보 업데이트 (기상청 오후 발표분 반영)
        s.add_job(self.collect_weather_short,
                  "cron", hour=18, minute=30,
                  id="weather_short_evening", replace_existing=True)

        # -----------------------------------------------------------------------
        # AI 해설 자동 생성
        # 출전표 확정 후 금요일에 사전 해설, 결과 수집 후 월요일에 결과 해설 생성
        # -----------------------------------------------------------------------
        # 금요일 08:30 → 이번 주말 경주 사전 해설 자동 생성 (출전표 확정 30분 후)
        s.add_job(self.generate_all_pre_race_commentary,
                  "cron", day_of_week="fri", hour=8, minute=30,
                  id="ai_pre_commentary", replace_existing=True)

        # 월요일 14:30 → 주말 경주 결과 해설 자동 생성 (결과 수집 30분 후)
        s.add_job(self.generate_all_post_race_commentary,
                  "cron", day_of_week="mon", hour=14, minute=30,
                  id="ai_post_commentary", replace_existing=True)

        # -----------------------------------------------------------------------
        # 변경사항 감지 (Phase 3 신규)
        # 경마 당일(토/일/월) 09:00~17:00 사이 30분마다 실행합니다.
        # 기수변경/출전취소/조교사변경/장비변경/트랙급변 5종을 감지합니다.
        # -----------------------------------------------------------------------
        for day in ("sat", "sun", "mon"):
            s.add_job(
                self.run_change_detection,
                "cron",
                day_of_week=day,
                hour="9-17",    # 09:00~17:00 시간대에만 실행
                minute="*/30",  # 30분 간격 (0분, 30분마다)
                id=f"change_detection_{day}",
                replace_existing=True,
            )

        # -----------------------------------------------------------------------
        # Rate Limit 카운터 리셋
        # 매일 자정 00:00 → 어제의 API 호출 카운터를 초기화합니다.
        # Redis TTL로도 자동 리셋되지만, 확실하게 명시적으로 처리합니다.
        # -----------------------------------------------------------------------
        s.add_job(self.reset_daily_counter,
                  "cron", hour=0, minute=0,
                  id="reset_daily_counter", replace_existing=True)

        logger.info("[스케줄러] 작업 등록 완료: %d개", len(self.scheduler.get_jobs()))

    # =========================================================================
    # 공통 수집 실행 헬퍼
    # =========================================================================

    async def _run_with_guard(
        self,
        job_name: str,
        lock_ttl: int,
        coro_func,
        *args,
        **kwargs,
    ) -> None:
        """수집 작업을 안전하게 실행하는 공통 래퍼입니다.

        공통 패턴:
          1. 분산 락 획득 → 중복 실행 방지
          2. Rate Limit 확인 → 2,800콜 초과 시 건너뜀
          3. 실제 수집 실행
          4. 완료 후 체크포인트 저장
          5. 락 해제 (예외가 발생해도 반드시 해제)

        @param job_name  작업 이름 (락 키, 체크포인트 키로 사용)
        @param lock_ttl  락 최대 유지 시간(초). 작업 예상 소요 시간보다 넉넉하게 설정.
        @param coro_func 실행할 비동기 함수
        """
        # 1. 중복 실행 방지 락 획득
        # 락을 못 얻으면(이미 실행 중이면) 바로 종료합니다.
        if not await redis_svc.acquire_lock(job_name, ttl_seconds=lock_ttl):
            logger.info("[%s] 이미 실행 중이므로 건너뜁니다.", job_name)
            return

        try:
            # 2. Rate Limit 확인
            # 오늘 API 호출이 2,800회를 넘었으면 수집을 중단합니다.
            if await redis_svc.is_limit_reached():
                count = await redis_svc.get_daily_call_count()
                logger.warning(
                    "[%s] Rate Limit 도달(%d콜). 수집을 건너뜁니다.", job_name, count
                )
                return

            # 3. 실제 수집 실행
            logger.info("[%s] 수집 시작.", job_name)
            await coro_func(*args, **kwargs)

            # 4. 체크포인트 저장 (마지막 성공 시각)
            await redis_svc.set_checkpoint(job_name, datetime.now().isoformat())
            logger.info("[%s] 수집 완료.", job_name)

        except KRARateLimitExceededError:
            # Rate Limit 초과 시 로그만 남기고 종료합니다.
            logger.warning("[%s] Rate Limit 초과로 수집 중단.", job_name)
        except Exception as exc:
            # 예상치 못한 예외는 로그에 전체 스택 트레이스를 기록합니다.
            logger.exception("[%s] 수집 중 오류 발생: %s", job_name, exc)
        finally:
            # 5. 락 해제 (예외 발생 여부와 관계없이 반드시 실행)
            await redis_svc.release_lock(job_name)

    # =========================================================================
    # 경주 결과 수집
    # =========================================================================

    async def collect_weekend_results(self) -> None:
        """월요일 14:00 — 주말(토/일) 경주 결과를 수집합니다."""
        today = date.today()
        target_dates = [today - timedelta(days=2), today - timedelta(days=1)]
        await self._run_with_guard(
            "collect_weekend_results", 7200,
            self._collect_results_for_dates, target_dates
        )

    async def collect_monday_results(self) -> None:
        """화요일 09:00 — 월요일 경주 결과를 수집합니다."""
        target_dates = [date.today() - timedelta(days=1)]
        await self._run_with_guard(
            "collect_monday_results", 3600,
            self._collect_results_for_dates, target_dates
        )

    async def _collect_results_for_dates(self, target_dates: list[date]) -> None:
        """지정한 날짜들의 경주 결과를 3개 경마장 모두 수집합니다."""
        for target_date in target_dates:
            for meet_code in ALL_MEET_CODES:
                async with AsyncSessionLocal() as session:
                    kra = KRAApiService()
                    try:
                        await DataService(session, kra).collect_race_results(
                            meet_code=meet_code,
                            rc_date=target_date,
                        )
                    finally:
                        await kra.close()

    # =========================================================================
    # 출전표 수집
    # =========================================================================

    async def collect_initial_weekend_entries(self) -> None:
        """목요일 10:00 — 주말 출전표 초안을 수집합니다."""
        await self._run_with_guard(
            "collect_initial_entries", 7200,
            self._collect_entries_for_dates, self._get_upcoming_race_dates(days_ahead=4)
        )

    async def collect_updated_weekend_entries(self) -> None:
        """목요일 17:30 — 출전표 변경사항을 업데이트합니다."""
        await self._run_with_guard(
            "collect_updated_entries", 7200,
            self._collect_entries_for_dates, self._get_upcoming_race_dates(days_ahead=4)
        )

    async def collect_friday_final_entries(self) -> None:
        """금요일 08:00 — 출전표 확정본을 수집합니다."""
        await self._run_with_guard(
            "collect_friday_entries", 7200,
            self._collect_entries_for_dates, self._get_upcoming_race_dates(days_ahead=3)
        )

    async def collect_daily_info(self) -> None:
        """토/일/월 09:05 — 경주 당일 마체중, 기수 변경, 트랙 상태를 업데이트합니다."""
        await self._run_with_guard(
            "collect_daily_info", 3600,
            self._collect_daily_info_impl, date.today()
        )

    async def _collect_daily_info_impl(self, target_date: date) -> None:
        """출전 정보(마체중/기수 등) + 경주로 상태(함수율/날씨)를 함께 수집합니다."""
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                kra = KRAApiService()
                try:
                    ds = DataService(session, kra)
                    await ds.collect_entry_info(meet_code=meet_code, rc_date=target_date)
                    await ds.collect_track_conditions(meet_code=meet_code, rc_date=target_date)
                except KRARateLimitExceededError:
                    logger.warning("[당일 수집] Rate Limit 초과. meet=%s 수집 중단.", meet_code)
                    break
                except Exception as exc:
                    logger.error("[당일 수집] %s 오류: %s", meet_code, exc)
                finally:
                    await kra.close()

    async def _collect_entries_for_dates(self, target_dates: list[date]) -> None:
        """지정한 날짜들의 출전표를 3개 경마장 모두 수집합니다."""
        for target_date in target_dates:
            for meet_code in ALL_MEET_CODES:
                async with AsyncSessionLocal() as session:
                    kra = KRAApiService()
                    try:
                        await DataService(session, kra).collect_entry_info(
                            meet_code=meet_code,
                            rc_date=target_date,
                        )
                    finally:
                        await kra.close()

    # =========================================================================
    # 마스터 데이터 수집
    # =========================================================================

    async def collect_weekly(self) -> None:
        """매주 화요일 06:00 — 경주마 명단과 레이팅을 최신화합니다."""
        await self._run_with_guard(
            "collect_weekly", 7200,
            self._collect_weekly_master
        )

    async def collect_monthly(self) -> None:
        """매월 1일 05:00 — 기수/조교사/마필/진료 기록을 전체 갱신합니다."""
        await self._run_with_guard(
            "collect_monthly", 10800,
            self._collect_monthly_master
        )

    async def _collect_weekly_master(self) -> None:
        """주간 마스터 데이터(경주마 명단/레이팅)를 수집합니다."""
        today = date.today()
        rc_month = today.strftime("%Y%m")

        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                kra = KRAApiService()
                try:
                    await DataService(session, kra).collect_race_schedule(
                        meet_codes=[meet_code],
                        rc_year=today.year,
                        rc_month=rc_month,
                    )
                finally:
                    await kra.close()

    async def _collect_monthly_master(self) -> None:
        """월간 마스터 데이터(기수/조교사/마필 기본·성적·상세)를 경마장별로 전체 수집합니다."""
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                kra = KRAApiService()
                try:
                    ds = DataService(session, kra)

                    # 기수: 기본정보(jockeyInfo_1) + 성적(jockeyResult_1)
                    jockey_summary = await ds.collect_master_jockeys([meet_code])
                    logger.info(
                        "[월간 마스터] 기수 기본정보 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, jockey_summary.records_collected, jockey_summary.status,
                    )
                    jockey_result_summary = await ds.collect_jockey_results([meet_code])
                    logger.info(
                        "[월간 마스터] 기수 성적 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, jockey_result_summary.records_collected, jockey_result_summary.status,
                    )

                    # 조교사: 기본정보+승률 (trainerInfo_1 직접 제공)
                    trainer_summary = await ds.collect_master_trainers([meet_code])
                    logger.info(
                        "[월간 마스터] 조교사 수집 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, trainer_summary.records_collected, trainer_summary.status,
                    )

                    # 마필: 명단(racehorselist) + 성적(raceHorseResult_2) + 상세(raceHorseInfo_2)
                    horse_summary = await ds.collect_master_horses([meet_code])
                    logger.info(
                        "[월간 마스터] 마필 명단 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, horse_summary.records_collected, horse_summary.status,
                    )
                    horse_result_summary = await ds.collect_horse_results([meet_code])
                    logger.info(
                        "[월간 마스터] 마필 성적 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, horse_result_summary.records_collected, horse_result_summary.status,
                    )
                    horse_detail_summary = await ds.collect_horse_details([meet_code])
                    logger.info(
                        "[월간 마스터] 마필 상세 완료. meet=%s, 수집=%d건, 상태=%s",
                        meet_code, horse_detail_summary.records_collected, horse_detail_summary.status,
                    )
                except KRARateLimitExceededError:
                    logger.warning("[월간 마스터] Rate Limit 초과로 %s 수집 중단.", meet_code)
                    break
                except Exception as exc:
                    logger.exception("[월간 마스터] %s 수집 중 오류: %s", meet_code, exc)
                finally:
                    await kra.close()

    # =========================================================================
    # 날씨 수집
    # =========================================================================

    async def collect_weather_short(self) -> None:
        """매일 06:30, 18:30 — 3개 경마장 단기예보(오늘~3일 후)를 수집합니다."""
        await self._run_with_guard(
            "collect_weather_short", 1800,
            self._run_weather_short
        )

    async def collect_weather_mid(self) -> None:
        """매일 06:00 — 3개 경마장 중기예보(3~10일 후)를 수집합니다."""
        await self._run_with_guard(
            "collect_weather_mid", 1800,
            self._run_weather_mid
        )

    async def _run_weather_short(self) -> None:
        """단기예보를 3개 경마장 모두 수집합니다."""
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                svc = WeatherApiService(session)
                try:
                    data = await svc.fetch_short_term_forecast(meet_code)
                    await svc.save_forecast(meet_code, data)
                except Exception as exc:
                    logger.error("[단기예보] %s 수집 실패: %s", meet_code, exc)
                finally:
                    await svc.close()

    async def _run_weather_mid(self) -> None:
        """중기예보를 3개 경마장 모두 수집합니다."""
        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                svc = WeatherApiService(session)
                try:
                    data = await svc.fetch_mid_term_forecast(meet_code)
                    await svc.save_forecast(meet_code, data)
                except Exception as exc:
                    logger.error("[중기예보] %s 수집 실패: %s", meet_code, exc)
                finally:
                    await svc.close()

    # =========================================================================
    # Rate Limit 카운터 리셋
    # =========================================================================

    # =========================================================================
    # AI 해설 자동 생성
    # =========================================================================

    async def generate_all_pre_race_commentary(self) -> None:
        """금요일 08:30 — 이번 주말 예정 경주의 사전 해설을 GPT로 자동 생성합니다.

        출전표 확정(08:00) 30분 후에 실행하여 최신 출전마 정보를 반영합니다.
        """
        await self._run_with_guard(
            "ai_pre_commentary", 3600,
            self._run_pre_commentary
        )

    async def generate_all_post_race_commentary(self) -> None:
        """월요일 14:30 — 주말 경기 결과 해설을 GPT로 자동 생성합니다.

        결과 수집(14:00) 30분 후에 실행하여 최신 결과를 반영합니다.
        """
        await self._run_with_guard(
            "ai_post_commentary", 3600,
            self._run_post_commentary
        )

    async def _run_pre_commentary(self) -> None:
        """이번 주 토/일/월 경주의 사전 해설을 생성합니다."""
        from app.services.ai_commentary import AICommentaryService
        from app.models.race import Race, RaceStatusEnum
        from sqlalchemy import select, and_

        target_dates = self._get_upcoming_race_dates(days_ahead=3)

        for target_date in target_dates:
            async with AsyncSessionLocal() as session:
                # 해당 날짜의 예정 경주 ID 목록을 조회합니다.
                stmt = select(Race.id).where(
                    and_(
                        Race.rc_date == target_date,
                        Race.status == RaceStatusEnum.SCHEDULED,
                    )
                )
                race_ids = list((await session.scalars(stmt)).all())

                svc = AICommentaryService(session)
                for race_id in race_ids:
                    try:
                        await svc.generate_pre_race_commentary(race_id)
                        logger.info("[AI 해설] 사전 해설 생성. race_id=%d", race_id)
                    except Exception as exc:
                        logger.error("[AI 해설] 사전 해설 실패. race_id=%d: %s", race_id, exc)

    async def _run_post_commentary(self) -> None:
        """지난 주말 완료된 경주의 결과 해설을 생성합니다."""
        from app.services.ai_commentary import AICommentaryService
        from app.models.race import Race, RaceStatusEnum
        from sqlalchemy import select, and_

        today = date.today()
        # 월요일 기준으로 토/일/월 결과를 처리합니다.
        target_dates = [
            today - timedelta(days=2),  # 토요일
            today - timedelta(days=1),  # 일요일
            today,                      # 월요일
        ]

        for target_date in target_dates:
            async with AsyncSessionLocal() as session:
                stmt = select(Race.id).where(
                    and_(
                        Race.rc_date == target_date,
                        Race.status == RaceStatusEnum.COMPLETED,
                    )
                )
                race_ids = list((await session.scalars(stmt)).all())

                svc = AICommentaryService(session)
                for race_id in race_ids:
                    try:
                        await svc.generate_post_race_commentary(race_id)
                        logger.info("[AI 해설] 결과 해설 생성. race_id=%d", race_id)
                    except Exception as exc:
                        logger.error("[AI 해설] 결과 해설 실패. race_id=%d: %s", race_id, exc)

    async def run_change_detection(self) -> None:
        """
        경마 당일 30분마다 — 변경사항 5종을 감지합니다. (Phase 3 신규)

        감지 항목:
          🔴 기수변경 / ⚫ 출전취소 / 🟠 조교사변경 / 🟡 장비변경 / 🔵 트랙급변

        분산 락으로 동시 실행을 막습니다.
        """
        await self._run_with_guard(
            "change_detection",
            lock_ttl=1800,  # 최대 30분 실행 허용 (다음 실행 전까지)
            coro_func=self._run_change_detection_impl,
        )

    async def _run_change_detection_impl(self) -> None:
        """변경감지 실제 구현 — ChangeDetector를 호출합니다."""
        from app.services.change_detector import ChangeDetector

        today = date.today().strftime("%Y%m%d")
        total_changes = 0

        for meet_code in ALL_MEET_CODES:
            async with AsyncSessionLocal() as session:
                kra = KRAApiService()
                try:
                    detector = ChangeDetector(session, kra)
                    changes = await detector.detect_all(rc_date=today)
                    total_changes += len(changes)
                except Exception as exc:
                    logger.error("[변경감지] %s 처리 오류: %s", meet_code, exc)
                finally:
                    await kra.close()

        logger.info("[변경감지] 오늘(%s) 총 %d건 감지", today, total_changes)

    async def reset_daily_counter(self) -> None:
        """매일 00:00 — 마사회 API 호출 카운터를 0으로 초기화합니다."""
        try:
            await redis_svc.reset_daily_counter()
            logger.info("[Rate Limit] 일일 카운터 자정 리셋 완료.")
        except Exception as exc:
            logger.error("[Rate Limit] 카운터 리셋 실패: %s", exc)

    # =========================================================================
    # 유틸리티
    # =========================================================================

    @staticmethod
    def _get_upcoming_race_dates(days_ahead: int) -> list[date]:
        """오늘부터 n일 후까지의 날짜 목록을 반환합니다.

        실제 경주가 없는 날은 API가 빈 결과를 주므로 걱정 없이 전체 범위를 수집합니다.
        """
        base = date.today()
        return [base + timedelta(days=i) for i in range(days_ahead + 1)]
