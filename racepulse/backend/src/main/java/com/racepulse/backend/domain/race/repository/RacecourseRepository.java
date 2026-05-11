package com.racepulse.backend.domain.race.repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.racepulse.backend.domain.race.entity.Racecourse;

// =============================================================================
// RacecourseRepository.java — racecourses 테이블 기본 조회 창구
// =============================================================================
// JpaRepository를 상속하면 findAll, findById 같은 기본 메서드를
// 직접 구현하지 않아도 바로 사용할 수 있습니다.
// =============================================================================

public interface RacecourseRepository extends JpaRepository<Racecourse, Long> {
}
