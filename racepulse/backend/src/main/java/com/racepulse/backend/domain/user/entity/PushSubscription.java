package com.racepulse.backend.domain.user.entity;

// =============================================================================
// PushSubscription.java — push_subscriptions 테이블과 매핑되는 Entity
// =============================================================================
// 브라우저가 구독할 때 보내는 정보를 DB에 저장합니다.
//
// Web Push 동작 원리:
//   브라우저 ──→ 구독 정보(endpoint + 키) ──→ 우리 서버 (여기에 저장)
//   이벤트 발생 → 우리 서버 ──→ Push 서버(Google/Mozilla) ──→ 브라우저 알림창
//
// endpoint: 브라우저가 Push 서버에서 발급받은 고유 URL입니다.
//   예: https://fcm.googleapis.com/fcm/send/eXAm...
//   우리가 이 주소로 HTTP POST를 보내면 브라우저에 알림이 전달됩니다.
//
// p256dh_key: 메시지를 암호화하는 ECDH 공개키입니다.
//   우리 서버가 이 키로 메시지를 암호화 → 브라우저만 복호화 가능합니다.
//
// auth_key: 메시지를 인증하는 대칭키입니다.
//   브라우저가 "우리가 구독한 곳에서 온 메시지"인지 확인하는 데 씁니다.
// =============================================================================

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "push_subscriptions")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@AllArgsConstructor
@Builder
public class PushSubscription {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // 어느 유저의 구독인지 연결합니다.
    // FetchType.LAZY = User 정보가 필요할 때만 DB에서 가져옵니다.
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 브라우저가 Push 서버에서 발급받은 고유 URL
    // 이 주소로 HTTP 요청을 보내면 해당 브라우저에 알림이 도착합니다.
    @Column(nullable = false, unique = true, columnDefinition = "text")
    private String endpoint;

    // 메시지 암호화에 사용하는 ECDH 공개키 (Base64url 인코딩)
    @Column(name = "p256dh_key", nullable = false, length = 255)
    private String p256dhKey;

    // 메시지 인증에 사용하는 대칭키 (Base64url 인코딩)
    @Column(name = "auth_key", nullable = false, length = 255)
    private String authKey;

    // 어느 브라우저/기기인지 기록합니다 (Chrome, Firefox, Safari 등)
    @Column(name = "user_agent", length = 500)
    private String userAgent;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
    }
}
