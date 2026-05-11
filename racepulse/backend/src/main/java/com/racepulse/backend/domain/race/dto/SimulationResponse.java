package com.racepulse.backend.domain.race.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
public class SimulationResponse {
    private Long raceId;
    private Integer nSimulations;
    private List<SimulationHorseResponse> horses;
    private Double upsetProbability;
    private String computedAt;
}
