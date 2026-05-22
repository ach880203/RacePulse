package com.racepulse.backend.domain.change.repository;

import java.time.LocalDate;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;

import com.racepulse.backend.domain.change.entity.EquipmentChange;

// =============================================================================
// EquipmentChangeRepository.java — 장비 변경 이력 조회 창구
// =============================================================================
// API 서비스는 Repository만 호출하고 SQL 세부 내용은 Spring Data JPA에 맡깁니다.
// 이렇게 두면 컨트롤러와 서비스 코드가 DB 접근 방식에 덜 묶입니다.
// =============================================================================

public interface EquipmentChangeRepository extends JpaRepository<EquipmentChange, Long> {

    List<EquipmentChange> findByRaceIdOrderByDetectedAtDesc(Long raceId);

    List<EquipmentChange> findByChangeDateOrderByDetectedAtDesc(LocalDate changeDate);
}
