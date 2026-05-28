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
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.List;

@Configuration
@EnableWebSecurity
@EnableMethodSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    // JwtAuthenticationFilter = 매 요청에서 JWT를 검증하는 우리가 만든 필터입니다.
    private final JwtAuthenticationFilter jwtAuthenticationFilter;

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // CORS = 프런트(3000)와 백엔드(8080) 출처가 다를 때
                // 브라우저가 응답을 읽어도 되는지 판단하는 규칙입니다.
                // withCredentials=true 로 쿠키를 함께 쓰고 있으므로
                // "*" 가 아니라 정확한 프런트 주소를 허용해야 합니다.
                .cors(Customizer.withDefaults())
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
                                "/api/v1/home",
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
                                "/api/v1/predictions",
                                "/api/v1/predictions/**",
                                "/api/v1/horses",
                                "/api/v1/horses/**",
                                "/api/v1/jockeys",
                                "/api/v1/jockeys/**",
                                "/api/v1/trainers",
                                "/api/v1/trainers/**",
                                "/api/v1/search",
                                "/api/v1/search/**",
                                "/api/v1/privacy",
                                "/api/v1/terms",
                                // 대시보드 통계와 해설은 로그인 없이 공개 조회 가능
                                "/api/v1/dashboard/**",
                                "/api/v1/commentary/**",
                                // 날씨 예보도 공개 조회 가능 (인증 없이 경주 상세에서 표시)
                                "/api/v1/weather/**"
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

    /**
     * CORS 허용 설정.
     * 개발 중에는 Vite 개발 서버 포트가 3000 또는 5173으로 달라질 수 있어 둘 다 허용합니다.
     * 추후 운영 배포 시에는 실제 프런트 도메인만 남기도록 관리해야 합니다.
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        configuration.setAllowedOrigins(List.of(
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173"
        ));
        configuration.setAllowedMethods(List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(List.of("Authorization", "Content-Type", "Accept", "Origin"));
        configuration.setAllowCredentials(true);
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
