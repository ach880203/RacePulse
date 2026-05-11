package com.racepulse.backend.domain.user.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class PreferenceResponse {
    private String theme;
    private String nickname;
}
