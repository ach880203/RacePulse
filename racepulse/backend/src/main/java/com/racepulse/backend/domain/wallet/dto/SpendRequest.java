package com.racepulse.backend.domain.wallet.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Getter;

// =============================================================================
// SpendRequest.java - 편자 소비 API 요청 DTO
// =============================================================================
// contentType은 어떤 유료 콘텐츠를 열람하려는지 나타냅니다.
// raceId는 나중에 "어느 경주에서 사용했는지" 추적할 수 있도록 함께 받습니다.
// =============================================================================

@Getter
public class SpendRequest {

    @NotNull(message = "콘텐츠 종류는 필수입니다.")
    private WalletContentType contentType;

    private Long raceId;
}
