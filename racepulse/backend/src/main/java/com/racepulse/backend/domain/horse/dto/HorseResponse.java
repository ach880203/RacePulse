package com.racepulse.backend.domain.horse.dto;

import java.math.BigDecimal;

import com.racepulse.backend.domain.horse.entity.Horse;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// 경주마 목록/상세 API에 맞춘 응답 DTO입니다.
@Getter
@Builder
@AllArgsConstructor
public class HorseResponse {

    private final Long id;
    private final String name;
    private final String engName;
    private final Integer birthYear;
    private final String sex;
    private final String color;
    private final String origin;
    private final String fatherName;
    private final String motherName;
    private final String owner;
    private final String meetCode;
    private final BigDecimal rating1;
    private final BigDecimal rating2;
    private final BigDecimal rating3;
    private final BigDecimal rating4;
    private final Boolean isActive;
    private final String thumbnailUrl;
    private final String photoUrl;

    public static HorseResponse from(Horse horse) {
        return HorseResponse.builder()
                .id(horse.getId())
                .name(horse.getName())
                .engName(horse.getEngName())
                .birthYear(horse.getBirthYear())
                .sex(horse.getSex())
                .color(horse.getColor())
                .origin(horse.getOrigin())
                .fatherName(horse.getFatherName())
                .motherName(horse.getMotherName())
                .owner(horse.getOwner())
                .meetCode(horse.getMeetCode().name())
                .rating1(horse.getRating1())
                .rating2(horse.getRating2())
                .rating3(horse.getRating3())
                .rating4(horse.getRating4())
                .isActive(horse.getIsActive())
                .thumbnailUrl(horse.getThumbnailUrl())
                .photoUrl(horse.getPhotoUrl())
                .build();
    }
}
