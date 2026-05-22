package com.racepulse.backend.domain.wallet.entity;

import com.racepulse.backend.domain.user.entity.User;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AccessLevel;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

import java.time.OffsetDateTime;

// =============================================================================
// WalletTransaction.java - 편자/건초 증감 내역을 남기는 감사 로그 Entity
// =============================================================================
// 지갑 잔액은 현재 상태이고, 거래 내역은 "언제 왜 잔액이 바뀌었는지"를 남기는 기록입니다.
// 이 테이블은 삭제하지 않고 계속 쌓아야 나중에 문의, 정산, 오류 분석을 할 수 있습니다.
// =============================================================================

@Entity
@Table(name = "wallet_transactions")
@Getter
@Builder
@AllArgsConstructor
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class WalletTransaction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // @ManyToOne = "거래 내역 여러 개가 유저 1명에게 속한다"는 다대일 관계입니다.
    // 한 유저는 출석, 광고, 소비 등 여러 거래 기록을 계속 만들 수 있습니다.
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 거래 종류는 Enum으로 저장해 문자열 오타를 막고, 통계 기준값을 안정적으로 유지합니다.
    @Enumerated(EnumType.STRING)
    @Column(name = "transaction_type", nullable = false, length = 30)
    private TransactionType transactionType;

    // EVENT, PAID, HAY 중 어떤 재화가 변했는지 기록합니다.
    @Enumerated(EnumType.STRING)
    @Column(name = "currency_type", nullable = false, length = 10)
    private CurrencyType currencyType;

    // 양수는 획득, 음수는 소비입니다. DB CHECK 제약으로 0원 거래는 저장하지 않습니다.
    @Column(nullable = false)
    private int amount;

    // balanceAfter를 저장하는 이유:
    // 나중에 "이 거래 직후 잔액이 얼마였는지"를 매번 처음부터 재계산하지 않고 바로 알 수 있습니다.
    @Column(name = "balance_after", nullable = false)
    private int balanceAfter;

    // 운영자가 거래 내역을 읽을 때 이해할 수 있도록 짧은 설명을 남깁니다.
    @Column(length = 200)
    private String description;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = OffsetDateTime.now();
    }
}
