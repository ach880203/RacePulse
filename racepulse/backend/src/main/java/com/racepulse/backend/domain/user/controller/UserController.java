package com.racepulse.backend.domain.user.controller;

import com.racepulse.backend.domain.user.dto.FavoriteRequest;
import com.racepulse.backend.domain.user.dto.FavoriteResponse;
import com.racepulse.backend.domain.user.dto.PreferenceRequest;
import com.racepulse.backend.domain.user.dto.PreferenceResponse;
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

}
