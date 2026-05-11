package com.racepulse.backend.domain.horse.controller;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.horse.dto.HorseResponse;
import com.racepulse.backend.domain.horse.service.HorseService;
import com.racepulse.backend.domain.race.entity.MeetCode;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.response.PageResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;

// 경주마 목록 조회 컨트롤러입니다.
@Tag(name = "Horses", description = "경주마 조회 API")
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/horses")
public class HorseController {

    private final HorseService horseService;

    @Operation(summary = "경주마 목록 조회", description = "경마장 코드와 이름 포함 검색 조건으로 경주마 목록을 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<PageResponse<HorseResponse>>> getHorses(
            @RequestParam(required = false) MeetCode meetCode,
            @RequestParam(required = false) String name,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) int size
    ) {
        PageRequest pageRequest = PageRequest.of(
                page,
                size,
                Sort.by(Sort.Order.asc("name"), Sort.Order.asc("id"))
        );

        PageResponse<HorseResponse> response = PageResponse.from(
                horseService.getHorses(meetCode, name, pageRequest)
        );

        return ResponseEntity.ok(ApiResponse.success(response, "조회 성공"));
    }
}
