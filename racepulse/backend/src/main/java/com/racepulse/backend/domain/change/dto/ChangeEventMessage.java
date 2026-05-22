package com.racepulse.backend.domain.change.dto;

import java.time.OffsetDateTime;

import com.fasterxml.jackson.annotation.JsonAlias;

import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

// =============================================================================
// ChangeEventMessage.java — Redis 변경 감지 이벤트 수신 DTO
// =============================================================================
// Redis Pub/Sub 메시지는 ML 서버나 배치 작업에서 JSON 문자열로 들어옵니다.
// @JsonAlias는 snake_case(race_id)와 camelCase(raceId)를 모두 받아 주기 위한 장치입니다.
// 이벤트 발행 주체가 달라져도 백엔드 수신 코드가 쉽게 깨지지 않도록 방어합니다.
// =============================================================================

@Getter
@Setter
@NoArgsConstructor
public class ChangeEventMessage {

    private String type;

    @JsonAlias("race_id")
    private Long raceId;

    @JsonAlias("horse_id")
    private Long horseId;

    @JsonAlias("horse_name")
    private String horseName;

    @JsonAlias("old_value")
    private String oldValue;

    @JsonAlias("new_value")
    private String newValue;

    @JsonAlias("detected_at")
    private OffsetDateTime detectedAt;
}
