package com.racepulse.backend.domain.user.entity;

// =============================================================================
// NotificationSetting.java — notification_settings 테이블과 매핑되는 Entity
// =============================================================================
// 유저가 어떤 종류의 알림을 받을지 개인 설정을 저장합니다.
// 예: 경주 결과 알림은 ON, 기수 변경 알림은 OFF 등 개별 설정이 가능합니다.
// =============================================================================

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;

@Entity
@Table(
        name = "notification_settings",
        // 같은 유저가 같은 알림 유형을 중복 등록하지 못하도록 유니크 제약을 겁니다.
        uniqueConstraints = @UniqueConstraint(columnNames = {"user_id", "type"})
)
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class NotificationSetting {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // @Enumerated(EnumType.STRING) = Enum 값을 숫자가 아닌 문자열로 저장합니다.
    // 예: RACE_START, JOCKEY_CHANGE, RESULT
    @Enumerated(EnumType.STRING)
    @Column(nullable = false, columnDefinition = "notification_type")
    private NotificationType type;

    // true = 이 알림 유형 받기 ON, false = OFF
    @Column(name = "is_enabled", nullable = false)
    @Builder.Default
    private boolean enabled = true;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    // @UpdateTimestamp = 레코드가 수정될 때 자동으로 현재 시각이 저장됩니다.
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    /**
     * 알림 설정을 켜거나 끕니다.
     */
    public void updateEnabled(boolean enabled) {
        this.enabled = enabled;
    }
}
