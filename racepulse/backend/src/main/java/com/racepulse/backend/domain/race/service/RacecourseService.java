package com.racepulse.backend.domain.race.service;

import java.util.List;

import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.racepulse.backend.domain.race.dto.RacecourseResponse;
import com.racepulse.backend.domain.race.repository.RacecourseRepository;

import lombok.RequiredArgsConstructor;

// =============================================================================
// RacecourseService.java — 경마장 조회 비즈니스 로직
// =============================================================================
// Service 계층을 두는 이유:
// 컨트롤러는 HTTP 요청/응답에 집중하고,
// 실제 조회 규칙은 서비스에서 관리해 역할을 분리하기 위해서입니다.
// =============================================================================

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class RacecourseService {

    private final RacecourseRepository racecourseRepository;

    // 경마장 전체 목록을 id 순서로 읽어 응답 DTO로 변환합니다.
    public List<RacecourseResponse> getRacecourses() {
        return racecourseRepository.findAll(Sort.by(Sort.Direction.ASC, "id"))
                .stream()
                .map(RacecourseResponse::from)
                .toList();
    }
}
