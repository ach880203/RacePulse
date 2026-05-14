package com.racepulse.backend.global.security;

// =============================================================================
// JwtTokenProviderTest.java — JWT 유틸리티 단위 테스트
// =============================================================================
// 단위 테스트(Unit Test)란?
//   딱 하나의 클래스/메서드만 격리해서 테스트합니다.
//   DB도 없고, Spring 서버도 안 켜집니다. 그래서 0.1초 이내로 실행됩니다.
//
// 이 테스트가 검증하는 것:
//   1. 토큰 생성 → 데이터 정상 추출
//   2. 만료된 토큰 → false 반환
//   3. 위변조된 토큰 → false 반환
//   4. rememberMe 여부에 따른 만료 시간 차이
// =============================================================================

import io.jsonwebtoken.Jwts;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;

class JwtTokenProviderTest {

    // 테스트용 비밀키 (32자 이상 평문 — HMAC-SHA256 최소 조건)
    private static final String TEST_SECRET =
            "test-secret-key-for-racepulse-jwt-at-least-32-chars!!";

    // 테스트용 만료 시간 설정
    private static final long ACCESS_EXPIRATION          = 3_600_000L;   // 1시간 (ms)
    private static final long REFRESH_EXPIRATION         = 86_400_000L;  // 24시간 (ms)
    private static final long REFRESH_EXPIRATION_EXTENDED = 259_200_000L; // 3일 (ms)

    // 테스트 대상 객체
    private JwtTokenProvider jwtTokenProvider;

    // ==========================================================================
    // @BeforeEach = 각 @Test 메서드 실행 전에 자동으로 호출됩니다.
    //               매번 새로운 인스턴스를 만들어 테스트 간 상태가 섞이지 않게 합니다.
    // ==========================================================================
    @BeforeEach
    void setUp() {
        // Spring 없이 직접 생성자를 호출해서 인스턴스를 만듭니다.
        // @Value 주입 대신 생성자 인자로 직접 값을 넘깁니다.
        jwtTokenProvider = new JwtTokenProvider(
                TEST_SECRET,
                ACCESS_EXPIRATION,
                REFRESH_EXPIRATION,
                REFRESH_EXPIRATION_EXTENDED
        );
    }

    // ==========================================================================
    // 테스트 1: Access Token 생성 후 userId 정상 추출
    // ==========================================================================
    @Test
    @DisplayName("Access Token 생성 → userId 추출 성공")
    void generateAccessToken_thenGetUserIdFromToken() {
        // given — 테스트 입력값 준비
        UUID userId = UUID.randomUUID();
        String role = "USER";
        String tier = "FREE";

        // when — 실제 동작 실행
        String token = jwtTokenProvider.generateAccessToken(userId, role, tier);

        // then — 결과 검증
        // assertThat(실제값).isEqualTo(기대값) 형식입니다.
        UUID extractedUserId = jwtTokenProvider.getUserIdFromToken(token);
        assertThat(extractedUserId).isEqualTo(userId);
    }

    // ==========================================================================
    // 테스트 2: Access Token 생성 후 role 정상 추출
    // ==========================================================================
    @Test
    @DisplayName("Access Token 생성 → role 추출 성공")
    void generateAccessToken_thenGetRoleFromToken() {
        // given
        UUID userId = UUID.randomUUID();
        String role = "ADMIN";
        String tier = "PRO";

        // when
        String token = jwtTokenProvider.generateAccessToken(userId, role, tier);

        // then
        String extractedRole = jwtTokenProvider.getRoleFromToken(token);
        assertThat(extractedRole).isEqualTo("ADMIN");
    }

    // ==========================================================================
    // 테스트 3: 정상 토큰 → validateToken() = true
    // ==========================================================================
    @Test
    @DisplayName("유효한 Access Token → validateToken = true")
    void validateToken_withValidToken_returnsTrue() {
        // given
        String token = jwtTokenProvider.generateAccessToken(
                UUID.randomUUID(), "USER", "FREE"
        );

        // when & then
        assertThat(jwtTokenProvider.validateToken(token)).isTrue();
    }

    // ==========================================================================
    // 테스트 4: 만료된 토큰 → validateToken() = false
    //
    // 핵심 아이디어:
    //   만료 시간을 -1ms(이미 지난 시간)로 설정한 JwtTokenProvider를 따로 만들면
    //   생성 즉시 만료된 토큰을 만들 수 있습니다.
    // ==========================================================================
    @Test
    @DisplayName("만료된 Access Token → validateToken = false")
    void validateToken_withExpiredToken_returnsFalse() {
        // given — 만료 시간이 -1ms인 특수 provider 생성 (토큰이 생성 즉시 만료됨)
        JwtTokenProvider expiredProvider = new JwtTokenProvider(
                TEST_SECRET,
                -1L,  // 이미 만료된 시간
                REFRESH_EXPIRATION,
                REFRESH_EXPIRATION_EXTENDED
        );
        String expiredToken = expiredProvider.generateAccessToken(
                UUID.randomUUID(), "USER", "FREE"
        );

        // when & then
        // 정상 provider로 만료 토큰을 검증하면 false가 나와야 합니다.
        assertThat(jwtTokenProvider.validateToken(expiredToken)).isFalse();
    }

    // ==========================================================================
    // 테스트 5: 위변조된 토큰 → validateToken() = false
    //
    // 핵심 아이디어:
    //   JWT는 Header.Payload.Signature 구조입니다.
    //   Signature 마지막 글자를 바꾸면 서명 검증에 실패합니다.
    // ==========================================================================
    @Test
    @DisplayName("위변조된 Token → validateToken = false")
    void validateToken_withTamperedToken_returnsFalse() {
        // given
        String token = jwtTokenProvider.generateAccessToken(
                UUID.randomUUID(), "USER", "FREE"
        );

        // 토큰 마지막 글자를 변조합니다.
        // 예: "eyJ...abc" → "eyJ...abX"
        String tamperedToken = token.substring(0, token.length() - 1) + "X";

        // when & then
        assertThat(jwtTokenProvider.validateToken(tamperedToken)).isFalse();
    }

    // ==========================================================================
    // 테스트 6: 완전히 다른 문자열 → validateToken() = false
    // ==========================================================================
    @Test
    @DisplayName("JWT 형식 아닌 문자열 → validateToken = false")
    void validateToken_withGarbageString_returnsFalse() {
        assertThat(jwtTokenProvider.validateToken("this-is-not-a-jwt")).isFalse();
        assertThat(jwtTokenProvider.validateToken("")).isFalse();
        assertThat(jwtTokenProvider.validateToken("Bearer fake.token.here")).isFalse();
    }

    // ==========================================================================
    // 테스트 7: Refresh Token — rememberMe=false → 24시간 만료
    // ==========================================================================
    @Test
    @DisplayName("Refresh Token (rememberMe=false) → 유효, 24시간 내 만료")
    void generateRefreshToken_withoutRememberMe_isValid() {
        // given
        UUID userId = UUID.randomUUID();

        // when
        String token = jwtTokenProvider.generateRefreshToken(userId, false);

        // then — 토큰이 유효하고, userId도 정상 추출되어야 합니다.
        assertThat(jwtTokenProvider.validateToken(token)).isTrue();
        assertThat(jwtTokenProvider.getUserIdFromToken(token)).isEqualTo(userId);
    }

    // ==========================================================================
    // 테스트 8: Refresh Token — rememberMe=true → 3일 만료
    // ==========================================================================
    @Test
    @DisplayName("Refresh Token (rememberMe=true) → 유효, 3일 내 만료")
    void generateRefreshToken_withRememberMe_isValid() {
        // given
        UUID userId = UUID.randomUUID();

        // when
        String token = jwtTokenProvider.generateRefreshToken(userId, true);

        // then
        assertThat(jwtTokenProvider.validateToken(token)).isTrue();
        assertThat(jwtTokenProvider.getUserIdFromToken(token)).isEqualTo(userId);
    }

    // ==========================================================================
    // 테스트 9: 다른 비밀키로 서명된 토큰 → validateToken() = false
    //
    // 실제 공격 시나리오: 공격자가 자기 서버에서 만든 토큰을 우리 서버에 쓰려는 경우
    // ==========================================================================
    @Test
    @DisplayName("다른 비밀키로 서명된 토큰 → validateToken = false")
    void validateToken_signedWithDifferentKey_returnsFalse() {
        // given — 다른 비밀키로 토큰 생성
        JwtTokenProvider anotherProvider = new JwtTokenProvider(
                "completely-different-secret-key-for-attacker-server!!",
                ACCESS_EXPIRATION,
                REFRESH_EXPIRATION,
                REFRESH_EXPIRATION_EXTENDED
        );
        String foreignToken = anotherProvider.generateAccessToken(
                UUID.randomUUID(), "ADMIN", "PRO"  // 심지어 ADMIN 권한으로 시도
        );

        // when & then — 우리 서버의 provider는 이 토큰을 거부해야 합니다.
        assertThat(jwtTokenProvider.validateToken(foreignToken)).isFalse();
    }

    // ==========================================================================
    // 테스트 10: getAccessTokenExpirationSeconds() — 단위 변환 정확성
    // ==========================================================================
    @Test
    @DisplayName("getAccessTokenExpirationSeconds → 밀리초를 초로 정확히 변환")
    void getAccessTokenExpirationSeconds_returnsCorrectValue() {
        // ACCESS_EXPIRATION = 3_600_000ms → 3600초 = 1시간
        assertThat(jwtTokenProvider.getAccessTokenExpirationSeconds()).isEqualTo(3600L);
    }
}
