package com.racepulse.backend.domain.race.dto;

import java.time.LocalDate;
import java.time.LocalTime;

import com.racepulse.backend.domain.race.entity.Race;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// 경주 목록 화면에 필요한 최소 필드만 담는 응답 DTO입니다.
@Getter
@Builder
@AllArgsConstructor
public class RaceResponse {

    private final Long id;
    private final String meetCode;
    private final LocalDate rcDate;
    private final Integer raceNo;
    private final String raceName;
    private final Integer distance;
    private final String status;
    private final LocalTime startTime;

    public static RaceResponse from(Race race) {
        return RaceResponse.builder()
                .id(race.getId())
                .meetCode(race.getMeetCode().name())
                .rcDate(race.getRcDate())
                .raceNo(race.getRaceNo())
                .raceName(race.getRaceName())
                .distance(race.getDistance())
                .status(race.getStatus().name())
                .startTime(race.getStartTime())
                .build();
    }
}
