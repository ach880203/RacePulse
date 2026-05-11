package com.racepulse.backend.domain.user.entity;

// =============================================================================
// User.java — users 테이블과 매핑되는 JPA Entity 클래스
// =============================================================================
// Entity란? DB 테이블 한 행(row)에 해당하는 Java 클래스입니다.
// @Entity 를 붙이면 JPA가 이 클래스를 DB 테이블과 연결해줍니다.
// =============================================================================

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.UpdateTimestamp;

import java.time.LocalDateTime;
import java.util.UUID;

// @Entity = JPA가 이 클래스를 DB 테이블과 연결한다는 선언입니다.
@Entity
// @Table = 연결할 DB 테이블 이름을 명시합니다.
@Table(name = "users")
// @Getter = 모든 필드의 getter 메서드를 Lombok이 자동 생성합니다.
@Getter
// @NoArgsConstructor = 매개변수 없는 기본 생성자를 Lombok이 자동 생성합니다.
//   JPA는 반드시 기본 생성자가 필요합니다.
@NoArgsConstructor(access = AccessLevel.PROTECTED)
// @AllArgsConstructor, @Builder = 빌더 패턴으로 객체를 생성할 수 있게 합니다.
@AllArgsConstructor
@Builder
public class User {

    // @Id = 이 필드가 기본 키(PK)라는 뜻입니다.
    // @GeneratedValue(strategy = GenerationType.AUTO) = JPA가 UUID를 자동 생성합니다.
    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    @Column(columnDefinition = "uuid")
    private UUID id;

    // nullable = false → 이메일은 반드시 있어야 합니다.
    // unique = true → 같은 이메일로 두 계정을 만들 수 없습니다.
    @Column(nullable = false, unique = true, length = 255)
    private String email;

    // 카카오 유저는 비밀번호가 없으므로 nullable 허용합니다.
    @Column(length = 255)
    private String password;

    // 카카오에서 발급한 유저 고유 ID (문자열 숫자, 예: "1234567890")
    @Column(name = "kakao_id", unique = true, length = 100)
    private String kakaoId;

    // @Enumerated(EnumType.STRING) = Enum 값을 숫자(0,1,2)가 아닌 문자열(LOCAL, KAKAO)로 저장합니다.
    // 숫자로 저장하면 Enum 순서가 바뀔 때 의미가 틀려질 수 있어 문자열이 안전합니다.
    @Enumerated(EnumType.STRING)
    @Column(name = "auth_provider", nullable = false, length = 20,
            columnDefinition = "auth_provider")
    private AuthProvider authProvider;

    @Column(nullable = false, length = 50)
    private String nickname;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10, columnDefinition = "user_role")
    @Builder.Default
    private UserRole role = UserRole.USER;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10, columnDefinition = "user_tier")
    @Builder.Default
    private UserTier tier = UserTier.FREE;

    // @Column(updatable = false) = 최초 생성 후 절대 변경되지 않는 컬럼임을 JPA에 알립니다.
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    // @UpdateTimestamp = 레코드가 수정될 때 Hibernate가 자동으로 현재 시각을 넣어줍니다.
    @UpdateTimestamp
    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    // @PrePersist = INSERT 직전에 자동으로 호출되는 메서드입니다.
    // createdAt/updatedAt 을 자동으로 채워줍니다.
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }
}
