package com.racepulse.backend.domain.race.dto;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// =============================================================================
// PredictionItemResponse.java — 예측 결과 페이지에서 말 1마리 정보를 담는 DTO
// =============================================================================
// Entity를 그대로 프런트에 넘기지 않고, 화면에 필요한 값만 모아서 전달합니다.
// 이렇게 분리해두면 DB 컬럼이 바뀌더라도 화면 계약(API 응답 형식)을 안정적으로 유지할 수 있습니다.
// =============================================================================

@Getter
@Builder
@AllArgsConstructor
public class PredictionItemResponse {

    private final Long horseId;
    private final String horseName;
    private final Integer gateNo;
    private final Integer predictedRank;
    private final Double winProbability;
    private final Double placeProbability;
    private final String conditionGrade;
    private final List<String> keyFeatures;
}
