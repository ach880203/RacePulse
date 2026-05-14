package com.racepulse.backend.global.security;

// =============================================================================
// JwtTokenProvider.java — JWT 토큰 생성 및 검증 유틸리티
// =============================================================================
// JWT(JSON Web Token)란?
//   Header.Payload.Signature 세 부분이 점(.)으로 이어진 문자열입니다.
//   예: eyJhbGc....(Header) . eyJ1c2VySW....(Payload) . SflKxwRJSMeKKF2QT4....(Signature)
//
//   Header   = 사용한 알고리즘 정보 (예: HS256)
//   Payload  = 실제 데이터 (userId, role, tier, 만료시각 등)
//   Signature = 헤더+페이로드를 비밀키로 서명한 값 (위변조 방지)
//
// 서버만 비밀키를 알고 있으므로, 서명이 맞으면 "우리 서버가 발급한 토큰"임을 증명합니다.
// =============================================================================

import io.jsonwebtoken.*;
import io.jsonwebtoken.io.Decoders;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.Date;
import java.util.UUID;

// @Slf4j = log.info(), log.error() 같은 로그 메서드를 자동 생성해줍니다.
@Slf4j
// @Component = 스프링이 이 클래스를 Bean으로 관리하도록 등록합니다.
@Component
public class JwtTokenProvider {

    // 비밀키 — application.yaml의 jwt.secret 값을 주입받습니다.
    // @Value = 설정 파일의 값을 필드에 주입하는 Spring 어노테이션입니다.
    private final SecretKey secretKey;

    // Access Token 유효기간 (밀리초 단위, 기본 1시간 = 3600000ms)
    private final long accessExpiration;

    // Refresh Token 유효기간 (밀리초 단위, 기본 24시간)
    private final long refreshExpiration;

    // Refresh Token 유효기간 (로그인 유지 선택 시, 기본 3일)
    private final long refreshExpirationExtended;

    // @Value("${키}") = application.yaml에서 해당 키의 값을 자동으로 주입합니다.
    public JwtTokenProvider(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.access-expiration}") long accessExpiration,
            @Value("${jwt.refresh-expiration}") long refreshExpiration,
            @Value("${jwt.refresh-expiration-extended}") long refreshExpirationExtended
    ) {
        // 비밀키 문자열 → SecretKey 변환
        // Base64 인코딩 문자열이면 디코딩, 아니면 UTF-8 바이트 그대로 사용합니다.
        // HMAC-SHA256은 최소 256비트(32바이트) 이상이어야 합니다.
        this.secretKey = Keys.hmacShaKeyFor(decodeSecret(secret));
        this.accessExpiration = accessExpiration;
        this.refreshExpiration = refreshExpiration;
        this.refreshExpirationExtended = refreshExpirationExtended;
    }

    /**
     * Access Token을 생성합니다.
     *
     * @param userId 유저의 UUID
     * @param role   유저 권한 (USER / ADMIN)
     * @param tier   구독 등급 (FREE / PRO)
     * @return JWT Access Token 문자열
     */
    public String generateAccessToken(UUID userId, String role, String tier) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + accessExpiration);

        return Jwts.builder()
                // claim = JWT Payload에 넣을 데이터 항목입니다.
                .claim("userId", userId.toString())
                .claim("role", role)
                .claim("tier", tier)
                // subject = 이 토큰의 주인 (일반적으로 유저 ID)
                .subject(userId.toString())
                // issuedAt = 토큰 발급 시각
                .issuedAt(now)
                // expiration = 토큰 만료 시각
                .expiration(expiry)
                // signWith = 비밀키로 서명합니다. 위변조를 방지합니다.
                .signWith(secretKey)
                .compact();  // 최종 JWT 문자열로 조합합니다.
    }

    /**
     * Refresh Token을 생성합니다.
     *
     * @param userId     유저의 UUID
     * @param rememberMe true이면 3일, false이면 24시간 유효
     * @return JWT Refresh Token 문자열
     */
    public String generateRefreshToken(UUID userId, boolean rememberMe) {
        Date now = new Date();
        long duration = rememberMe ? refreshExpirationExtended : refreshExpiration;
        Date expiry = new Date(now.getTime() + duration);

        return Jwts.builder()
                .subject(userId.toString())
                .issuedAt(now)
                .expiration(expiry)
                .signWith(secretKey)
                .compact();
    }

    /**
     * JWT 토큰에서 userId(UUID)를 추출합니다.
     */
    public UUID getUserIdFromToken(String token) {
        Claims claims = parseClaims(token);
        return UUID.fromString(claims.getSubject());
    }

    /**
     * JWT 토큰에서 role(권한)을 추출합니다.
     */
    public String getRoleFromToken(String token) {
        Claims claims = parseClaims(token);
        return claims.get("role", String.class);
    }

    /**
     * JWT 토큰이 유효한지 검증합니다.
     *
     * @return true = 유효, false = 무효(만료/위변조/형식오류)
     */
    public boolean validateToken(String token) {
        if (token == null || token.isBlank()) {
            return false;
        }
        try {
            parseClaims(token);
            return true;
        } catch (ExpiredJwtException e) {
            // 만료된 토큰: 클라이언트가 Refresh Token으로 재발급 요청해야 합니다.
            log.debug("JWT 만료: {}", e.getMessage());
        } catch (JwtException | IllegalArgumentException e) {
            // 위변조되거나 형식이 잘못된 토큰, 또는 빈 문자열 등 잘못된 입력
            log.warn("JWT 검증 실패: {}", e.getMessage());
        }
        return false;
    }

    /**
     * Access Token의 남은 유효 시간을 초 단위로 반환합니다.
     */
    public long getAccessTokenExpirationSeconds() {
        return accessExpiration / 1000;
    }

    /**
     * 비밀키 문자열을 바이트 배열로 변환합니다.
     * Base64 인코딩 문자열이면 디코딩하고, 아니면 UTF-8 바이트를 그대로 사용합니다.
     */
    private byte[] decodeSecret(String secret) {
        try {
            // 표준 Base64 시도
            return Base64.getDecoder().decode(secret);
        } catch (IllegalArgumentException e1) {
            try {
                // Base64URL 시도 (- 와 _ 를 사용하는 URL-safe Base64)
                return Base64.getUrlDecoder().decode(secret);
            } catch (IllegalArgumentException e2) {
                // Base64가 아닌 평문 문자열이면 UTF-8 바이트로 변환
                return secret.getBytes(StandardCharsets.UTF_8);
            }
        }
    }

    /**
     * JWT 문자열을 파싱하여 Payload(Claims)를 꺼냅니다.
     * Claims = Payload 안의 모든 데이터를 Map처럼 담고 있는 객체입니다.
     */
    private Claims parseClaims(String token) {
        return Jwts.parser()
                .verifyWith(secretKey)   // 서명 검증에 사용할 비밀키 지정
                .build()
                .parseSignedClaims(token) // 파싱 + 서명 검증 동시 실행
                .getPayload();           // Payload(Claims) 반환
    }
}
