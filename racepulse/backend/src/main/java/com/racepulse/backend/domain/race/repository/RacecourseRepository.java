package com.racepulse.backend.domain.race.repository;

import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.domain.race.entity.Racecourse;

// =============================================================================
// RacecourseRepository.java — racecourses 테이블 기본 조회 창구
// =============================================================================
// JpaRepository를 상속하면 findAll, findById 같은 기본 메서드를
// 직접 구현하지 않아도 바로 사용할 수 있습니다.
// =============================================================================

public interface RacecourseRepository extends JpaRepository<Racecourse, Long> {

    // meetCode는 화면 URL에서 사용하는 공개 코드라서 ID를 몰라도 경마장 1건을 찾을 수 있게 합니다.
    Optional<Racecourse> findByMeetCode(MeetCode meetCode);
}
