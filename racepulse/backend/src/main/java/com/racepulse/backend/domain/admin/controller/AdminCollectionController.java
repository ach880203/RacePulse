package com.racepulse.backend.domain.admin.controller;

import com.racepulse.backend.domain.admin.service.AdminCollectionService;
import com.racepulse.backend.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

// =============================================================================
// AdminCollectionController.java — 관리자 수동 수집 API
// =============================================================================
// 관리자 화면은 Spring Boot만 호출하고, Spring Boot가 내부적으로 FastAPI 수집 작업을 시작합니다.
// =============================================================================

@RestController
@RequestMapping("/api/v1/admin/collection/trigger")
@RequiredArgsConstructor
public class AdminCollectionController {

    private final AdminCollectionService adminCollectionService;

    @PreAuthorize("hasRole('ADMIN')")
    @PostMapping("/entries")
    public ResponseEntity<ApiResponse<AdminCollectionService.TriggerResponse>> triggerEntriesCollection() {
        // 출전표 수집은 오래 걸릴 수 있어 시작 요청만 받고 202로 즉시 응답합니다.
        return ResponseEntity
                .status(HttpStatus.ACCEPTED)
                .body(ApiResponse.success(
                        adminCollectionService.triggerEntriesCollection(),
                        "출전표 수집이 시작되었습니다."
                ));
    }

    @PreAuthorize("hasRole('ADMIN')")
    @PostMapping("/results")
    public ResponseEntity<ApiResponse<AdminCollectionService.TriggerResponse>> triggerResultsCollection() {
        // 경기 결과 수집도 백그라운드에서 진행해 관리자 화면이 응답 대기로 멈추지 않게 합니다.
        return ResponseEntity
                .status(HttpStatus.ACCEPTED)
                .body(ApiResponse.success(
                        adminCollectionService.triggerResultsCollection(),
                        "경기 결과 수집이 시작되었습니다."
                ));
    }

    @PreAuthorize("hasRole('ADMIN')")
    @GetMapping("/status")
    public ResponseEntity<ApiResponse<AdminCollectionService.CollectionStatusResponse>> getCollectionStatus() {
        // 상태 조회는 관리자 화면의 자동 새로고침이 쓰므로 가볍게 최신 로그만 반환합니다.
        return ResponseEntity.ok(ApiResponse.success(
                adminCollectionService.getCollectionStatus(),
                "수집 상태 조회 성공"
        ));
    }
}
