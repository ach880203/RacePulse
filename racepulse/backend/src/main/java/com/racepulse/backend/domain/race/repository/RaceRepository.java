package com.racepulse.backend.domain.race.repository;

import java.time.LocalDate;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.racepulse.backend.domain.race.entity.Race;
import com.racepulse.backend.domain.race.entity.RaceStatus;

// JpaSpecificationExecutor = 조건이 선택적으로 붙는 검색 화면을 만들 때 유용합니다.
// 이번 경주 목록 API처럼 meetCode, rcDate, status가 "있을 수도 없을 수도" 있을 때 적합합니다.
public interface RaceRepository extends JpaRepository<Race, Long>, JpaSpecificationExecutor<Race> {

    // 홈/목록 화면은 가장 가까운 예정 경주만 필요하므로 DB에서 정렬과 개수 제한을 함께 처리합니다.
    List<Race> findByRcDateGreaterThanEqualAndStatusOrderByRcDateAscStartTimeAscRaceNoAsc(
            LocalDate rcDate,
            RaceStatus status,
            Pageable pageable
    );

    // 결과 화면은 최근 완료 경주를 먼저 보여줘야 하므로 날짜와 경주 번호를 내림차순으로 정렬합니다.
    List<Race> findByStatusOrderByRcDateDescRaceNoDesc(RaceStatus status, Pageable pageable);
}
