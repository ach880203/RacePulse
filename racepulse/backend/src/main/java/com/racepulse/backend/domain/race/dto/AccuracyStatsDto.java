package com.racepulse.backend.domain.race.dto;

// =============================================================================
// AccuracyStatsDto.java — 대시보드 정확도 통계 응답 DTO
// =============================================================================
// Top-1 정확도란?
//   ML 모델이 1위로 예측한 말이 실제로 1위를 했는지의 비율입니다.
//   예: 100번 예측 중 42번 맞춤 → Top-1 정확도 42%
//
// Top-3 정확도란?
//   ML 모델이 1위로 예측한 말이 실제로 3위 이내에 든 비율입니다.
//   경마는 착순이 유동적이므로 Top-3도 중요한 지표입니다.
// =============================================================================

import lombok.Builder;
import lombok.Getter;

import java.util.List;
import java.util.Map;

@Getter
@Builder
public class AccuracyStatsDto {

    // 전체 예측 건수
    private long totalPredictions;

    // 전체 기간 Top-1 정확도 (%)
    private double top1Accuracy;

    // 전체 기간 Top-3 정확도 (%)
    private double top3Accuracy;

    // 최근 30일 Top-1 정확도 (%)
    private double last30DaysTop1;

    // 경마장별 정확도 (SC/BU/JJ)
    // 예: { "SC": { "top1": 43.0, "top3": 69.1 }, ... }
    private Map<String, MeetAccuracy> byMeetCode;

    // 월별 추이 데이터 (꺾은선 그래프용)
    private List<MonthlyTrend> monthlyTrend;

    // -------------------------------------------------------------------------
    // 중첩 클래스: 경마장별 정확도
    // -------------------------------------------------------------------------
    @Getter
    @Builder
    public static class MeetAccuracy {
        private double top1;
        private double top3;
    }

    // -------------------------------------------------------------------------
    // 중첩 클래스: 월별 추이 데이터 1건
    // -------------------------------------------------------------------------
    @Getter
    @Builder
    public static class MonthlyTrend {
        private String month;   // "2026-01" 형식
        private double top1;
        private double top3;
    }
}
