package com.racepulse.backend.domain.user.controller;

import com.racepulse.backend.domain.user.dto.FavoriteRequest;
import com.racepulse.backend.domain.user.dto.FavoriteResponse;
import com.racepulse.backend.domain.user.dto.PreferenceRequest;
import com.racepulse.backend.domain.user.dto.PreferenceResponse;
import com.racepulse.backend.domain.privacy.dto.ConsentRequest;
import com.racepulse.backend.domain.privacy.dto.ConsentResponse;
import com.racepulse.backend.domain.privacy.service.UserConsentService;
import com.racepulse.backend.domain.user.service.UserPageService;
import com.racepulse.backend.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/user")
public class UserController {

    private final UserPageService userPageService;
    private final UserConsentService userConsentService;

    @GetMapping("/favorites")
    public ResponseEntity<ApiResponse<List<FavoriteResponse>>> getFavorites(@AuthenticationPrincipal UUID userId) {
        return ResponseEntity.ok(ApiResponse.success(userPageService.getFavorites(userId), "즐겨찾기 조회 성공"));
    }

    @PostMapping("/favorites")
    public ResponseEntity<ApiResponse<FavoriteResponse>> addFavorite(@AuthenticationPrincipal UUID userId, @RequestBody FavoriteRequest request) {
        return ResponseEntity.ok(ApiResponse.success(userPageService.addFavorite(userId, request), "즐겨찾기 추가 성공"));
    }

    @DeleteMapping("/favorites/{id}")
    public ResponseEntity<ApiResponse<Void>> deleteFavorite(@AuthenticationPrincipal UUID userId, @PathVariable Long id) {
        userPageService.deleteFavorite(userId, id);
        return ResponseEntity.ok(ApiResponse.success(null, "즐겨찾기 해제 성공"));
    }

    @GetMapping("/history")
    public ResponseEntity<ApiResponse<List<String>>> getHistory() {
        return ResponseEntity.ok(ApiResponse.success(List.of(), "조회 이력 조회 성공"));
    }

    @GetMapping("/preferences")
    public ResponseEntity<ApiResponse<PreferenceResponse>> getPreferences(@AuthenticationPrincipal UUID userId) {
        return ResponseEntity.ok(ApiResponse.success(userPageService.getPreferences(userId), "설정 조회 성공"));
    }

    @PatchMapping("/preferences")
    public ResponseEntity<ApiResponse<PreferenceResponse>> updatePreferences(@AuthenticationPrincipal UUID userId, @RequestBody PreferenceRequest request) {
        return ResponseEntity.ok(ApiResponse.success(userPageService.updatePreferences(userId, request), "설정 변경 성공"));
    }

    // 현재 로그인한 유저의 약관/마케팅 동의 상태를 조회합니다.
    // @AuthenticationPrincipal에는 JwtAuthenticationFilter가 토큰에서 꺼낸 userId가 들어옵니다.
    @GetMapping("/consent")
    public ResponseEntity<ApiResponse<ConsentResponse>> getConsent(@AuthenticationPrincipal UUID userId) {
        return ResponseEntity.ok(ApiResponse.success(userConsentService.getConsent(userId), "동의 상태 조회 성공"));
    }

    // 약관 재동의 또는 마케팅 수신 동의 변경을 처리합니다.
    // 마케팅 동의만 바꾸는 요청은 기존 약관 동의 시각을 보존합니다.
    @PostMapping("/consent")
    public ResponseEntity<ApiResponse<ConsentResponse>> updateConsent(
            @AuthenticationPrincipal UUID userId,
            @RequestBody ConsentRequest request
    ) {
        return ResponseEntity.ok(ApiResponse.success(userConsentService.updateConsent(userId, request), "동의 상태 변경 성공"));
    }

}
