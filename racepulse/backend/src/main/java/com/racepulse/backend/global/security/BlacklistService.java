package com.racepulse.backend.global.security;

// =============================================================================
// BlacklistService.java — Access Token 블랙리스트 관리 (Redis)
// =============================================================================
// RefreshTokenService에서 블랙리스트 로직을 분리한 이유:
//   JwtAuthenticationFilter → RefreshTokenService → JwtTokenProvider
//   JwtAuthenticationFilter → JwtTokenProvider
// 위 구조에서 순환 참조(circular dependency) 위험을 방지하기 위해 분리합니다.
// =============================================================================

import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.util.concurrent.TimeUnit;

@Service
@RequiredArgsConstructor
public class BlacklistService {

    private final StringRedisTemplate redisTemplate;
    private static final String BLACKLIST_PREFIX = "blacklist:";

    /**
     * Access Token을 블랙리스트에 등록합니다.
     * remainingSeconds 초 후 Redis에서 자동 삭제됩니다.
     */
    public void add(String accessToken, long remainingSeconds) {
        redisTemplate.opsForValue().set(
                BLACKLIST_PREFIX + accessToken, "logout",
                remainingSeconds, TimeUnit.SECONDS
        );
    }

    /**
     * Access Token이 블랙리스트에 있는지 확인합니다.
     */
    public boolean contains(String accessToken) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(BLACKLIST_PREFIX + accessToken));
    }
}
