package com.racepulse.backend.domain.user.repository;

// =============================================================================
// UserRepository.java — users 테이블을 조회/저장하는 JPA Repository
// =============================================================================
// Repository란? DB와 대화하는 창구 역할을 하는 인터페이스입니다.
// JpaRepository를 상속하면 save(), findById(), delete() 등 기본 메서드를 자동으로 제공합니다.
// =============================================================================

import com.racepulse.backend.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserRepository extends JpaRepository<User, UUID> {

    /**
     * 이메일로 유저를 조회합니다.
     * Optional = 유저가 없을 수도 있으므로 null 대신 Optional로 감쌉니다.
     * 이렇게 하면 NullPointerException 을 예방할 수 있습니다.
     */
    Optional<User> findByEmail(String email);

    /**
     * 카카오 유저 고유 ID로 유저를 조회합니다.
     * 카카오 로그인 콜백 처리 시: 이미 가입된 카카오 유저인지 확인할 때 사용합니다.
     */
    Optional<User> findByKakaoId(String kakaoId);

    /**
     * 이메일이 이미 DB에 존재하는지 확인합니다.
     * 회원가입 시 중복 이메일 검사에 사용합니다.
     */
    boolean existsByEmail(String email);
}
