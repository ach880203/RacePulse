package com.racepulse.backend.domain.race.controller;

import java.util.List;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.race.dto.RacecourseResponse;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.domain.race.service.RacecourseService;
import com.racepulse.backend.global.response.ApiResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

// =============================================================================
// RacecourseController.java — /api/v1/racecourses 엔드포인트
// =============================================================================
// 컨트롤러는 "HTTP 요청을 받아 서비스 호출 후 JSON 응답 반환" 역할에 집중합니다.
// =============================================================================

@Tag(name = "Racecourses", description = "경마장 조회 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/racecourses")
public class RacecourseController {

    private final RacecourseService racecourseService;

    @Operation(summary = "경마장 전체 목록 조회", description = "서울/부산경남/제주 경마장 목록을 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<List<RacecourseResponse>>> getRacecourses() {
        return ResponseEntity.ok(
                ApiResponse.success(racecourseService.getRacecourses(), "조회 성공")
        );
    }

    @Operation(summary = "경마장 단건 조회", description = "경마장 코드(SC/BU/JJ)로 경마장 상세 정보를 조회합니다.")
    @GetMapping("/{meetCode}")
    public ResponseEntity<ApiResponse<RacecourseResponse>> getRacecourse(
            @PathVariable MeetCode meetCode
    ) {
        return ResponseEntity.ok(
                ApiResponse.success(racecourseService.getRacecourse(meetCode), "조회 성공")
        );
    }
}
