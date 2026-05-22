package com.racepulse.backend.domain.wallet.dto;

import lombok.Builder;
import lombok.Getter;

// =============================================================================
// SpendResponse.java - 편자 소비 API 응답 DTO
// =============================================================================
// 소비 성공 여부와 남은 잔액을 함께 내려 주면 프론트엔드가 지갑 화면을 바로 갱신할 수 있습니다.
// =============================================================================

@Getter
@Builder
public class SpendResponse {

    private final boolean success;
    private final WalletContentType contentType;
    private final int cost;
    private final int remainingTotal;
    private final int remainingEvent;
    private final int remainingPaid;
}
