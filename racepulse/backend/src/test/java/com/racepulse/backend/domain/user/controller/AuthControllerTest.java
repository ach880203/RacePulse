package com.racepulse.backend.domain.user.controller;

// =============================================================================
// AuthControllerTest.java — 인증 API 컨트롤러 테스트
// =============================================================================
// 사용 방식: Standalone MockMvc
//   @WebMvcTest(Spring Security 포함) 대신 MockMvcBuilders.standaloneSetup()을 씁니다.
//   장점:
//     - Spring Security, CSRF, JWT 필터 없음 → 복잡한 보안 설정 불필요
//     - 컨트롤러 로직(요청 포맷, 응답 구조, 유효성 검사)에만 집중
//     - 빠른 실행 (Spring 컨텍스트 로드 없음)
//   단점:
//     - 실제 JWT 인증 필터 동작은 검증하지 않음 (JwtTokenProviderTest에서 검증)
// =============================================================================

import com.fasterxml.jackson.databind.ObjectMapper;
import com.racepulse.backend.domain.user.dto.AuthResponse;
import com.racepulse.backend.domain.user.entity.AuthProvider;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.entity.UserRole;
import com.racepulse.backend.domain.user.entity.UserTier;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.domain.user.service.AuthService;
import com.racepulse.backend.domain.user.service.KakaoOAuthService;
import com.racepulse.backend.global.security.BlacklistService;
import com.racepulse.backend.global.security.JwtTokenProvider;
import com.racepulse.backend.global.security.RefreshTokenService;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.http.MediaType;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.method.annotation.AuthenticationPrincipalArgumentResolver;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.hamcrest.Matchers.containsString;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.BDDMockito.given;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

// @ExtendWith(MockitoExtension.class) = @Mock, @InjectMocks 를 활성화합니다.
// Spring 컨텍스트 없이 Mockito만 사용합니다.
@ExtendWith(MockitoExtension.class)
class AuthControllerTest {

    private MockMvc mockMvc;
    private final ObjectMapper objectMapper = new ObjectMapper();

    // @Mock = Mockito가 가짜 객체를 만들어줍니다. DB/Redis 없이 원하는 값을 반환하도록 설정 가능합니다.
    @Mock private AuthService authService;
    @Mock private KakaoOAuthService kakaoOAuthService;
    @Mock private RefreshTokenService refreshTokenService;
    @Mock private JwtTokenProvider jwtTokenProvider;
    @Mock private UserRepository userRepository;
    @Mock private BlacklistService blacklistService;

    // @InjectMocks = 위의 @Mock 들을 AuthController 생성자에 자동 주입합니다.
    @InjectMocks
    private AuthController authController;

    private static final String BASE_URL  = "/api/v1/auth";
    private static final UUID   TEST_USER_ID = UUID.randomUUID();

    private AuthResponse sampleAuthResponse;

    @BeforeEach
    void setUp() {
        // standaloneSetup = Spring Security 없이 컨트롤러만 MockMvc에 등록합니다.
        // AuthenticationPrincipalArgumentResolver = @AuthenticationPrincipal 파라미터를
        //   SecurityContextHolder에서 꺼낼 수 있도록 해줍니다.
        mockMvc = MockMvcBuilders
                .standaloneSetup(authController)
                .setCustomArgumentResolvers(new AuthenticationPrincipalArgumentResolver())
                .build();

        sampleAuthResponse = AuthResponse.builder()
                .accessToken("sample.access.token")
                .refreshToken("sample.refresh.token")
                .tokenType("Bearer")
                .expiresIn(3600L)
                .userId(TEST_USER_ID)
                .email("test@racepulse.com")
                .nickname("tester")
                .role("USER")
                .tier("FREE")
                .build();

        // 각 테스트 시작 전 SecurityContext 초기화
        SecurityContextHolder.clearContext();
    }

    // =========================================================================
    // 회원가입
    // =========================================================================
    @Nested
    @DisplayName("POST /register")
    class Register {

        @Test
        @DisplayName("정상 입력 -> 201, ApiResponse 포맷 확인")
        void success() throws Exception {
            given(authService.register(any())).willReturn(sampleAuthResponse);

            mockMvc.perform(post(BASE_URL + "/register")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "password123",
                                        "nickname": "tester",
                                        "termsAgreed": true,
                                        "marketingAgreed": false
                                    }
                                    """))
                    .andExpect(status().isCreated())
                    .andExpect(jsonPath("$.success").value(true))
                    .andExpect(jsonPath("$.message").value("회원가입 성공"))
                    .andExpect(jsonPath("$.data.accessToken").value("sample.access.token"))
                    .andExpect(jsonPath("$.data.tokenType").value("Bearer"))
                    // refreshToken 은 @JsonIgnore -> 응답 본문에 없어야 함
                    .andExpect(jsonPath("$.data.refreshToken").doesNotExist());
        }

        @Test
        @DisplayName("회원가입 성공 -> Set-Cookie 에 refresh_token, HttpOnly 포함")
        void cookie() throws Exception {
            given(authService.register(any())).willReturn(sampleAuthResponse);

            mockMvc.perform(post(BASE_URL + "/register")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "password123",
                                        "nickname": "tester",
                                        "termsAgreed": true,
                                        "marketingAgreed": false
                                    }
                                    """))
                    .andExpect(status().isCreated())
                    .andExpect(header().exists("Set-Cookie"))
                    .andExpect(header().string("Set-Cookie", containsString("refresh_token=")))
                    .andExpect(header().string("Set-Cookie", containsString("HttpOnly")));
        }

        @Test
        @DisplayName("이메일 형식 오류 -> 400")
        void invalidEmail() throws Exception {
            mockMvc.perform(post(BASE_URL + "/register")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "not-an-email",
                                        "password": "password123",
                                        "nickname": "tester",
                                        "termsAgreed": true
                                    }
                                    """))
                    .andExpect(status().isBadRequest());
        }

        @Test
        @DisplayName("비밀번호 8자 미만 -> 400")
        void shortPassword() throws Exception {
            mockMvc.perform(post(BASE_URL + "/register")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "short",
                                        "nickname": "tester",
                                        "termsAgreed": true
                                    }
                                    """))
                    .andExpect(status().isBadRequest());
        }

        @Test
        @DisplayName("닉네임 누락 -> 400")
        void missingNickname() throws Exception {
            mockMvc.perform(post(BASE_URL + "/register")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "password123",
                                        "termsAgreed": true
                                    }
                                    """))
                    .andExpect(status().isBadRequest());
        }
    }

    // =========================================================================
    // 로그인
    // =========================================================================
    @Nested
    @DisplayName("POST /login")
    class Login {

        @Test
        @DisplayName("정상 로그인 -> 200, accessToken 포함")
        void success() throws Exception {
            given(authService.login(any())).willReturn(sampleAuthResponse);

            mockMvc.perform(post(BASE_URL + "/login")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "password123",
                                        "rememberMe": false
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.success").value(true))
                    .andExpect(jsonPath("$.message").value("로그인 성공"))
                    .andExpect(jsonPath("$.data.accessToken").exists())
                    .andExpect(jsonPath("$.data.userId").exists());
        }

        @Test
        @DisplayName("로그인 성공 -> Set-Cookie 에 HttpOnly refresh_token 포함")
        void cookie() throws Exception {
            given(authService.login(any())).willReturn(sampleAuthResponse);

            mockMvc.perform(post(BASE_URL + "/login")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "email": "test@racepulse.com",
                                        "password": "password123",
                                        "rememberMe": false
                                    }
                                    """))
                    .andExpect(status().isOk())
                    .andExpect(header().exists("Set-Cookie"))
                    .andExpect(header().string("Set-Cookie", containsString("HttpOnly")));
        }

        @Test
        @DisplayName("이메일 누락 -> 400")
        void missingEmail() throws Exception {
            mockMvc.perform(post(BASE_URL + "/login")
                            .contentType(MediaType.APPLICATION_JSON)
                            .content("""
                                    {
                                        "password": "password123"
                                    }
                                    """))
                    .andExpect(status().isBadRequest());
        }
    }

    // =========================================================================
    // Access Token 재발급
    // =========================================================================
    @Nested
    @DisplayName("POST /refresh")
    class Refresh {

        @Test
        @DisplayName("refresh_token 쿠키 없음 -> 401, success=false")
        void noCookie() throws Exception {
            mockMvc.perform(post(BASE_URL + "/refresh"))
                    .andExpect(status().isUnauthorized())
                    .andExpect(jsonPath("$.success").value(false));
        }

        @Test
        @DisplayName("refresh_token 쿠키 있음 -> 200, 새 accessToken 반환")
        void withCookie() throws Exception {
            AuthResponse newAuth = AuthResponse.builder()
                    .accessToken("new.access.token")
                    .refreshToken("new.refresh.token")
                    .tokenType("Bearer")
                    .expiresIn(3600L)
                    .userId(TEST_USER_ID)
                    .email("test@racepulse.com")
                    .nickname("tester")
                    .role("USER")
                    .tier("FREE")
                    .build();
            given(refreshTokenService.rotate(anyString())).willReturn(newAuth);

            mockMvc.perform(post(BASE_URL + "/refresh")
                            .cookie(new Cookie("refresh_token", "old.refresh.token")))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.success").value(true))
                    .andExpect(jsonPath("$.data.accessToken").value("new.access.token"));
        }
    }

    // =========================================================================
    // 내 정보 조회
    // =========================================================================
    @Nested
    @DisplayName("GET /me")
    class GetMe {

        @Test
        @DisplayName("인증 없음 -> 401, success=false")
        void noAuth() throws Exception {
            // SecurityContext 가 비어있으면 @AuthenticationPrincipal UUID userId = null
            // 컨트롤러가 null 을 확인하고 401 반환합니다.
            SecurityContextHolder.clearContext();

            mockMvc.perform(get(BASE_URL + "/me"))
                    .andExpect(status().isUnauthorized())
                    .andExpect(jsonPath("$.success").value(false));
        }

        @Test
        @DisplayName("인증된 사용자 -> 200, 유저 정보 반환")
        void withAuth() throws Exception {
            // SecurityContextHolder 에 UUID 주인공을 직접 등록합니다.
            // standaloneSetup + AuthenticationPrincipalArgumentResolver 조합으로
            // @AuthenticationPrincipal UUID userId 가 TEST_USER_ID 로 주입됩니다.
            UsernamePasswordAuthenticationToken auth =
                    new UsernamePasswordAuthenticationToken(
                            TEST_USER_ID,
                            null,
                            List.of(new SimpleGrantedAuthority("ROLE_USER"))
                    );
            SecurityContextHolder.getContext().setAuthentication(auth);

            User mockUser = User.builder()
                    .id(TEST_USER_ID)
                    .email("test@racepulse.com")
                    .nickname("tester")
                    .role(UserRole.USER)
                    .tier(UserTier.FREE)
                    .authProvider(AuthProvider.LOCAL)
                    .build();
            given(userRepository.findById(TEST_USER_ID)).willReturn(Optional.of(mockUser));

            mockMvc.perform(get(BASE_URL + "/me"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.success").value(true))
                    .andExpect(jsonPath("$.data.email").value("test@racepulse.com"))
                    .andExpect(jsonPath("$.data.nickname").value("tester"))
                    .andExpect(jsonPath("$.data.role").value("USER"));
        }
    }
}
