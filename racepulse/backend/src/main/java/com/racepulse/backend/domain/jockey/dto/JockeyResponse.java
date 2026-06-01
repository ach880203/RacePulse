package com.racepulse.backend.domain.jockey.dto;

import java.math.BigDecimal;

import com.racepulse.backend.domain.jockey.entity.Jockey;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class JockeyResponse {

    private final Long id;
    private final String licenseNo;
    private final String name;
    private final String engName;
    private final Integer birthYear;
    private final Integer debutYear;
    private final String meetCode;
    private final String affiliation;
    private final String photoUrl;
    private final Boolean isActive;
    private final BigDecimal winRateTotal;    // 통산 승률 (0~1)
    private final BigDecimal winRateRecent;   // 최근 승률 (0~1)
    private final BigDecimal placeRateTotal;  // 통산 연대율 (0~1)

    public static JockeyResponse from(Jockey jockey) {
        return JockeyResponse.builder()
                .id(jockey.getId())
                .licenseNo(jockey.getLicenseNo())
                .name(jockey.getName())
                .engName(jockey.getEngName())
                .birthYear(jockey.getBirthYear())
                .debutYear(jockey.getDebutYear())
                .meetCode(jockey.getMeetCode())
                .affiliation(jockey.getAffiliation())
                .photoUrl(jockey.getPhotoUrl())
                .isActive(jockey.getIsActive())
                .winRateTotal(jockey.getWinRateTotal())
                .winRateRecent(jockey.getWinRateRecent())
                .placeRateTotal(jockey.getPlaceRateTotal())
                .build();
    }
}
