package com.racepulse.backend.domain.jockey.controller;

import com.racepulse.backend.domain.jockey.dto.JockeyResponse;
import com.racepulse.backend.domain.jockey.service.JockeyService;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.response.PageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Jockeys", description = "기수 조회 API")
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/jockeys")
public class JockeyController {

    private final JockeyService jockeyService;

    @Operation(summary = "기수 목록 조회", description = "경마장 코드와 이름 검색 조건으로 기수 목록을 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<PageResponse<JockeyResponse>>> getJockeys(
            @RequestParam(required = false) String meetCode,
            @RequestParam(required = false) String name,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) int size
    ) {
        PageRequest pageRequest = PageRequest.of(
                page,
                size,
                Sort.by(Sort.Order.asc("name"), Sort.Order.asc("id"))
        );

        PageResponse<JockeyResponse> response = PageResponse.from(
                jockeyService.getJockeys(meetCode, name, pageRequest)
        );

        return ResponseEntity.ok(ApiResponse.success(response, "조회 성공"));
    }

    @Operation(summary = "기수 상세 조회", description = "기수 ID로 1명의 상세 정보를 조회합니다.")
    @GetMapping("/{jockeyId}")
    public ResponseEntity<ApiResponse<JockeyResponse>> getJockey(
            @PathVariable Long jockeyId
    ) {
        return ResponseEntity.ok(ApiResponse.success(jockeyService.getJockey(jockeyId), "조회 성공"));
    }
}
