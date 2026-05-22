package com.racepulse.backend.domain.wallet.dto;

import com.racepulse.backend.domain.wallet.entity.TransactionType;

// =============================================================================
// WalletContentType.java - 편자를 소비해서 여는 콘텐츠 종류와 가격
// =============================================================================
// 가격을 Controller에 흩뿌리지 않고 Enum에 모아 두면 가격 변경 시 한 곳만 수정하면 됩니다.
// =============================================================================

public enum WalletContentType {
    TOP_1(35, TransactionType.SPEND_TOP1),
    ENSEMBLE(50, TransactionType.SPEND_ENSEMBLE),
    AI_PRE(25, TransactionType.SPEND_AI_PRE),
    COUNTERFACTUAL(18, TransactionType.SPEND_COUNTERFACTUAL),
    TOP_3(3, TransactionType.SPEND_TOP3),
    AI_POST(3, TransactionType.SPEND_AI_POST),
    STAT(1, TransactionType.SPEND_STAT),
    CHANGE_DETAIL(1, TransactionType.SPEND_CHANGE_DETAIL);

    private final int cost;
    private final TransactionType transactionType;

    WalletContentType(int cost, TransactionType transactionType) {
        this.cost = cost;
        this.transactionType = transactionType;
    }

    public int getCost() {
        return cost;
    }

    public TransactionType getTransactionType() {
        return transactionType;
    }
}
