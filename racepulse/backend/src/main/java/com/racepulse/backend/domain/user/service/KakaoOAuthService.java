package com.racepulse.backend.domain.user.service;

// =============================================================================
// KakaoOAuthService.java — 카카오 OAuth 2.0 로그인 처리 서비스
// =============================================================================
// OAuth 2.0 전체 흐름 (인가코드 방식):
//
// [1단계] 사용자가 "카카오로 로그인" 버튼 클릭
//         → GET /api/v1/auth/kakao
//         → 서버가 카카오 로그인 페이지 URL 로 리다이렉트
//
// [2단계] 사용자가 카카오에서 로그인 + 권한 동의
//         → 카카오가 우리 서버로 "인가코드(code)"를 담아 리다이렉트
//         → GET /api/v1/auth/kakao/callback?code=XXXX
//
// [3단계] 인가코드 → 카카오 Access Token 교환 (서버↔카카오 통신)
//         POST https://kauth.kakao.com/oauth/token
//
// [4단계] 카카오 Access Token → 유저 정보 조회 (서버↔카카오 통신)
//         GET https://kapi.kakao.com/v2/user/me
//
// [5단계] DB에 유저 저장(신규) 또는 조회(기존) → JWT 발급
// =============================================================================

import com.racepulse.backend.domain.user.dto.AuthResponse;
import com.racepulse.backend.domain.user.entity.AuthProvider;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.global.security.JwtTokenProvider;
import com.racepulse.backend.global.security.RefreshTokenService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.RestTemplate;

import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class KakaoOAuthService {

    private final UserRepository userRepository;
    private final JwtTokenProvider jwtTokenProvider;
    private final RefreshTokenService refreshTokenService;

    // RestTemplate = HTTP 요청을 보내는 Spring 내장 HTTP 클라이언트입니다.
    private final RestTemplate restTemplate;

    // application.yaml 의 카카오 설정 값을 주입합니다.
    @Value("${spring.security.oauth2.client.registration.kakao.client-id}")
    private String clientId;

    @Value("${spring.security.oauth2.client.registration.kakao.client-secret}")
    private String clientSecret;

    @Value("${spring.security.oauth2.client.registration.kakao.redirect-uri}")
    private String redirectUri;

    // 카카오 인증 서버 URL
    private static final String KAKAO_TOKEN_URL     = "https://kauth.kakao.com/oauth/token";
    private static final String KAKAO_USER_INFO_URL = "https://kapi.kakao.com/v2/user/me";
    private static final String KAKAO_AUTH_URL      = "https://kauth.kakao.com/oauth/authorize";

    /**
     * 카카오 로그인 페이지 URL을 생성합니다.
     * 사용자가 이 URL로 이동하면 카카오 로그인 화면이 나타납니다.
     */
    public String buildAuthorizationUrl() {
        // response_type=code = 인가코드 방식을 사용하겠다는 의미입니다.
        // scope = 카카오에서 요청할 정보 항목 (닉네임, 이메일)
        return KAKAO_AUTH_URL
                + "?client_id=" + clientId
                + "&redirect_uri=" + redirectUri
                + "&response_type=code"
                + "&scope=profile_nickname,account_email";
    }

    /**
     * 카카오 콜백 처리: 인가코드로 카카오 Access Token을 받고, 유저 정보로 JWT를 발급합니다.
     *
     * @param code      카카오가 보내준 인가코드
     * @param rememberMe 로그인 유지 여부
     * @return 발급된 JWT 정보 (AuthResponse)
     */
    @Transactional
    public AuthResponse processCallback(String code, boolean rememberMe) {
        // [3단계] 인가코드 → 카카오 Access Token 교환
        String kakaoAccessToken = fetchKakaoAccessToken(code);

        // [4단계] 카카오 Access Token → 유저 정보 조회
        KakaoUserInfo userInfo = fetchKakaoUserInfo(kakaoAccessToken);

        log.info("카카오 로그인 처리. kakaoId={}, email={}", userInfo.kakaoId(), userInfo.email());

        // [5단계] DB에서 기존 유저 조회 또는 신규 유저 저장
        User user = findOrCreateUser(userInfo);

        // JWT 발급
        return issueTokens(user, rememberMe);
    }

    /**
     * 인가코드를 카카오 Access Token으로 교환합니다.
     * 카카오 인증 서버에 POST 요청을 보내서 토큰을 받습니다.
     */
    @SuppressWarnings("unchecked")
    private String fetchKakaoAccessToken(String code) {
        // Content-Type: application/x-www-form-urlencoded (카카오 API 요구사항)
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_FORM_URLENCODED);

        // 요청 파라미터 구성
        MultiValueMap<String, String> params = new LinkedMultiValueMap<>();
        params.add("grant_type", "authorization_code"); // 인가코드 방식
        params.add("client_id", clientId);              // 우리 앱의 REST API 키
        params.add("client_secret", clientSecret);      // 보안 강화용 시크릿 키
        params.add("redirect_uri", redirectUri);        // 카카오 앱 설정과 일치해야 합니다
        params.add("code", code);                       // 카카오가 보내준 인가코드

        HttpEntity<MultiValueMap<String, String>> request = new HttpEntity<>(params, headers);

        ResponseEntity<Map> response = restTemplate.postForEntity(
                KAKAO_TOKEN_URL, request, Map.class
        );

        Map<String, Object> body = response.getBody();
        if (body == null || !body.containsKey("access_token")) {
            throw new RuntimeException("카카오 Access Token 발급 실패");
        }

        return (String) body.get("access_token");
    }

    /**
     * 카카오 Access Token으로 카카오 유저 정보를 조회합니다.
     */
    @SuppressWarnings("unchecked")
    private KakaoUserInfo fetchKakaoUserInfo(String kakaoAccessToken) {
        // Authorization: Bearer <카카오 Access Token>
        HttpHeaders headers = new HttpHeaders();
        headers.setBearerAuth(kakaoAccessToken);

        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<Map> response = restTemplate.exchange(
                KAKAO_USER_INFO_URL, HttpMethod.GET, request, Map.class
        );

        Map<String, Object> body = response.getBody();
        if (body == null) {
            throw new RuntimeException("카카오 유저 정보 조회 실패");
        }

        // 카카오 API 응답 구조:
        // { "id": 1234567890, "kakao_account": { "email": "...", "profile": { "nickname": "..." } } }
        String kakaoId = String.valueOf(body.get("id"));
        Map<String, Object> kakaoAccount = (Map<String, Object>) body.get("kakao_account");
        Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");

        String email = (String) kakaoAccount.getOrDefault("email", kakaoId + "@kakao.local");
        String nickname = (String) profile.getOrDefault("nickname", "카카오유저");

        return new KakaoUserInfo(kakaoId, email, nickname);
    }

    /**
     * DB에서 kakaoId로 기존 유저를 찾거나, 없으면 신규 유저를 생성합니다.
     */
    private User findOrCreateUser(KakaoUserInfo info) {
        return userRepository.findByKakaoId(info.kakaoId())
                .orElseGet(() -> {
                    // 신규 유저 생성
                    User newUser = User.builder()
                            .email(info.email())
                            .kakaoId(info.kakaoId())
                            .nickname(info.nickname())
                            .authProvider(AuthProvider.KAKAO)
                            .build();
                    User saved = userRepository.save(newUser);
                    log.info("카카오 신규 유저 등록. userId={}", saved.getId());
                    return saved;
                });
    }

    /**
     * 유저 정보로 Access Token + Refresh Token을 발급하고 AuthResponse를 반환합니다.
     */
    public AuthResponse issueTokens(User user, boolean rememberMe) {
        String accessToken = jwtTokenProvider.generateAccessToken(
                user.getId(), user.getRole().name(), user.getTier().name()
        );
        String refreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), rememberMe);

        // Refresh Token은 DB에 해시로 저장합니다.
        UUID familyId = UUID.randomUUID();
        refreshTokenService.saveRefreshToken(user, refreshToken, familyId, rememberMe);

        return AuthResponse.builder()
                .accessToken(accessToken)
                .refreshToken(refreshToken)
                .expiresIn(jwtTokenProvider.getAccessTokenExpirationSeconds())
                .userId(user.getId())
                .email(user.getEmail())
                .nickname(user.getNickname())
                .role(user.getRole().name())
                .tier(user.getTier().name())
                .build();
    }

    /**
     * 카카오에서 받아온 유저 정보를 담는 내부 레코드입니다.
     * record = 불변 데이터 클래스로 Java 16+에서 사용 가능합니다.
     */
    record KakaoUserInfo(String kakaoId, String email, String nickname) {}
}
