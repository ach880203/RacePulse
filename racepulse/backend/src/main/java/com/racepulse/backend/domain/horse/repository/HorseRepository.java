package com.racepulse.backend.domain.horse.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.racepulse.backend.domain.horse.entity.Horse;

// 경주마 목록 API도 조건 검색이 필요하므로 Specification 기반 조회를 함께 엽니다.
public interface HorseRepository extends JpaRepository<Horse, Long>, JpaSpecificationExecutor<Horse> {
}
