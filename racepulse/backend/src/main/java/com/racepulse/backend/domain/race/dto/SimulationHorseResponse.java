package com.racepulse.backend.domain.race.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.Map;

@Getter
@Builder
@AllArgsConstructor
public class SimulationHorseResponse {
    private Long horseId;
    private String horseName;
    private Map<String, Double> rankDistribution;
    private Double expectedRank;
}
