package com.racepulse.backend.domain.horse.dto;

import java.math.BigDecimal;

import com.racepulse.backend.domain.horse.entity.Horse;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// 경주마 목록 API에 맞춘 응답 DTO입니다.
@Getter
@Builder
@AllArgsConstructor
public class HorseResponse {

    private final Long id;
    private final String name;
    private final String engName;
    private final String meetCode;
    private final String sex;
    private final BigDecimal rating1;
    private final Boolean isActive;
    private final String thumbnailUrl;

    public static HorseResponse from(Horse horse) {
        return HorseResponse.builder()
                .id(horse.getId())
                .name(horse.getName())
                .engName(horse.getEngName())
                .meetCode(horse.getMeetCode().name())
                .sex(horse.getSex())
                .rating1(horse.getRating1())
                .isActive(horse.getIsActive())
                .thumbnailUrl(horse.getThumbnailUrl())
                .build();
    }
}
