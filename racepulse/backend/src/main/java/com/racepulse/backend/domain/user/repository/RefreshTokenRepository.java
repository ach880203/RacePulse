package com.racepulse.backend.domain.user.repository;

// =============================================================================
// RefreshTokenRepository.java — refresh_tokens 테이블 Repository
// =============================================================================

import com.racepulse.backend.domain.user.entity.RefreshToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.UUID;

public interface RefreshTokenRepository extends JpaRepository<RefreshToken, Long> {

    /**
     * 토큰 해시로 Refresh Token을 조회합니다.
     * 클라이언트가 보낸 토큰을 해시로 변환한 후 이 메서드로 DB와 비교합니다.
     */
    Optional<RefreshToken> findByTokenHash(String tokenHash);

    /**
     * 특정 family_id에 속한 모든 토큰을 삭제합니다.
     * 탈취 감지 시: 같은 로그인 세션의 토큰을 전부 무효화할 때 사용합니다.
     *
     * @Modifying = 데이터를 변경(DELETE/UPDATE)하는 쿼리임을 JPA에 알립니다.
     * @Query = JPQL(Java 객체 기반 SQL)로 직접 쿼리를 작성합니다.
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.familyId = :familyId")
    void deleteAllByFamilyId(@Param("familyId") UUID familyId);

    /**
     * 만료된 Refresh Token을 모두 삭제합니다. (정기 정리용)
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.expiresAt < :now")
    void deleteAllExpired(@Param("now") LocalDateTime now);

    /**
     * 특정 유저의 모든 Refresh Token을 삭제합니다. (로그아웃 처리)
     */
    @Modifying
    @Query("DELETE FROM RefreshToken rt WHERE rt.user.id = :userId")
    void deleteAllByUserId(@Param("userId") UUID userId);
}
