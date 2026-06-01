package com.racepulse.backend.domain.horse.service;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.racepulse.backend.domain.horse.dto.HorseResponse;
import com.racepulse.backend.domain.horse.entity.Horse;
import com.racepulse.backend.domain.horse.repository.HorseRepository;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;

import lombok.RequiredArgsConstructor;

// =============================================================================
// HorseService.java — 경주마 목록 조회 로직
// =============================================================================
// 이름 검색은 "완전 일치"보다 "포함 검색"이 실사용에 편합니다.
// 그래서 SQL의 like 조건과 소문자 변환을 함께 써 대소문자 차이도 줄였습니다.
// =============================================================================

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class HorseService {

    private final HorseRepository horseRepository;

    public Page<HorseResponse> getHorses(MeetCode meetCode, String name, Pageable pageable) {
        // 항상 참인 기본 조건에서 시작하면 deprecated 된 where(null)을 피하면서도
        // 뒤에 선택 필터를 자연스럽게 and로 이어붙일 수 있습니다.
        Specification<Horse> specification = (root, query, criteriaBuilder) -> criteriaBuilder.conjunction();

        if (meetCode != null) {
            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.equal(root.get("meetCode"), meetCode));
        }

        if (name != null && !name.isBlank()) {
            String keyword = "%" + name.trim().toLowerCase() + "%";

            specification = specification.and((root, query, criteriaBuilder) ->
                    criteriaBuilder.like(criteriaBuilder.lower(root.get("name")), keyword));
        }

        return horseRepository.findAll(specification, pageable)
                .map(HorseResponse::from);
    }

    /** 경주마 ID로 단건 조회합니다. 없으면 404 예외를 던집니다. */
    public HorseResponse getHorseById(Long horseId) {
        Horse horse = horseRepository.findById(horseId)
                .orElseThrow(() -> new BusinessException(ErrorCode.HORSE_NOT_FOUND));
        return HorseResponse.from(horse);
    }
}
