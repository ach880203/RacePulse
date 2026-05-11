package com.racepulse.backend.domain.user.entity;

// =============================================================================
// RefreshToken.java — refresh_tokens 테이블과 매핑되는 Entity 클래스
// =============================================================================
// Refresh Token을 DB에 저장하는 이유:
// 1. 토큰이 만료됐는지, 이미 사용됐는지 서버에서 직접 확인할 수 있습니다.
// 2. Token Family 탈취 감지 기능을 구현할 수 있습니다.
//    (이미 사용된 토큰으로 다시 요청이 오면 → 탈취로 간주 → 전체 무효화)
// =============================================================================

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "refresh_tokens")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class RefreshToken {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 어느 유저의 Refresh Token인지 연결합니다.
    // @JoinColumn = FK 컬럼 이름을 명시합니다.
    // FetchType.LAZY = User 정보를 실제로 필요할 때만 DB에서 가져옵니다 (성능 최적화).
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 보안을 위해 실제 토큰 값 대신 SHA-256 해시를 저장합니다.
    // DB가 유출되더라도 해시 값만 노출되어 원래 토큰을 바로 알 수 없습니다.
    @Column(name = "token_hash", nullable = false, unique = true, length = 64)
    private String tokenHash;

    // family_id: 같은 로그인 세션(로그인 1회)에서 발급된 토큰들을 묶는 그룹 ID입니다.
    // Token Family 탈취 감지에 사용됩니다.
    @Column(name = "family_id", nullable = false, columnDefinition = "uuid")
    private UUID familyId;

    // 이 토큰이 이미 사용됐는지 여부입니다.
    // Refresh Token을 쓸 때마다 is_used=true로 표시하고 새 토큰을 발급합니다.
    @Column(name = "is_used", nullable = false)
    @Builder.Default
    private boolean used = false;

    // 토큰 만료 시각. 이 시각이 지나면 토큰은 무효입니다.
    @Column(name = "expires_at", nullable = false)
    private LocalDateTime expiresAt;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }

    /**
     * 이 토큰을 "사용 완료" 상태로 표시합니다.
     * Token Rotation: Refresh Token 을 쓰면 즉시 무효화하고 새 토큰을 발급합니다.
     */
    public void markAsUsed() {
        this.used = true;
    }
}
