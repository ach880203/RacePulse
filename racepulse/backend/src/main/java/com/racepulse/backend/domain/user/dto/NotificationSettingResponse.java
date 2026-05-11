package com.racepulse.backend.domain.user.dto;

// 알림 설정 조회 응답 DTO

import com.racepulse.backend.domain.user.entity.NotificationSetting;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class NotificationSettingResponse {

    private String type;        // 알림 유형 (RACE_START / JOCKEY_CHANGE / RESULT)
    private boolean enabled;    // 알림 ON/OFF 여부
    private String typeLabel;   // 사람이 읽기 쉬운 한글 이름

    /**
     * NotificationSetting Entity를 응답 DTO로 변환합니다.
     */
    public static NotificationSettingResponse from(NotificationSetting setting) {
        return NotificationSettingResponse.builder()
                .type(setting.getType().name())
                .enabled(setting.isEnabled())
                .typeLabel(toLabel(setting.getType().name()))
                .build();
    }

    private static String toLabel(String type) {
        return switch (type) {
            case "RACE_START"    -> "경주 시작 알림";
            case "JOCKEY_CHANGE" -> "기수 변경 알림";
            case "RESULT"        -> "경주 결과 알림";
            default              -> type;
        };
    }
}
