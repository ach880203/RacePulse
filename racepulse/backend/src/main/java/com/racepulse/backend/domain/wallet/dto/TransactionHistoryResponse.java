package com.racepulse.backend.domain.wallet.dto;

import com.racepulse.backend.domain.wallet.entity.CurrencyType;
import com.racepulse.backend.domain.wallet.entity.TransactionType;
import com.racepulse.backend.domain.wallet.entity.WalletTransaction;
import lombok.Builder;
import lombok.Getter;

import java.time.OffsetDateTime;

// =============================================================================
// TransactionHistoryResponse.java - 거래 내역 한 줄을 내려 주는 응답 DTO
// =============================================================================
// 거래 내역 Entity에는 User 연결 정보가 있지만 API에는 필요한 거래 정보만 골라서 내려줍니다.
// =============================================================================

@Getter
@Builder
public class TransactionHistoryResponse {

    private final Long id;
    private final TransactionType transactionType;
    private final CurrencyType currencyType;
    private final int amount;
    private final int balanceAfter;
    private final String description;
    private final OffsetDateTime createdAt;

    public static TransactionHistoryResponse from(WalletTransaction transaction) {
        return TransactionHistoryResponse.builder()
                .id(transaction.getId())
                .transactionType(transaction.getTransactionType())
                .currencyType(transaction.getCurrencyType())
                .amount(transaction.getAmount())
                .balanceAfter(transaction.getBalanceAfter())
                .description(transaction.getDescription())
                .createdAt(transaction.getCreatedAt())
                .build();
    }
}
