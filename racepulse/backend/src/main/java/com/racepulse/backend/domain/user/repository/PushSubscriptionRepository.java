package com.racepulse.backend.domain.user.repository;

// =============================================================================
// PushSubscriptionRepository.java — push_subscriptions 테이블 Repository
// =============================================================================

import com.racepulse.backend.domain.user.entity.PushSubscription;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.UUID;

public interface PushSubscriptionRepository extends JpaRepository<PushSubscription, Long> {

    /**
     * 특정 유저의 모든 구독 정보를 조회합니다.
     * 유저가 여러 기기(PC, 스마트폰)에서 구독할 수 있으므로 List로 반환합니다.
     */
    List<PushSubscription> findByUserId(UUID userId);

    /**
     * 특정 유저의 특정 endpoint 구독을 삭제합니다.
     * 유저가 "이 기기에서 알림 끄기"를 하면 해당 구독만 삭제합니다.
     */
    @Modifying
    @Query("DELETE FROM PushSubscription ps WHERE ps.user.id = :userId AND ps.endpoint = :endpoint")
    void deleteByUserIdAndEndpoint(@Param("userId") UUID userId, @Param("endpoint") String endpoint);

    /**
     * 특정 유저의 모든 구독을 삭제합니다. (회원 탈퇴 또는 전체 알림 끄기)
     */
    @Modifying
    @Query("DELETE FROM PushSubscription ps WHERE ps.user.id = :userId")
    void deleteAllByUserId(@Param("userId") UUID userId);

    /**
     * endpoint 로 구독 여부를 확인합니다. (중복 구독 방지)
     */
    boolean existsByEndpoint(String endpoint);
}
