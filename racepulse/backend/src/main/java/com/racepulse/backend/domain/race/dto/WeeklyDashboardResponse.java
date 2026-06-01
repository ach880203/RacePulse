package com.racepulse.backend.domain.race.dto;

import java.time.LocalDate;
import java.util.List;

import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class WeeklyDashboardResponse {

    // 대시보드 화면에서 "이번 주" 기준을 사용자에게 명확히 보여주기 위해 시작일과 종료일을 함께 내려줍니다.
    private final LocalDate weekStart;
    private final LocalDate weekEnd;
    // 통계 숫자는 데이터가 없을 때도 null 대신 0으로 내려가야 화면 계산과 표시가 깨지지 않습니다.
    private final long scheduledRaceCount;
    private final long completedRaceCount;
    private final long predictionCount;
    private final double top1Accuracy;
    private final double top3Accuracy;
    private final List<RaceResponse> upcomingRaces;
    private final List<RaceResponse> recentResults;
}
