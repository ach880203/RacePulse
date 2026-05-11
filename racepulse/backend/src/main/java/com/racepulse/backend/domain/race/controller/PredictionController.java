package com.racepulse.backend.domain.race.controller;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.race.dto.PredictionResponse;
import com.racepulse.backend.domain.race.dto.SimulationResponse;
import com.racepulse.backend.domain.race.service.PredictionService;
import com.racepulse.backend.global.response.ApiResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;

// =============================================================================
// PredictionController.java — /api/v1/predictions 예측 결과 조회 엔드포인트
// =============================================================================
// 프런트는 이 컨트롤러만 호출하면 되도록 하고,
// ML 서버/DB 조합 로직은 서비스 계층에 숨겨서 화면 코드가 단순해지도록 분리합니다.
// =============================================================================

@Tag(name = "Predictions", description = "경주 예측 결과 조회 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/predictions")
public class PredictionController {

    private final PredictionService predictionService;

    @Operation(summary = "경주 예측 결과 조회", description = "특정 경주의 AI 예측 결과를 말별 카드 목록 형태로 조회합니다.")
    @GetMapping("/{raceId}")
    public ResponseEntity<ApiResponse<PredictionResponse>> getPrediction(
            @PathVariable Long raceId
    ) {
        PredictionResponse response = predictionService.getPrediction(raceId);
        return ResponseEntity.ok(ApiResponse.success(response, "조회 성공"));
    }
    @Operation(summary = "몬테카를로 시뮬레이션 결과 조회", description = "ML 서버의 시뮬레이션 결과를 Spring API 형식으로 전달합니다.")
    @GetMapping("/{raceId}/simulation")
    public ResponseEntity<ApiResponse<SimulationResponse>> getSimulation(
            @PathVariable Long raceId
    ) {
        SimulationResponse response = predictionService.getSimulation(raceId);
        return ResponseEntity.ok(ApiResponse.success(response, "시뮬레이션 조회 성공"));
    }
}
