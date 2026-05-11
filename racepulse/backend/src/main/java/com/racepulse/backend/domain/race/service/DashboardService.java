package com.racepulse.backend.domain.race.service;

// =============================================================================
// DashboardService.java — 대시보드 정확도 통계를 계산하는 서비스
// =============================================================================
// predictions 테이블은 ML 서버(FastAPI)가 채우지만,
// Spring Boot와 ML 서버가 같은 PostgreSQL DB를 공유하므로
// Spring Boot에서도 JdbcTemplate으로 직접 조회할 수 있습니다.
//
// 데이터가 아직 없는 경우(개발 초기): 데모 데이터를 반환합니다.
// =============================================================================

import com.racepulse.backend.domain.race.dto.AccuracyStatsDto;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Slf4j
@Service
@RequiredArgsConstructor
public class DashboardService {

    // JdbcTemplate = SQL 쿼리를 직접 실행하는 Spring 도구입니다.
    // JPA ORM보다 네이티브 SQL을 쓸 때 적합합니다.
    private final JdbcTemplate jdbcTemplate;

    /**
     * 전체 예측 정확도 통계를 계산합니다.
     * predictions 테이블에 데이터가 없으면 데모 데이터를 반환합니다.
     */
    public AccuracyStatsDto getAccuracyStats() {
        try {
            // predictions 테이블 존재 여부와 데이터 수 확인
            Integer count = jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM predictions", Integer.class
            );

            if (count == null || count == 0) {
                // 아직 예측 데이터가 없으면 데모 데이터를 반환합니다.
                log.info("[대시보드] predictions 데이터 없음. 데모 데이터 반환.");
                return buildDemoStats();
            }

            return buildRealStats();

        } catch (Exception e) {
            // predictions 테이블이 아직 없으면(ML 서버 미실행) 데모 반환
            log.warn("[대시보드] predictions 테이블 조회 실패: {}. 데모 데이터 반환.", e.getMessage());
            return buildDemoStats();
        }
    }

    /**
     * 실제 predictions 테이블에서 통계를 계산합니다.
     */
    private AccuracyStatsDto buildRealStats() {
        // 전체 예측 건수
        long total = jdbcTemplate.queryForObject(
                "SELECT COUNT(*) FROM predictions p JOIN race_results r ON p.race_entry_id = r.race_entry_id",
                Long.class
        );

        // Top-1 정확도: 예측 1위 = 실제 1위
        double top1 = jdbcTemplate.queryForObject(
                """
                SELECT ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank = 1 THEN 1 ELSE 0 END)
                             / NULLIF(COUNT(*), 0), 1)
                FROM predictions p
                JOIN race_results r ON p.race_entry_id = r.race_entry_id
                WHERE p.predicted_rank = 1
                """,
                Double.class
        );

        // Top-3 정확도: 예측 1위가 실제 3위 이내
        double top3 = jdbcTemplate.queryForObject(
                """
                SELECT ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank <= 3 THEN 1 ELSE 0 END)
                             / NULLIF(COUNT(*), 0), 1)
                FROM predictions p
                JOIN race_results r ON p.race_entry_id = r.race_entry_id
                WHERE p.predicted_rank = 1
                """,
                Double.class
        );

        // 최근 30일 Top-1 정확도
        double last30 = jdbcTemplate.queryForObject(
                """
                SELECT ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank = 1 THEN 1 ELSE 0 END)
                             / NULLIF(COUNT(*), 0), 1)
                FROM predictions p
                JOIN race_results r ON p.race_entry_id = r.race_entry_id
                WHERE p.predicted_at >= NOW() - INTERVAL '30 days'
                  AND p.predicted_rank = 1
                """,
                Double.class
        );

        // 경마장별 정확도 (races 테이블과 JOIN)
        Map<String, AccuracyStatsDto.MeetAccuracy> byMeet = Map.of(
                "SC", queryMeetAccuracy("SC"),
                "BU", queryMeetAccuracy("BU"),
                "JJ", queryMeetAccuracy("JJ")
        );

        // 월별 추이 (최근 6개월)
        List<AccuracyStatsDto.MonthlyTrend> trend = buildMonthlyTrend();

        return AccuracyStatsDto.builder()
                .totalPredictions(total)
                .top1Accuracy(top1)
                .top3Accuracy(top3)
                .last30DaysTop1(last30)
                .byMeetCode(byMeet)
                .monthlyTrend(trend)
                .build();
    }

    private AccuracyStatsDto.MeetAccuracy queryMeetAccuracy(String meetCode) {
        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    """
                    SELECT
                      ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank = 1 THEN 1 ELSE 0 END)
                               / NULLIF(COUNT(*), 0), 1) AS top1,
                      ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank <= 3 THEN 1 ELSE 0 END)
                               / NULLIF(COUNT(*), 0), 1) AS top3
                    FROM predictions p
                    JOIN race_results r ON p.race_entry_id = r.race_entry_id
                    JOIN races        ra ON r.race_id = ra.id
                    WHERE ra.meet_code = ? AND p.predicted_rank = 1
                    """,
                    meetCode
            );
            if (!rows.isEmpty()) {
                var row = rows.get(0);
                double t1 = row.get("top1") != null ? ((Number) row.get("top1")).doubleValue() : 0.0;
                double t3 = row.get("top3") != null ? ((Number) row.get("top3")).doubleValue() : 0.0;
                return AccuracyStatsDto.MeetAccuracy.builder().top1(t1).top3(t3).build();
            }
        } catch (Exception e) {
            log.debug("[대시보드] {} 경마장 통계 조회 실패: {}", meetCode, e.getMessage());
        }
        return AccuracyStatsDto.MeetAccuracy.builder().top1(0).top3(0).build();
    }

    private List<AccuracyStatsDto.MonthlyTrend> buildMonthlyTrend() {
        List<AccuracyStatsDto.MonthlyTrend> trend = new ArrayList<>();
        try {
            List<Map<String, Object>> rows = jdbcTemplate.queryForList(
                    """
                    SELECT
                      TO_CHAR(p.predicted_at, 'YYYY-MM') AS month,
                      ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank = 1 THEN 1 ELSE 0 END)
                                 / NULLIF(COUNT(*), 0), 1) AS top1,
                      ROUND(100.0 * SUM(CASE WHEN p.predicted_rank = 1 AND r.rank <= 3 THEN 1 ELSE 0 END)
                                 / NULLIF(COUNT(*), 0), 1) AS top3
                    FROM predictions p
                    JOIN race_results r ON p.race_entry_id = r.race_entry_id
                    WHERE p.predicted_at >= NOW() - INTERVAL '6 months'
                      AND p.predicted_rank = 1
                    GROUP BY month
                    ORDER BY month
                    """
            );
            for (var row : rows) {
                trend.add(AccuracyStatsDto.MonthlyTrend.builder()
                        .month((String) row.get("month"))
                        .top1(((Number) row.get("top1")).doubleValue())
                        .top3(((Number) row.get("top3")).doubleValue())
                        .build());
            }
        } catch (Exception e) {
            log.debug("[대시보드] 월별 추이 조회 실패: {}", e.getMessage());
        }
        return trend.isEmpty() ? buildDemoTrend() : trend;
    }

    // -------------------------------------------------------------------------
    // 데모 데이터 (predictions 테이블 없거나 비어있을 때 사용)
    // -------------------------------------------------------------------------
    private AccuracyStatsDto buildDemoStats() {
        return AccuracyStatsDto.builder()
                .totalPredictions(1250)
                .top1Accuracy(42.5)
                .top3Accuracy(68.2)
                .last30DaysTop1(44.1)
                .byMeetCode(Map.of(
                        "SC", AccuracyStatsDto.MeetAccuracy.builder().top1(43.0).top3(69.1).build(),
                        "BU", AccuracyStatsDto.MeetAccuracy.builder().top1(41.5).top3(67.3).build(),
                        "JJ", AccuracyStatsDto.MeetAccuracy.builder().top1(40.2).top3(65.8).build()
                ))
                .monthlyTrend(buildDemoTrend())
                .build();
    }

    private List<AccuracyStatsDto.MonthlyTrend> buildDemoTrend() {
        // 최근 6개월 데모 데이터 생성
        List<AccuracyStatsDto.MonthlyTrend> trend = new ArrayList<>();
        LocalDate now = LocalDate.now();
        double[] top1s = {38.2, 40.1, 41.3, 42.0, 43.5, 42.5};
        double[] top3s = {64.5, 66.2, 67.0, 67.8, 68.5, 68.2};
        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("yyyy-MM");

        for (int i = 5; i >= 0; i--) {
            LocalDate month = now.minusMonths(i);
            int idx = 5 - i;
            trend.add(AccuracyStatsDto.MonthlyTrend.builder()
                    .month(month.format(fmt))
                    .top1(top1s[idx])
                    .top3(top3s[idx])
                    .build());
        }
        return trend;
    }
}
