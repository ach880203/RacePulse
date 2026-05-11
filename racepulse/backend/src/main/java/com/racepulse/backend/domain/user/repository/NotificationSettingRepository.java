package com.racepulse.backend.domain.user.repository;

// =============================================================================
// NotificationSettingRepository.java — notification_settings 테이블 Repository
// =============================================================================

import com.racepulse.backend.domain.user.entity.NotificationSetting;
import com.racepulse.backend.domain.user.entity.NotificationType;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface NotificationSettingRepository extends JpaRepository<NotificationSetting, Long> {

    /**
     * 특정 유저의 모든 알림 설정을 조회합니다.
     */
    List<NotificationSetting> findByUserId(UUID userId);

    /**
     * 특정 유저의 특정 알림 유형 설정을 조회합니다.
     */
    Optional<NotificationSetting> findByUserIdAndType(UUID userId, NotificationType type);
}
