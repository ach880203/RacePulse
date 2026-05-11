package com.racepulse.backend.global.config;

// =============================================================================
// SecurityConfig.java — Spring Security 전체 보안 설정
// =============================================================================
// Spring Security Filter Chain이란?
//   모든 HTTP 요청이 Controller에 도달하기 전에 거치는 보안 관문(필터) 목록입니다.
//   우리가 만든 JwtAuthenticationFilter도 이 체인에 등록합니다.
//
// 필터 실행 순서 (앞 → 뒤):
//   ... → JwtAuthenticationFilter → UsernamePasswordAuthenticationFilter → ...
//   JWT 필터를 앞에 넣어야 JWT 인증이 먼저 처리됩니다.
// =============================================================================

import com.racepulse.backend.global.security.JwtAuthenticationFilter;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.client.RestTemplate;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    // JwtAuthenticationFilter = 매 요청에서 JWT를 검증하는 우리가 만든 필터입니다.
    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // CSRF = 브라우저 폼 요청 위조 방지 기능. REST API + JWT 구조에서는 비활성화합니다.
                .csrf(AbstractHttpConfigurer::disable)

                // STATELESS = 서버가 세션을 유지하지 않습니다.
                // JWT 토큰으로만 인증하므로 세션이 필요 없습니다.
                .sessionManagement(session ->
                        session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                .authorizeHttpRequests(auth -> auth
                        // 인증 없이 접근 가능한 경로들
                        .requestMatchers(
                                "/api/v1/health",
                                "/api/v1/auth/**",          // 로그인, 회원가입, 카카오 OAuth
                                "/api/v1/push/vapid-public-key", // VAPID 공개키는 인증 없이 조회 가능
                                "/swagger-ui/**",
                                "/swagger-ui.html",
                                "/api-docs/**",
                                "/v3/api-docs/**"
                        ).permitAll()

                        // GET 요청만 인증 없이 허용하는 공개 조회 API
                        .requestMatchers(
                                HttpMethod.GET,
                                "/api/v1/racecourses",
                                "/api/v1/racecourses/**",
                                "/api/v1/races",
                                "/api/v1/races/**",
                                "/api/v1/horses",
                                "/api/v1/horses/**",
                                // 대시보드 통계와 해설은 로그인 없이 공개 조회 가능
                                "/api/v1/dashboard/**",
                                "/api/v1/commentary/**"
                        ).permitAll()

                        // 나머지 모든 요청은 JWT 인증 필요
                        .anyRequest().authenticated()
                )

                // JWT 필터를 UsernamePasswordAuthenticationFilter 앞에 삽입합니다.
                // 이렇게 해야 JWT가 먼저 처리되고 Spring 기본 인증 필터보다 앞서 실행됩니다.
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * PasswordEncoder Bean 등록.
     * BCrypt = 비밀번호를 단방향 해시로 변환하는 강력한 알고리즘입니다.
     * 같은 비밀번호라도 매번 다른 해시값이 나옵니다 (salt 자동 생성).
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /**
     * RestTemplate Bean 등록.
     * KakaoOAuthService에서 카카오 서버로 HTTP 요청을 보낼 때 사용합니다.
     */
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
