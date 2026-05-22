package com.racepulse.backend.domain.wallet.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Getter;

// =============================================================================
// EarnRequest.java - 획득 API 확장용 요청 DTO
// =============================================================================
// 현재 광고 API는 duration 파라미터를 직접 받지만, 이후 요청 본문 방식으로 바꿀 때 재사용할 수 있습니다.
// =============================================================================

@Getter
public class EarnRequest {

    @NotNull(message = "광고 시간은 필수입니다.")
    @Min(value = 1, message = "광고 시간은 1초 이상이어야 합니다.")
    private Integer duration;
}
