package com.racepulse.backend.global.security;

// =============================================================================
// JwtAuthenticationFilter.java — 모든 HTTP 요청에서 JWT를 검증하는 필터
// =============================================================================
// Spring Security Filter Chain이란?
//   HTTP 요청이 Controller에 도달하기 전에 거치는 일련의 관문(Filter)들입니다.
//   순서: HTTP 요청 → Filter1 → Filter2 → ... → Controller → 응답
//
// 이 필터의 역할:
//   1. 요청 헤더에서 JWT를 꺼냅니다.
//   2. JWT가 유효하면 SecurityContext에 인증 정보를 저장합니다.
//   3. JWT가 없거나 무효면 그냥 다음 필터로 넘깁니다.
//      (401 처리는 SecurityConfig에서 담당합니다.)
//
// SecurityContext란?
//   현재 요청을 보낸 유저가 누구인지 스프링이 기억하는 저장소입니다.
//   Controller에서 @AuthenticationPrincipal 로 꺼내쓸 수 있습니다.
// =============================================================================

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;
import java.util.UUID;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    // OncePerRequestFilter = 같은 요청에서 이 필터가 두 번 실행되지 않도록 보장합니다.

    private final JwtTokenProvider jwtTokenProvider;
    // BlacklistService = 로그아웃된 토큰(블랙리스트)인지 확인하기 위해 주입합니다.
    private final BlacklistService blacklistService;

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain
    ) throws ServletException, IOException {

        // 1. 요청 헤더에서 JWT를 꺼냅니다.
        String token = extractToken(request);

        // 2. 토큰이 존재하고 유효하면 SecurityContext에 인증 정보를 저장합니다.
        // 블랙리스트 확인: 로그아웃된 토큰은 Redis에 블랙리스트로 등록됩니다.
        if (StringUtils.hasText(token) && jwtTokenProvider.validateToken(token)
                && !blacklistService.contains(token)) {
            try {
                UUID userId = jwtTokenProvider.getUserIdFromToken(token);
                String role = jwtTokenProvider.getRoleFromToken(token);

                // SimpleGrantedAuthority = Spring Security가 이해하는 권한 객체입니다.
                // role 값은 "USER" 또는 "ADMIN" — "ROLE_" 접두사를 붙여야 합니다.
                List<SimpleGrantedAuthority> authorities = List.of(
                        new SimpleGrantedAuthority("ROLE_" + role)
                );

                // UsernamePasswordAuthenticationToken = 인증 완료 상태를 나타내는 객체입니다.
                // principal = 누구인지 (여기서는 userId)
                // credentials = 비밀번호 (JWT 기반에서는 null)
                // authorities = 권한 목록
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(userId, null, authorities);

                // SecurityContextHolder = 현재 스레드에서 인증 정보를 보관하는 저장소입니다.
                // 여기에 저장하면 이후 Controller에서 @AuthenticationPrincipal 로 꺼낼 수 있습니다.
                SecurityContextHolder.getContext().setAuthentication(authentication);

                log.debug("JWT 인증 성공. userId={}", userId);

            } catch (Exception e) {
                // 토큰 파싱 중 예외가 발생하면 인증 정보를 설정하지 않고 다음으로 넘깁니다.
                log.warn("JWT 처리 중 오류: {}", e.getMessage());
                SecurityContextHolder.clearContext();
            }
        }

        // 3. 다음 필터(또는 Controller)로 요청을 전달합니다.
        filterChain.doFilter(request, response);
    }

    /**
     * HTTP 요청 헤더에서 Bearer 토큰을 추출합니다.
     *
     * Authorization 헤더 형식: "Bearer eyJhbGci..."
     * "Bearer " 접두사를 제거하고 JWT 문자열만 반환합니다.
     */
    private String extractToken(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");

        // StringUtils.hasText = null, 빈 문자열, 공백만 있는 경우 모두 false를 반환합니다.
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            // "Bearer " (7글자)를 제거하고 순수 JWT 문자열만 반환합니다.
            return bearerToken.substring(7);
        }
        return null;
    }
}
