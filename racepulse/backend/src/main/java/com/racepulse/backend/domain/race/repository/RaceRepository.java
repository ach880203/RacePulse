package com.racepulse.backend.domain.race.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.JpaSpecificationExecutor;

import com.racepulse.backend.domain.race.entity.Race;

// JpaSpecificationExecutor = 조건이 선택적으로 붙는 검색 화면을 만들 때 유용합니다.
// 이번 경주 목록 API처럼 meetCode, rcDate, status가 "있을 수도 없을 수도" 있을 때 적합합니다.
public interface RaceRepository extends JpaRepository<Race, Long>, JpaSpecificationExecutor<Race> {
}
