package com.racepulse.backend.domain.wallet.entity;

// JPA 어노테이션 모음입니다. Entity, Table, Column처럼 DB 테이블과 Java 클래스를 연결할 때 씁니다.
import com.racepulse.backend.domain.user.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.PreUpdate;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

// =============================================================================
// UserWallet.java - users 테이블과 1:1로 연결되는 편자 지갑 Entity
// =============================================================================
// @Entity = 이 Java 클래스가 DB 테이블과 연결되는 JPA Entity라는 뜻입니다.
// @Table(name = "user_wallets") = 실제 DB 테이블 이름은 user_wallets를 사용합니다.
// =============================================================================

@Entity
@Table(name = "user_wallets")
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class UserWallet {

    // @Id = DB 기본키(PK)입니다. 각 지갑 row를 구분하는 고유 번호입니다.
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // @OneToOne = "유저 1명은 지갑 1개만 가진다"는 1대1 관계입니다.
    // unique = true 제약도 함께 걸려 있어 같은 유저에게 지갑이 2개 생기는 일을 DB에서 막습니다.
    @OneToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    // 이벤트 편자는 출석, 광고, 퀴즈로 얻는 앱 내 재화입니다.
    // 현금으로 환급되지 않고 앱 안의 콘텐츠 열람에만 쓰이므로 현금 가치가 있는 재산으로 보지 않습니다.
    @Column(name = "event_horseshoe", nullable = false)
    @Builder.Default
    private int eventHorseshoe = 0;

    // 이벤트 편자 만료 시각입니다. 이벤트 편자는 6개월 만료가 있어 구매 편자보다 먼저 소비합니다.
    @Column(name = "event_horseshoe_expires_at")
    private OffsetDateTime eventHorseshoeExpiresAt;

    // 구매 편자는 결제로 얻는 앱 내 재화입니다. 만료가 없으므로 이벤트 편자를 모두 쓴 뒤 소비합니다.
    @Column(name = "paid_horseshoe", nullable = false)
    @Builder.Default
    private int paidHorseshoe = 0;

    // 건초는 다마고치 전용 재화입니다. 편자와 교환하지 못하게 분리해 과금 재화와 보상 재화를 섞지 않습니다.
    @Column(name = "hay", nullable = false)
    @Builder.Default
    private int hay = 0;

    // 생성/수정 시각은 DB 기본값도 있지만, JPA로 저장할 때도 명확히 채워 둡니다.
    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    // 총 보유 편자는 이벤트 편자와 구매 편자의 합입니다.
    public int getTotalHorseshoe() {
        return this.eventHorseshoe + this.paidHorseshoe;
    }

    // 이벤트 편자를 더합니다. 새로 받은 이벤트 편자는 받은 날부터 6개월 뒤 만료됩니다.
    public void addEventHorseshoe(int amount, OffsetDateTime expiresAt) {
        this.eventHorseshoe += amount;
        this.eventHorseshoeExpiresAt = expiresAt;
    }

    // 구매 편자를 더합니다. 결제 연동은 Phase 4에서 붙지만 지갑 로직은 미리 준비합니다.
    public void addPaidHorseshoe(int amount) {
        this.paidHorseshoe += amount;
    }

    // 건초를 더합니다. 건초는 편자와 별도로 관리합니다.
    public void addHay(int amount) {
        this.hay += amount;
    }

    // 이벤트 편자를 차감합니다. 서비스에서 부족 여부를 먼저 검사하므로 여기서는 실제 반영만 합니다.
    public void subtractEventHorseshoe(int amount) {
        this.eventHorseshoe -= amount;
    }

    // 구매 편자를 차감합니다. 잔액이 음수가 되지 않도록 서비스와 DB CHECK 제약에서 이중으로 막습니다.
    public void subtractPaidHorseshoe(int amount) {
        this.paidHorseshoe -= amount;
    }

    @PrePersist
    protected void onCreate() {
        OffsetDateTime now = OffsetDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = OffsetDateTime.now();
    }
}
