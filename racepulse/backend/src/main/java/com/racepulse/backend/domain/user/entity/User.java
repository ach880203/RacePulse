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
import java.time.OffsetDateTime;
import java.time.ZoneId;
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

    // 현재 서비스 중인 약관 버전입니다.
    // 약관 문구가 바뀌면 이 값을 올리고, 기존 유저의 termsVersion과 비교해 재동의가 필요한지 판단합니다.
    public static final String CURRENT_TERMS_VERSION = "1.0";

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

    // 마케팅 정보 수신 동의는 선택 항목입니다.
    // 개인정보보호법에서는 필수 동의(서비스 이용에 꼭 필요한 항목)와 선택 동의를 분리해야 하므로 기본값은 false입니다.
    @Builder.Default
    @Column(name = "marketing_agreed", nullable = false)
    private boolean marketingAgreed = false;

    // OffsetDateTime은 LocalDateTime과 달리 +09:00 같은 타임존 정보를 함께 다룹니다.
    // 동의 시각은 법적/운영 기록에 가까워서 서버 위치가 바뀌어도 같은 순간을 비교할 수 있게 타임존 포함 타입을 사용합니다.
    @Column(name = "terms_agreed_at")
    private OffsetDateTime termsAgreedAt;

    // 유저가 어떤 버전의 약관에 동의했는지 저장합니다.
    // 약관이 1.0에서 1.1로 올라가면 이 값과 CURRENT_TERMS_VERSION을 비교해 재동의 안내를 띄울 수 있습니다.
    @Column(name = "terms_version", length = 10)
    private String termsVersion;

    // @PrePersist = INSERT 직전에 자동으로 호출되는 메서드입니다.
    // createdAt/updatedAt 을 자동으로 채워줍니다.
    @PrePersist
    protected void onCreate() {
        this.createdAt = LocalDateTime.now();
        this.updatedAt = LocalDateTime.now();
    }

    // 이용약관 동의를 기록하는 메서드입니다.
    // 회원가입뿐 아니라 나중에 약관이 개정되어 재동의를 받을 때도 같은 로직을 재사용합니다.
    public void agreeToTerms(boolean marketingAgreed) {
        this.termsAgreedAt = OffsetDateTime.now(ZoneId.of("Asia/Seoul"));
        this.termsVersion = CURRENT_TERMS_VERSION;
        this.marketingAgreed = marketingAgreed;
    }

    // 마케팅 수신 동의만 바꾸는 메서드입니다.
    // 약관 동의 시각은 "약관에 동의한 순간"이므로, 단순 마케팅 ON/OFF 변경 때 덮어쓰지 않습니다.
    public void updateMarketingAgreed(boolean marketingAgreed) {
        this.marketingAgreed = marketingAgreed;
    }
}
