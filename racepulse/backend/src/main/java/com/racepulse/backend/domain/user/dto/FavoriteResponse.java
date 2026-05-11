package com.racepulse.backend.domain.user.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class FavoriteResponse {
    private Long id;
    private String targetType;
    private Long targetId;
    private String name;
    private String subText;
}
