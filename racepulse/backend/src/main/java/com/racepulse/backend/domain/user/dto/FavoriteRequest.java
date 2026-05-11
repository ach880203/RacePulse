package com.racepulse.backend.domain.user.dto;

import lombok.Getter;

@Getter
public class FavoriteRequest {
    private String targetType;
    private Long targetId;
}
