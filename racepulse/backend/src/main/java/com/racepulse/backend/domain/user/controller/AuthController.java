package com.racepulse.backend.domain.user.controller;

// =============================================================================
// AuthController.java — 인증 관련 API 7개를 제공하는 컨트롤러
// =============================================================================
// 제공 API:
//   GET  /api/v1/auth/kakao           → 카카오 로그인 페이지로 리다이렉트
//   GET  /api/v1/auth/kakao/callback  → 카카오 콜백 처리
//   POST /api/v1/auth/register        → 이메일 회원가입
//   POST /api/v1/auth/login           → 이메일 로그인
//   POST /api/v1/auth/logout          → 로그아웃
//   POST /api/v1/auth/refresh         → Access Token 재발급
//   GET  /api/v1/auth/me              → 내 정보 조회
// =============================================================================

import com.racepulse.backend.domain.user.dto.AuthResponse;
import com.racepulse.backend.domain.user.dto.LoginRequest;
import com.racepulse.backend.domain.user.dto.RegisterRequest;
import com.racepulse.backend.domain.user.dto.UserResponse;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.domain.user.service.AuthService;
import com.racepulse.backend.domain.user.service.KakaoOAuthService;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.security.JwtTokenProvider;
import com.racepulse.backend.global.security.RefreshTokenService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.util.StringUtils;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.Arrays;
import java.util.UUID;

// @Tag = Swagger UI에서 API 그룹 이름과 설명을 표시합니다.
@Tag(name = "Auth", description = "회원가입, 로그인, 카카오 OAuth, 토큰 관리 API")
@Slf4j
@RestController
// @RequestMapping = 이 컨트롤러의 모든 API 앞에 붙는 기본 경로입니다.
@RequestMapping("/api/v1/auth")
@RequiredArgsConstructor
public class AuthController {

    private final KakaoOAuthService kakaoOAuthService;
    private final AuthService authService;
    private final RefreshTokenService refreshTokenService;
    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;

    // Refresh Token 쿠키 이름 (HttpOnly Cookie)
    private static final String REFRESH_TOKEN_COOKIE = "refresh_token";

    // =========================================================================
    // 카카오 OAuth
    // =========================================================================

    @Operation(summary = "카카오 로그인 시작", description = "카카오 로그인 페이지로 리다이렉트합니다.")
    @GetMapping("/kakao")
    public void redirectToKakao(HttpServletResponse response) throws IOException {
        // sendRedirect = 브라우저를 카카오 로그인 URL로 이동시킵니다.
        String authUrl = kakaoOAuthService.buildAuthorizationUrl();
        log.debug("카카오 로그인 리다이렉트. url={}", authUrl);
        response.sendRedirect(authUrl);
    }

    @Operation(summary = "카카오 콜백 처리", description = "카카오에서 인가코드를 받아 JWT를 발급합니다.")
    @GetMapping("/kakao/callback")
    public ResponseEntity<ApiResponse<AuthResponse>> kakaoCallback(
            @RequestParam String code,
            @RequestParam(defaultValue = "false") boolean rememberMe,
            HttpServletResponse response
    ) {
        AuthResponse auth = kakaoOAuthService.processCallback(code, rememberMe);

        // Refresh Token을 HttpOnly Cookie에 담아서 내려줍니다.
        // HttpOnly Cookie란? JavaScript에서 읽을 수 없는 쿠키 → XSS 공격 방어
        setRefreshTokenCookie(response, auth.getRefreshToken(), rememberMe);

        return ResponseEntity.ok(ApiResponse.success(auth, "카카오 로그인 성공"));
    }

    // =========================================================================
    // 이메일 회원가입 / 로그인
    // =========================================================================

    @Operation(summary = "이메일 회원가입")
    @PostMapping("/register")
    public ResponseEntity<ApiResponse<AuthResponse>> register(
            @Valid @RequestBody RegisterRequest request,
            HttpServletResponse response
    ) {
        // @Valid = RegisterRequest 의 @NotBlank, @Email 등 검증을 실행합니다.
        AuthResponse auth = authService.register(request);
        setRefreshTokenCookie(response, auth.getRefreshToken(), false);
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(ApiResponse.success(auth, "회원가입 성공"));
    }

    @Operation(summary = "이메일 로그인")
    @PostMapping("/login")
    public ResponseEntity<ApiResponse<AuthResponse>> login(
            @Valid @RequestBody LoginRequest request,
            HttpServletResponse response
    ) {
        AuthResponse auth = authService.login(request);
        setRefreshTokenCookie(response, auth.getRefreshToken(), request.isRememberMe());
        return ResponseEntity.ok(ApiResponse.success(auth, "로그인 성공"));
    }

    // =========================================================================
    // 로그아웃
    // =========================================================================

    @Operation(summary = "로그아웃", description = "Access Token 블랙리스트 등록 + Refresh Token 전체 삭제")
    @PostMapping("/logout")
    public ResponseEntity<ApiResponse<Void>> logout(
            HttpServletRequest request,
            HttpServletResponse response,
            @AuthenticationPrincipal UUID userId
    ) {
        // Access Token을 블랙리스트에 등록합니다.
        // 만료 전이라도 이 토큰으로는 더 이상 인증이 안 됩니다.
        String accessToken = extractBearerToken(request);
        if (StringUtils.hasText(accessToken) && jwtTokenProvider.validateToken(accessToken)) {
            refreshTokenService.addToBlacklist(accessToken, jwtTokenProvider.getAccessTokenExpirationSeconds());
        }

        // DB에서 해당 유저의 모든 Refresh Token을 삭제합니다.
        if (userId != null) {
            refreshTokenService.revokeAll(userId);
        }

        // 브라우저의 Refresh Token 쿠키도 삭제합니다.
        clearRefreshTokenCookie(response);

        return ResponseEntity.ok(ApiResponse.success(null, "로그아웃 성공"));
    }

    // =========================================================================
    // Access Token 재발급
    // =========================================================================

    @Operation(summary = "Access Token 재발급", description = "HttpOnly 쿠키의 Refresh Token으로 새 Access Token을 발급합니다.")
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponse<AuthResponse>> refresh(
            HttpServletRequest request,
            HttpServletResponse response
    ) {
        // HttpOnly 쿠키에서 Refresh Token을 꺼냅니다.
        // 클라이언트가 직접 헤더에 담는 것이 아니라 쿠키에서 자동으로 옵니다.
        String refreshToken = extractRefreshTokenFromCookie(request);
        if (!StringUtils.hasText(refreshToken)) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.<AuthResponse>builder()
                            .success(false).message("Refresh Token이 없습니다.").build());
        }

        // Token Rotation: 기존 토큰 무효화 + 새 Access Token 발급
        AuthResponse auth = refreshTokenService.rotate(refreshToken);

        // 새 Refresh Token도 발급해서 쿠키 갱신
        setRefreshTokenCookie(response, auth.getRefreshToken(), false);

        return ResponseEntity.ok(ApiResponse.success(auth, "Access Token 재발급 성공"));
    }

    // =========================================================================
    // 내 정보 조회
    // =========================================================================

    @Operation(summary = "내 정보 조회", description = "현재 로그인한 유저의 정보를 반환합니다.")
    @GetMapping("/me")
    public ResponseEntity<ApiResponse<UserResponse>> getMe(
            @AuthenticationPrincipal UUID userId
    ) {
        // @AuthenticationPrincipal = JwtAuthenticationFilter가 SecurityContext에 저장한
        // principal 값(userId)을 바로 꺼내쓰는 어노테이션입니다.
        if (userId == null) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                    .body(ApiResponse.<UserResponse>builder()
                            .success(false).message("로그인이 필요합니다.").build());
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("유저를 찾을 수 없습니다."));

        return ResponseEntity.ok(ApiResponse.success(UserResponse.from(user), "내 정보 조회 성공"));
    }

    // =========================================================================
    // 쿠키 유틸리티 메서드
    // =========================================================================

    /**
     * Refresh Token을 HttpOnly Cookie로 내려줍니다.
     *
     * HttpOnly = JavaScript 접근 불가 (XSS 방어)
     * Secure   = HTTPS 에서만 전송 (운영 환경에서는 반드시 true)
     * SameSite = CSRF 공격 방어 (같은 도메인 요청에서만 쿠키 전송)
     */
    private void setRefreshTokenCookie(HttpServletResponse response, String refreshToken, boolean rememberMe) {
        int maxAge = rememberMe ? (3 * 24 * 60 * 60) : (24 * 60 * 60); // 초 단위

        // Spring의 Cookie 객체 대신 Set-Cookie 헤더를 직접 작성합니다.
        // SameSite 속성이 Jakarta Cookie에서 지원되지 않기 때문입니다.
        String cookieValue = REFRESH_TOKEN_COOKIE + "=" + refreshToken
                + "; Path=/api/v1/auth"  // 인증 경로에서만 전송
                + "; HttpOnly"           // JavaScript 접근 차단
                + "; SameSite=Lax"       // 같은 사이트 요청에서만 전송
                + "; Max-Age=" + maxAge;
        // TODO: [Phase 2] HTTPS 배포 시 "; Secure" 추가

        response.addHeader("Set-Cookie", cookieValue);
    }

    /**
     * 브라우저의 Refresh Token 쿠키를 삭제합니다.
     */
    private void clearRefreshTokenCookie(HttpServletResponse response) {
        Cookie cookie = new Cookie(REFRESH_TOKEN_COOKIE, "");
        cookie.setHttpOnly(true);
        cookie.setPath("/api/v1/auth");
        cookie.setMaxAge(0); // 즉시 만료
        response.addCookie(cookie);
    }

    /**
     * HTTP 요청의 Authorization 헤더에서 Bearer 토큰을 추출합니다.
     */
    private String extractBearerToken(HttpServletRequest request) {
        String header = request.getHeader("Authorization");
        if (StringUtils.hasText(header) && header.startsWith("Bearer ")) {
            return header.substring(7);
        }
        return null;
    }

    /**
     * HTTP 요청의 쿠키에서 Refresh Token을 추출합니다.
     */
    private String extractRefreshTokenFromCookie(HttpServletRequest request) {
        if (request.getCookies() == null) return null;
        return Arrays.stream(request.getCookies())
                .filter(cookie -> REFRESH_TOKEN_COOKIE.equals(cookie.getName()))
                .map(Cookie::getValue)
                .findFirst()
                .orElse(null);
    }
}
