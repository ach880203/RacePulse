package com.racepulse.backend.domain.change.controller;

import java.util.UUID;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.change.dto.ChangeResponse;
import com.racepulse.backend.domain.change.dto.ChangeSubscribeRequest;
import com.racepulse.backend.domain.change.service.ChangeService;
import com.racepulse.backend.global.response.ApiResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;

// =============================================================================
// ChangeController.java — 경주 변경 감지 API 엔드포인트
// =============================================================================
// GET API는 공개 조회이고, POST 구독 API는 SecurityConfig의 기본 규칙에 따라 인증이 필요합니다.
// 경로 기준은 기존 RaceController와 맞추기 위해 /api/v1/races 아래에 둡니다.
// =============================================================================

@Tag(name = "Changes", description = "변경 감지 API")
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/races")
public class ChangeController {

    private final ChangeService changeService;

    @Operation(summary = "경주 변경 이력 조회", description = "특정 경주의 조교사/장비 변경 이력을 조회합니다.")
    @GetMapping("/{raceId}/changes")
    public ResponseEntity<ApiResponse<ChangeResponse.RaceChanges>> getRaceChanges(
            @PathVariable Long raceId
    ) {
        return ResponseEntity.ok(ApiResponse.success(changeService.getRaceChanges(raceId), "변경 이력 조회 성공"));
    }

    @Operation(summary = "오늘 변경 감지 요약 조회", description = "오늘 감지된 전체 조교사/장비 변경 이력을 조회합니다.")
    @GetMapping("/changes/today")
    public ResponseEntity<ApiResponse<ChangeResponse.TodayChanges>> getTodayChanges() {
        return ResponseEntity.ok(ApiResponse.success(changeService.getTodayChanges(), "오늘 변경 감지 조회 성공"));
    }

    @Operation(summary = "경주 변경 알림 구독", description = "특정 경주의 변경 알림 구독 상태를 설정합니다.")
    @PostMapping("/{raceId}/changes/subscribe")
    public ResponseEntity<ApiResponse<ChangeResponse.SubscribeResult>> subscribeToRaceChanges(
            @AuthenticationPrincipal UUID userId,
            @PathVariable Long raceId,
            @Valid @RequestBody ChangeSubscribeRequest request
    ) {
        return ResponseEntity.ok(ApiResponse.success(
                changeService.subscribeToRaceChanges(userId, raceId, request.subscribe()),
                "변경 알림 구독 상태가 저장되었습니다."
        ));
    }
}
