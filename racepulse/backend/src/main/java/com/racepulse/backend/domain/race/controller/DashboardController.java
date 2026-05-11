package com.racepulse.backend.domain.race.controller;

// =============================================================================
// DashboardController.java — 대시보드 정확도 통계 API
// =============================================================================

import com.racepulse.backend.domain.race.dto.AccuracyStatsDto;
import com.racepulse.backend.domain.race.service.DashboardService;
import com.racepulse.backend.global.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Tag(name = "Dashboard", description = "ML 예측 정확도 대시보드 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    @Operation(
        summary = "예측 정확도 통계 조회",
        description = "ML 모델의 누적 예측 정확도와 월별 추이를 반환합니다. " +
                      "예측 데이터가 없는 경우 데모 데이터를 반환합니다."
    )
    @GetMapping("/accuracy")
    public ResponseEntity<ApiResponse<AccuracyStatsDto>> getAccuracyStats() {
        AccuracyStatsDto stats = dashboardService.getAccuracyStats();
        return ResponseEntity.ok(ApiResponse.success(stats, "정확도 통계 조회 성공"));
    }
}
