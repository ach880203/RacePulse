package com.racepulse.backend.global.security;

// =============================================================================
// RefreshTokenService.java — Refresh Token 저장/검증/무효화 서비스
// =============================================================================
// Token Rotation(토큰 순환)이란?
//   Refresh Token을 한 번 쓰면 즉시 무효화하고 새 Refresh Token을 발급합니다.
//   그래서 Refresh Token도 한 번만 쓸 수 있는 일회용 토큰입니다.
//
// Token Family 탈취 감지란?
//   같은 로그인 세션(family)에서 발급된 토큰을 이미 사용된 것으로 표시합니다.
//   만약 "이미 사용됨" 상태인 토큰으로 또 요청이 오면 → 토큰이 탈취됐다고 판단합니다.
//   → 해당 family의 토큰 전체를 삭제하여 강제 로그아웃합니다.
// =============================================================================

import com.racepulse.backend.domain.user.dto.AuthResponse;
import com.racepulse.backend.domain.user.entity.RefreshToken;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.RefreshTokenRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.LocalDateTime;
import java.util.HexFormat;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class RefreshTokenService {

    private final RefreshTokenRepository refreshTokenRepository;
    private final BlacklistService blacklistService;
    private final JwtTokenProvider jwtTokenProvider;

    /**
     * Refresh Token을 DB에 저장합니다.
     * 로그인 성공 후 발급된 Refresh Token을 여기서 보관합니다.
     *
     * @param user       토큰 소유자
     * @param rawToken   JwtTokenProvider가 발급한 원본 토큰 문자열
     * @param familyId   이번 로그인 세션의 고유 ID
     * @param rememberMe 로그인 유지 여부 (만료 시간 결정)
     */
    @Transactional
    public void saveRefreshToken(User user, String rawToken, UUID familyId, boolean rememberMe) {
        String tokenHash = hashToken(rawToken);
        // rememberMe에 따라 만료 시각 계산
        long durationSeconds = rememberMe ? (3L * 24 * 60 * 60) : (24L * 60 * 60);
        LocalDateTime expiresAt = LocalDateTime.now().plusSeconds(durationSeconds);

        RefreshToken refreshToken = RefreshToken.builder()
                .user(user)
                .tokenHash(tokenHash)
                .familyId(familyId)
                .expiresAt(expiresAt)
                .build();

        refreshTokenRepository.save(refreshToken);
        log.debug("Refresh Token 저장 완료. userId={}, familyId={}", user.getId(), familyId);
    }

    /**
     * Refresh Token을 검증하고, Token Rotation을 수행한 후 새 Access Token과 Refresh Token을 반환합니다.
     *
     * 검증 과정:
     * 1. DB에서 토큰 해시 조회
     * 2. 만료 여부 확인
     * 3. 이미 사용된 토큰이면 탈취로 판단 → family 전체 삭제 → 예외 발생
     * 4. 정상이면 현재 토큰 is_used=true 처리 후 새 토큰 발급
     *
     * @param rawToken 클라이언트가 보낸 원본 Refresh Token
     * @return 새로 발급된 Access Token
     */
    @Transactional
    public AuthResponse rotate(String rawToken) {
        String tokenHash = hashToken(rawToken);

        // DB에서 해시로 토큰 조회
        RefreshToken stored = refreshTokenRepository.findByTokenHash(tokenHash)
                .orElseThrow(() -> new IllegalArgumentException("존재하지 않는 Refresh Token입니다."));

        // 만료 확인
        if (stored.getExpiresAt().isBefore(LocalDateTime.now())) {
            throw new IllegalArgumentException("만료된 Refresh Token입니다.");
        }

        // 이미 사용된 토큰으로 재요청 → 탈취 의심
        if (stored.isUsed()) {
            log.warn("이미 사용된 Refresh Token 재사용 감지! 탈취 의심. familyId={}", stored.getFamilyId());
            // 해당 family의 모든 토큰 삭제 (강제 로그아웃)
            refreshTokenRepository.deleteAllByFamilyId(stored.getFamilyId());
            throw new SecurityException("탈취가 의심되어 모든 세션이 종료됐습니다. 다시 로그인해주세요.");
        }

        // Token Rotation: 현재 토큰을 사용 완료 처리
        stored.markAsUsed();

        // 새 Refresh Token 발급 후 DB 저장
        User user = stored.getUser();
        String newRawRefreshToken = jwtTokenProvider.generateRefreshToken(user.getId(), false);
        saveRefreshToken(user, newRawRefreshToken, stored.getFamilyId(), false);

        // 새 Access Token 발급
        String newAccessToken = jwtTokenProvider.generateAccessToken(
                user.getId(),
                user.getRole().name(),
                user.getTier().name()
        );

        return AuthResponse.builder()
                .accessToken(newAccessToken)
                .refreshToken(newRawRefreshToken)
                .expiresIn(jwtTokenProvider.getAccessTokenExpirationSeconds())
                .userId(user.getId())
                .email(user.getEmail())
                .nickname(user.getNickname())
                .role(user.getRole().name())
                .tier(user.getTier().name())
                .build();
    }

    /**
     * 특정 유저의 모든 Refresh Token을 삭제합니다. (로그아웃)
     */
    @Transactional
    public void revokeAll(UUID userId) {
        refreshTokenRepository.deleteAllByUserId(userId);
        log.debug("Refresh Token 전체 삭제 완료. userId={}", userId);
    }

    /**
     * Access Token을 Redis 블랙리스트에 등록합니다.
     * 로그아웃 시 발급된 Access Token이 만료 전에 사용되지 않도록 막습니다.
     *
     * Redis 블랙리스트란?
     *   "이 토큰은 로그아웃된 토큰이다"를 Redis에 기록해두는 것입니다.
     *   JWT는 서버가 직접 무효화할 수 없으므로(stateless), 블랙리스트로 우회합니다.
     */
    public void addToBlacklist(String accessToken, long remainingSeconds) {
        blacklistService.add(accessToken, remainingSeconds);
    }

    /**
     * 토큰 원본 문자열을 SHA-256 해시로 변환합니다.
     * DB에 원본 대신 해시를 저장하여 보안을 강화합니다.
     */
    private String hashToken(String token) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            byte[] hash = digest.digest(token.getBytes(StandardCharsets.UTF_8));
            // byte 배열을 16진수 문자열로 변환합니다 (예: "a3f5c2...")
            return HexFormat.of().formatHex(hash);
        } catch (NoSuchAlgorithmException e) {
            // SHA-256은 Java 표준 알고리즘이므로 이 예외는 실제로 발생하지 않습니다.
            throw new RuntimeException("SHA-256 알고리즘 오류", e);
        }
    }
}
