package com.racepulse.backend.domain.wallet.dto;

import com.racepulse.backend.domain.wallet.entity.UserWallet;
import lombok.Builder;
import lombok.Getter;

import java.time.OffsetDateTime;

// =============================================================================
// WalletResponse.java - 지갑 조회 API 응답 DTO
// =============================================================================
// Entity를 API에 직접 내보내지 않고 DTO로 바꾸는 이유:
// DB 구조가 바뀌어도 API 응답 모양을 안정적으로 유지하고, 불필요한 내부 필드 노출을 막기 위해서입니다.
// =============================================================================

@Getter
@Builder
public class WalletResponse {

    private final int eventHorseshoe;
    private final OffsetDateTime eventHorseshoeExpiresAt;
    private final int paidHorseshoe;
    private final int totalHorseshoe;
    private final int hay;
    private final int todayAdEarned;
    private final int todayAdLimit;

    public static WalletResponse from(UserWallet wallet, int todayAdEarned, int todayAdLimit) {
        return WalletResponse.builder()
                .eventHorseshoe(wallet.getEventHorseshoe())
                .eventHorseshoeExpiresAt(wallet.getEventHorseshoeExpiresAt())
                .paidHorseshoe(wallet.getPaidHorseshoe())
                .totalHorseshoe(wallet.getTotalHorseshoe())
                .hay(wallet.getHay())
                .todayAdEarned(todayAdEarned)
                .todayAdLimit(todayAdLimit)
                .build();
    }
}
