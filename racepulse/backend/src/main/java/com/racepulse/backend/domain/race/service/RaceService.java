package com.racepulse.backend.domain.race.service;

import java.time.LocalDate;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.racepulse.backend.domain.race.dto.RaceResponse;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.domain.race.entity.Race;
import com.racepulse.backend.domain.race.entity.RaceStatus;
import com.racepulse.backend.domain.race.repository.RaceRepository;

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
}
