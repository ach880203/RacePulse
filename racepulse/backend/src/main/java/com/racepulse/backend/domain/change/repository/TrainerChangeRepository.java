package com.racepulse.backend.domain.change.repository;

import java.time.LocalDate;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.racepulse.backend.domain.change.entity.TrainerChange;

// =============================================================================
// TrainerChangeRepository.java — 조교사 변경 이력 조회 창구
// =============================================================================
// Spring Data JPA는 메서드 이름을 읽어 WHERE 조건을 자동으로 만들어 줍니다.
// findByRaceId는 TrainerChange.race.id 값을 기준으로 조회한다는 뜻입니다.
// =============================================================================

public interface TrainerChangeRepository extends JpaRepository<TrainerChange, Long> {

    List<TrainerChange> findByRaceIdOrderByDetectedAtDesc(Long raceId);

    List<TrainerChange> findByChangeDateOrderByDetectedAtDesc(LocalDate changeDate);
}
