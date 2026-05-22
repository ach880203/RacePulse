package com.racepulse.backend.domain.privacy.controller;

// =============================================================================
// PrivacyController.java — 개인정보처리방침/이용약관 공개 조회 API
// =============================================================================
// 두 문서는 로그인 전 회원가입 화면에서도 보여야 하므로 SecurityConfig에서 GET 공개 경로로 허용합니다.
// 응답은 프로젝트 공통 규칙에 따라 ApiResponse로 감싸서 내려줍니다.
// =============================================================================

import com.racepulse.backend.domain.privacy.dto.PolicyDocumentResponse;
import com.racepulse.backend.domain.privacy.service.PolicyDocumentService;
import com.racepulse.backend.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1")
public class PrivacyController {

    private final PolicyDocumentService policyDocumentService;

    @GetMapping("/privacy")
    public ResponseEntity<ApiResponse<PolicyDocumentResponse>> getPrivacy() {
        return ResponseEntity.ok(ApiResponse.success(
                policyDocumentService.getPrivacy(),
                "개인정보처리방침 조회 성공"
        ));
    }

    @GetMapping("/terms")
    public ResponseEntity<ApiResponse<PolicyDocumentResponse>> getTerms() {
        return ResponseEntity.ok(ApiResponse.success(
                policyDocumentService.getTerms(),
                "이용약관 조회 성공"
        ));
    }
}
