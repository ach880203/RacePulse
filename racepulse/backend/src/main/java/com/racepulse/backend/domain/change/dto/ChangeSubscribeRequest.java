package com.racepulse.backend.domain.change.dto;

import jakarta.validation.constraints.NotNull;

// =============================================================================
// ChangeSubscribeRequest.java — 변경 알림 구독 요청 DTO
// =============================================================================
// subscribe=true  : 해당 경주의 변경 알림을 받습니다.
// subscribe=false : 해당 경주의 변경 알림을 해제합니다.
// Boolean으로 받은 뒤 @NotNull을 붙인 이유는 값 누락과 false를 정확히 구분하기 위해서입니다.
// =============================================================================

public record ChangeSubscribeRequest(
        @NotNull Boolean subscribe
) {
}
