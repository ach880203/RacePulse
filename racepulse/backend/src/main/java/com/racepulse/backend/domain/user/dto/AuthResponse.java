package com.racepulse.backend.domain.user.dto;

// =============================================================================
// AuthResponse.java — 로그인/회원가입 성공 응답 DTO
// =============================================================================
// 로그인이 성공하면 Access Token을 응답 본문으로 내려줍니다.
// Refresh Token은 HttpOnly Cookie로만 내려줍니다.
//
// [HttpOnly Cookie란?]
// JavaScript가 document.cookie 로 읽을 수 없는 쿠키입니다.
// XSS(악성 스크립트) 공격으로 토큰을 훔쳐가는 것을 방지합니다.
// =============================================================================

import com.fasterxml.jackson.annotation.JsonIgnore;
import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

@Getter
@Builder
public class AuthResponse {

    // JWT Access Token — Authorization 헤더에 담아서 API 요청에 사용합니다.
    private String accessToken;

    // Refresh Token??HttpOnly Cookie濡쒕쭔 ?ъ슜?섎룄濡?JSON ?묐떟?먯꽌???쒖쇅?⑸땲??
    @JsonIgnore
    private String refreshToken;

    // 토큰 타입. 관례적으로 "Bearer"를 사용합니다.
    // API 요청 헤더: Authorization: Bearer <accessToken>
    @Builder.Default
    private String tokenType = "Bearer";

    // Access Token 만료까지 남은 시간 (초 단위)
    private long expiresIn;

    // 로그인한 유저의 기본 정보
    private UUID userId;
    private String email;
    private String nickname;
    private String role;
    private String tier;
}
