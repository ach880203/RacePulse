package com.racepulse.backend.domain.user.service;

// =============================================================================
// AuthService.java — 이메일 회원가입/로그인 처리 서비스
// =============================================================================

import com.racepulse.backend.domain.user.dto.AuthResponse;
import com.racepulse.backend.domain.user.dto.LoginRequest;
import com.racepulse.backend.domain.user.dto.RegisterRequest;
import com.racepulse.backend.domain.user.entity.AuthProvider;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final KakaoOAuthService kakaoOAuthService;
    private final StringRedisTemplate redisTemplate;

    // Rate Limiting 설정: 로그인 5회 실패 → 15분 잠금
    private static final int MAX_LOGIN_ATTEMPTS = 5;
    private static final long LOCK_DURATION_MINUTES = 15;
    private static final String LOGIN_FAIL_PREFIX = "login:fail:";
    private static final String LOGIN_LOCK_PREFIX = "login:lock:";

    /**
     * 이메일 회원가입을 처리합니다.
     */
    @Transactional
    public AuthResponse register(RegisterRequest request) {
        // 이메일 중복 확인
        if (userRepository.existsByEmail(request.getEmail())) {
            throw new BusinessException(ErrorCode.EMAIL_DUPLICATE);
        }

        // 이용약관 동의는 필수입니다.
        // DTO의 @NotNull이 누락값을 막고, 여기서는 false로 보낸 경우까지 확실히 거부합니다.
        if (!Boolean.TRUE.equals(request.getTermsAgreed())) {
            throw new BusinessException(ErrorCode.TERMS_NOT_AGREED);
        }

        // 비밀번호를 BCrypt 해시로 암호화합니다.
        // BCrypt란? 비밀번호를 단방향 해시로 저장하는 안전한 방식입니다.
        // 원래 비밀번호는 절대 저장하지 않습니다.
        String encodedPassword = passwordEncoder.encode(request.getPassword());

        User user = User.builder()
                .email(request.getEmail())
                .password(encodedPassword)
                .nickname(request.getNickname())
                .authProvider(AuthProvider.LOCAL)
                .build();

        // 마케팅 동의는 선택값이라 null이면 false로 처리합니다.
        // 약관 동의 시각과 약관 버전은 User 엔티티의 메서드에서 한 번에 기록합니다.
        user.agreeToTerms(Boolean.TRUE.equals(request.getMarketingAgreed()));

        User saved = userRepository.save(user);
        log.info("신규 이메일 회원가입. userId={}", saved.getId());

        // 회원가입 후 바로 로그인 처리
        return kakaoOAuthService.issueTokens(saved, false);
    }

    /**
     * 이메일 로그인을 처리합니다.
     * Rate Limiting: 5회 실패 시 15분 잠금
     */
    public AuthResponse login(LoginRequest request) {
        String email = request.getEmail();

        // 잠금 상태 확인
        if (isLocked(email)) {
            throw new IllegalStateException("로그인 시도가 너무 많습니다. 15분 후 다시 시도해주세요.");
        }

        // 유저 조회
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> {
                    incrementFailCount(email);
                    return new IllegalArgumentException("이메일 또는 비밀번호가 올바르지 않습니다.");
                });

        // 카카오 전용 계정으로 이메일 로그인 시도
        if (user.getAuthProvider() == AuthProvider.KAKAO) {
            throw new IllegalArgumentException("카카오 계정으로 가입된 이메일입니다. 카카오 로그인을 이용해주세요.");
        }

        // 비밀번호 검증 (BCrypt 해시 비교)
        if (!passwordEncoder.matches(request.getPassword(), user.getPassword())) {
            incrementFailCount(email);
            throw new IllegalArgumentException("이메일 또는 비밀번호가 올바르지 않습니다.");
        }

        // 로그인 성공 → 실패 카운터 초기화
        clearFailCount(email);
        log.info("이메일 로그인 성공. userId={}", user.getId());

        return kakaoOAuthService.issueTokens(user, request.isRememberMe());
    }

    // =========================================================================
    // Rate Limiting 관련 메서드 (Redis)
    // =========================================================================

    private boolean isLocked(String email) {
        return Boolean.TRUE.equals(redisTemplate.hasKey(LOGIN_LOCK_PREFIX + email));
    }

    private void incrementFailCount(String email) {
        String key = LOGIN_FAIL_PREFIX + email;
        Long count = redisTemplate.opsForValue().increment(key);

        // 처음 실패 시 TTL(만료시간)을 설정합니다.
        if (count != null && count == 1) {
            redisTemplate.expire(key, LOCK_DURATION_MINUTES, TimeUnit.MINUTES);
        }

        // 5회 실패 → 잠금 처리
        if (count != null && count >= MAX_LOGIN_ATTEMPTS) {
            redisTemplate.opsForValue().set(
                    LOGIN_LOCK_PREFIX + email, "locked",
                    LOCK_DURATION_MINUTES, TimeUnit.MINUTES
            );
            redisTemplate.delete(key);
            log.warn("로그인 5회 실패로 계정 잠금. email={}", email);
        }
    }

    private void clearFailCount(String email) {
        redisTemplate.delete(LOGIN_FAIL_PREFIX + email);
        redisTemplate.delete(LOGIN_LOCK_PREFIX + email);
    }
}
