package com.racepulse.backend.domain.race.controller;

import java.time.LocalDate;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.race.dto.RaceResponse;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.domain.race.entity.RaceStatus;
import com.racepulse.backend.domain.race.service.RaceService;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.response.PageResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;

// =============================================================================
// RaceController.java — /api/v1/races 엔드포인트
// =============================================================================
// @Validated = @Min 같은 검증 어노테이션을 실제로 동작시키기 위해 필요합니다.
// =============================================================================

@Tag(name = "Races", description = "경주 조회 API")
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/races")
public class RaceController {

    private final RaceService raceService;

    @Operation(summary = "경주 목록 조회", description = "경마장/날짜/상태 조건으로 경주 목록을 페이지 단위 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<PageResponse<RaceResponse>>> getRaces(
            @RequestParam(required = false) MeetCode meetCode,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) LocalDate rcDate,
            @RequestParam(required = false) RaceStatus status,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) int size
    ) {
        // Sort = DB에서 어떤 순서로 가져올지 지정하는 객체입니다.
        // 같은 날짜 안에서는 raceNo 오름차순으로 보이게 해 목록 가독성을 높였습니다.
        PageRequest pageRequest = PageRequest.of(
                page,
                size,
                Sort.by(Sort.Order.desc("rcDate"), Sort.Order.asc("raceNo"))
        );

        PageResponse<RaceResponse> response = PageResponse.from(
                raceService.getRaces(meetCode, rcDate, status, pageRequest)
        );

        return ResponseEntity.ok(ApiResponse.success(response, "조회 성공"));
    }
}
