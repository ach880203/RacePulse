package com.racepulse.backend.domain.change.dto;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

// =============================================================================
// ChangeResponse.java — 변경 감지 API 응답 DTO 모음
// =============================================================================
// record는 읽기 전용 응답 값을 간결하게 표현할 때 적합합니다.
// 엔티티를 그대로 반환하지 않고 DTO를 두면 DB 구조가 바뀌어도 API 모양을 보호할 수 있습니다.
// =============================================================================

public final class ChangeResponse {

    private ChangeResponse() {
    }

    public record RaceChanges(
            Long raceId,
            boolean hasChanges,
            List<ChangeItem> changes
    ) {
    }

    public record TodayChanges(
            LocalDate date,
            int totalCount,
            int highImpactCount,
            List<ChangeItem> changes
    ) {
    }

    public record ChangeItem(
            String type,
            String badge,
            String impact,
            Long raceId,
            Long horseId,
            String horseName,
            String oldValue,
            String newValue,
            Boolean blinkerFirstTime,
            OffsetDateTime detectedAt
    ) {
    }

    public record SubscribeResult(
            boolean subscribed
    ) {
    }
}
