package com.racepulse.backend.domain.race.service;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.racepulse.backend.domain.race.dto.RaceResponse;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.domain.race.entity.Race;
import com.racepulse.backend.domain.race.entity.RaceStatus;
import com.racepulse.backend.domain.race.repository.RaceRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;

import lombok.RequiredArgsConstructor;

// =============================================================================
// RaceService.java — 경주 목록 조회 로직
// =============================================================================
// 조건이 선택 입력인 검색 API는 "조건이 있으면 where 추가, 없으면 생략"이 핵심입니다.
// Specification은 이 조건 조립을 깔끔하게 처리할 수 있어 초보자도 흐름을 읽기 좋습니다.
// =============================================================================

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class RaceService {

    private final RaceRepository raceRepository;
    // JdbcTemplate = JPA 엔티티 없이 SQL을 직접 실행해 결과를 Map 목록으로 받습니다.
    // race_entries/race_results 테이블은 ML 서버가 관리하므로 JPA 엔티티 없이 조회합니다.
    private final JdbcTemplate jdbcTemplate;

    // 전달받은 필터 조건으로 경주 목록을 페이지 단위로 조회합니다.
    public Page<RaceResponse> getRaces(MeetCode meetCode, LocalDate rcDate, RaceStatus status, Pageable pageable) {
        // conjunction() = "일단 항상 참인 조건"으로 시작한 뒤,
        // 필요한 필터가 들어올 때마다 and 조건을 덧붙이는 방식입니다.
        Specification<Race> specification = (root, query, criteriaBuilder) -> criteriaBuilder.conjunction();

        if (meetCode != null) {
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.equal(root.get("meetCode"), meetCode));
        }

        if (rcDate != null) {
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.equal(root.get("rcDate"), rcDate));
        }

        if (status != null) {
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.equal(root.get("status"), status));
        }

        return raceRepository.findAll(specification, pageable)
                .map(RaceResponse::from);
    }

    /**
     * 오늘 이후 예정 경주를 최대 20건 조회합니다.
     *
     * 컨트롤러에서 날짜 조건을 만들지 않고 서비스에서 처리하는 이유는, "오늘" 기준이 바뀌어도
     * API 호출자는 같은 URL만 호출하면 되고 조회 규칙은 한 곳에서만 관리되기 때문입니다.
     */
    public List<RaceResponse> getUpcomingRaces() {
        return raceRepository.findByRcDateGreaterThanEqualAndStatusOrderByRcDateAscStartTimeAscRaceNoAsc(
                        LocalDate.now(),
                        RaceStatus.SCHEDULED,
                        PageRequest.of(0, 20)
                )
                .stream()
                .map(RaceResponse::from)
                .toList();
    }

    /**
     * 최근 완료 경주를 최대 20건 조회합니다.
     *
     * 완료 경주가 없을 수도 있으므로 빈 목록을 정상 응답으로 돌려주며,
     * 데이터가 없다는 이유로 500이 발생하지 않도록 예외를 던지지 않습니다.
     */
    public List<RaceResponse> getRecentResults() {
        return raceRepository.findByStatusOrderByRcDateDescRaceNoDesc(
                        RaceStatus.COMPLETED,
                        PageRequest.of(0, 20)
                )
                .stream()
                .map(RaceResponse::from)
                .toList();
    }

    // =========================================================================
    // 코드 리뷰 #1: 누락된 단건 / 출전 / 결과 조회 메서드 추가
    // =========================================================================

    /** 경주 ID로 단건 조회합니다. 없으면 404 예외를 던집니다. */
    public RaceResponse getRaceById(Long raceId) {
        Race race = raceRepository.findById(raceId)
                .orElseThrow(() -> new BusinessException(ErrorCode.RACE_NOT_FOUND));
        return RaceResponse.from(race);
    }

    /**
     * 특정 경주의 출전 명단을 조회합니다.
     *
     * race_entries 테이블을 JdbcTemplate으로 직접 조회해
     * horses / jockeys / trainers 와 JOIN 합니다.
     */
    public List<Map<String, Object>> getRaceEntries(Long raceId) {
        // raceRepository.existsById 로 먼저 경주 존재 여부를 확인합니다.
        if (!raceRepository.existsById(raceId)) {
            throw new BusinessException(ErrorCode.RACE_NOT_FOUND);
        }

        // PostgreSQL은 따옴표 없는 별칭을 소문자로 변환합니다.
        // FE가 camelCase(horseName, gateNo 등)를 기대하므로 큰따옴표로 대소문자를 보존합니다.
        return jdbcTemplate.queryForList(
                """
                SELECT
                    re.id                  AS "id",
                    re.race_id             AS "raceId",
                    re.horse_id            AS "horseId",
                    h.name                 AS "horseName",
                    h.eng_name             AS "horseEngName",
                    re.gate_no             AS "gateNo",
                    re.jockey_id           AS "jockeyId",
                    j.name                 AS "jockeyName",
                    re.trainer_id          AS "trainerId",
                    t.name                 AS "trainerName",
                    re.horse_weight        AS "weight",
                    re.burden_weight       AS "burden",
                    re.odds_win            AS "odds",
                    re.data_status         AS "dataStatus"
                FROM race_entries re
                LEFT JOIN horses   h ON h.id = re.horse_id
                LEFT JOIN jockeys  j ON j.id = re.jockey_id
                LEFT JOIN trainers t ON t.id = re.trainer_id
                WHERE re.race_id = ?
                ORDER BY re.gate_no
                """,
                raceId
        );
    }

    /**
     * 특정 경주의 결과를 조회합니다.
     *
     * race_results 테이블을 JdbcTemplate으로 직접 조회합니다.
     * V9 마이그레이션 기준 컬럼명: rank, record_time, margin, final_odds, horse_id
     */
    public List<Map<String, Object>> getRaceResult(Long raceId) {
        // @NonNull 경고 방지: raceId가 null이면 404로 처리합니다.
        if (raceId == null || !raceRepository.existsById(raceId)) {
            throw new BusinessException(ErrorCode.RACE_NOT_FOUND);
        }

        // PostgreSQL camelCase 보존을 위해 큰따옴표로 별칭을 감쌉니다.
        return jdbcTemplate.queryForList(
                """
                SELECT
                    rr.id                  AS "id",
                    rr.race_id             AS "raceId",
                    rr.horse_id            AS "horseId",
                    h.name                 AS "horseName",
                    re.gate_no             AS "gateNo",
                    rr.rank                AS "finishOrder",
                    rr.record_time         AS "finishTime",
                    rr.final_odds          AS "finalOdds",
                    j.name                 AS "jockeyName"
                FROM race_results rr
                LEFT JOIN horses       h  ON h.id  = rr.horse_id
                LEFT JOIN race_entries re ON re.id = rr.race_entry_id
                LEFT JOIN jockeys      j  ON j.id  = re.jockey_id
                WHERE rr.race_id = ?
                ORDER BY rr.rank NULLS LAST
                """,
                raceId
        );
    }
}
