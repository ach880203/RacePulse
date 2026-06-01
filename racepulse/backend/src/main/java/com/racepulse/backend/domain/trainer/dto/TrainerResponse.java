package com.racepulse.backend.domain.trainer.dto;

import java.math.BigDecimal;

import com.racepulse.backend.domain.trainer.entity.Trainer;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class TrainerResponse {

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
    private final BigDecimal winRateTotal;
    private final BigDecimal winRateRecent;

    public static TrainerResponse from(Trainer trainer) {
        return TrainerResponse.builder()
                .id(trainer.getId())
                .licenseNo(trainer.getLicenseNo())
                .name(trainer.getName())
                .engName(trainer.getEngName())
                .birthYear(trainer.getBirthYear())
                .debutYear(trainer.getDebutYear())
                .meetCode(trainer.getMeetCode())
                .affiliation(trainer.getAffiliation())
                .photoUrl(trainer.getPhotoUrl())
                .isActive(trainer.getIsActive())
                .winRateTotal(trainer.getWinRateTotal())
                .winRateRecent(trainer.getWinRateRecent())
                .build();
    }
}
