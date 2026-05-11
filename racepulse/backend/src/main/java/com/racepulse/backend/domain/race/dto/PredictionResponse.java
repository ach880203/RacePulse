package com.racepulse.backend.domain.race.dto;

import java.util.List;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// =============================================================================
// PredictionResponse.java — 경주별 예측 결과 페이지 전체 응답 DTO
// =============================================================================
// 상단 경주 정보에 필요한 raceName/modelVersion과
// 카드 목록에 필요한 predictions를 한 번에 내려주기 위한 응답 객체입니다.
// =============================================================================

@Getter
@Builder
@AllArgsConstructor
public class PredictionResponse {

    private final Long raceId;
    private final String raceName;
    private final String modelVersion;
    private final Double top1Accuracy;
    private final Double top3Accuracy;
    private final List<PredictionItemResponse> predictions;
}
