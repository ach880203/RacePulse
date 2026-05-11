package com.racepulse.backend.domain.race.service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.racepulse.backend.domain.race.dto.PredictionItemResponse;
import com.racepulse.backend.domain.race.dto.PredictionResponse;
import com.racepulse.backend.domain.race.dto.SimulationHorseResponse;
import com.racepulse.backend.domain.race.dto.SimulationResponse;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

// =============================================================================
// PredictionService.java — 예측 결과 조회/가공 서비스
// =============================================================================
// 이 서비스는 predictions / race_entries / horses / model_versions 테이블을 조합해서
// 프런트가 바로 그릴 수 있는 "예측 결과 페이지 전용 DTO"를 만들어줍니다.
//
// 예측값이 아직 없으면 ML 서버에 생성 요청을 한 번 보내고 다시 조회합니다.
// 이렇게 해두면 사용자가 페이지를 처음 열었을 때도 준비된 데이터가 있으면 바로 볼 수 있습니다.
// =============================================================================

@Slf4j
@Service
@RequiredArgsConstructor
public class PredictionService {

    private final JdbcTemplate jdbcTemplate;
    private final RestTemplate restTemplate;
    private final ObjectMapper objectMapper;

    @Value("${ml.server.url:http://localhost:8000}")
    private String mlServerUrl;

    public PredictionResponse getPrediction(Long raceId) {
        RacePredictionMeta raceMeta = getRaceMeta(raceId);

        List<PredictionRow> rows = queryPredictionRows(raceId);
        if (rows.isEmpty()) {
            requestPredictionGeneration(raceId);
            rows = queryPredictionRows(raceId);
        }

        if (rows.isEmpty()) {
            throw new IllegalStateException("예측 결과가 아직 준비되지 않았습니다.");
        }

        PredictionRow firstRow = rows.get(0);
        ModelAccuracy modelAccuracy = queryModelAccuracy(firstRow.modelName(), firstRow.modelVersion());

        List<PredictionItemResponse> predictions = rows.stream()
                .map(this::toPredictionItemResponse)
                .toList();

        return PredictionResponse.builder()
                .raceId(raceMeta.raceId())
                .raceName(raceMeta.raceName())
                .modelVersion(buildModelVersionLabel(firstRow.modelName(), firstRow.modelVersion()))
                .top1Accuracy(modelAccuracy.top1Accuracy())
                .top3Accuracy(modelAccuracy.top3Accuracy())
                .predictions(predictions)
                .build();
    }

    public SimulationResponse getSimulation(Long raceId) {
        String url = mlServerUrl + "/ml/simulate/" + raceId + "/result";
        Map<String, Object> response;
        try {
            response = restTemplate.getForObject(url, Map.class);
        } catch (Exception exception) {
            // 저장된 결과가 없으면 ML 서버에 한 번 생성 요청을 보낸 뒤 다시 조회합니다.
            restTemplate.postForObject(mlServerUrl + "/ml/simulate/" + raceId, null, Map.class);
            response = restTemplate.getForObject(url, Map.class);
        }

        if (response == null || response.get("data") == null) {
            throw new IllegalStateException("시뮬레이션 결과를 불러오지 못했습니다.");
        }

        Map<String, Object> data = objectMapper.convertValue(response.get("data"), new TypeReference<>() {
        });
        List<Map<String, Object>> horseRows = objectMapper.convertValue(data.get("horses"), new TypeReference<>() {
        });
        List<SimulationHorseResponse> horses = horseRows.stream()
                .map(row -> SimulationHorseResponse.builder()
                        .horseId(getLongFromMap(row, "horse_id", "horseId"))
                        .horseName(getStringFromMap(row, "horse_name", "horseName"))
                        .rankDistribution(objectMapper.convertValue(
                                row.get("rank_distribution") != null ? row.get("rank_distribution") : row.get("rankDistribution"),
                                new TypeReference<Map<String, Double>>() {
                                }
                        ))
                        .expectedRank(getDoubleFromMap(row, "expected_rank", "expectedRank"))
                        .build())
                .toList();

        return SimulationResponse.builder()
                .raceId(getLongFromMap(data, "race_id", "raceId"))
                .nSimulations(getInteger(data.get("n_simulations")))
                .horses(horses)
                .upsetProbability(getDoubleFromMap(data, "upset_probability", "upsetProbability"))
                .computedAt(getStringFromMap(data, "computed_at", "computedAt"))
                .build();
    }

    private RacePredictionMeta getRaceMeta(Long raceId) {
        List<RacePredictionMeta> rows = jdbcTemplate.query(
                """
                SELECT r.id, r.race_name
                FROM races r
                WHERE r.id = ?
                """,
                (rs, rowNum) -> new RacePredictionMeta(
                        rs.getLong("id"),
                        rs.getString("race_name")
                ),
                raceId
        );

        if (rows.isEmpty()) {
            throw new IllegalArgumentException("해당 경주를 찾을 수 없습니다.");
        }

        return rows.get(0);
    }

    private List<PredictionRow> queryPredictionRows(Long raceId) {
        return jdbcTemplate.query(
                """
                SELECT
                    p.model_name,
                    p.model_version,
                    p.predicted_rank,
                    p.win_prob,
                    p.place_prob,
                    h.id AS horse_id,
                    h.name AS horse_name,
                    e.gate_no,
                    e.rating,
                    e.odds_win,
                    e.rest_days,
                    e.is_debut,
                    e.is_comeback,
                    e.class_change,
                    e.distance_change,
                    e.data_status
                FROM predictions p
                JOIN race_entries e ON e.id = p.race_entry_id
                JOIN horses h ON h.id = e.horse_id
                WHERE p.race_id = ?
                ORDER BY p.predicted_rank ASC, p.win_prob DESC NULLS LAST
                """,
                (rs, rowNum) -> new PredictionRow(
                        rs.getString("model_name"),
                        rs.getString("model_version"),
                        getInteger(rs.getObject("predicted_rank")),
                        getDouble(rs.getObject("win_prob"), true),
                        getDouble(rs.getObject("place_prob"), true),
                        rs.getLong("horse_id"),
                        rs.getString("horse_name"),
                        getInteger(rs.getObject("gate_no")),
                        getBigDecimal(rs.getObject("rating")),
                        getBigDecimal(rs.getObject("odds_win")),
                        getInteger(rs.getObject("rest_days")),
                        rs.getBoolean("is_debut"),
                        rs.getBoolean("is_comeback"),
                        rs.getString("class_change"),
                        rs.getString("distance_change"),
                        rs.getString("data_status")
                ),
                raceId
        );
    }

    private void requestPredictionGeneration(Long raceId) {
        String url = mlServerUrl + "/ml/predict/" + raceId;
        try {
            // POST 본문이 필요 없는 API이므로 null 본문으로 생성만 요청합니다.
            restTemplate.postForObject(url, null, Map.class);
            log.info("[예측] race_id={} 예측 생성 요청 완료.", raceId);
        } catch (Exception exception) {
            // 생성이 실패해도 바로 예외를 끊지 않고, 아래 재조회에서 최종 판단하도록 둡니다.
            log.warn("[예측] race_id={} 예측 생성 요청 실패: {}", raceId, exception.getMessage());
        }
    }

    private ModelAccuracy queryModelAccuracy(String modelName, String modelVersion) {
        try {
            List<String> rows = jdbcTemplate.query(
                    """
                    SELECT metrics::text AS metrics_json
                    FROM model_versions
                    WHERE model_name = ? AND version = ?
                    ORDER BY is_active DESC, created_at DESC
                    LIMIT 1
                    """,
                    (rs, rowNum) -> rs.getString("metrics_json"),
                    modelName,
                    modelVersion
            );

            if (rows.isEmpty()) {
                return new ModelAccuracy(null, null);
            }

            Map<String, Object> metrics = objectMapper.readValue(
                    rows.get(0),
                    new TypeReference<>() {
                    }
            );

            Double top1Accuracy = extractMetric(metrics, "top1_accuracy", "top1Accuracy");
            Double top3Accuracy = extractMetric(metrics, "top3_accuracy", "top3Accuracy");

            return new ModelAccuracy(top1Accuracy, top3Accuracy);
        } catch (Exception exception) {
            log.debug("[예측] 모델 정확도 조회 실패: {}", exception.getMessage());
            return new ModelAccuracy(null, null);
        }
    }

    private PredictionItemResponse toPredictionItemResponse(PredictionRow row) {
        return PredictionItemResponse.builder()
                .horseId(row.horseId())
                .horseName(row.horseName())
                .gateNo(row.gateNo())
                .predictedRank(row.predictedRank())
                .winProbability(row.winProbability())
                .placeProbability(row.placeProbability())
                .conditionGrade(resolveConditionGrade(row.winProbability()))
                .keyFeatures(buildKeyFeatures(row))
                .build();
    }

    private String resolveConditionGrade(Double winProbability) {
        // 승률을 5단계로 잘라두면 프런트가 고정 색상 규칙으로 일관되게 표시할 수 있습니다.
        if (winProbability == null) {
            return "중";
        }
        if (winProbability >= 35.0) {
            return "최상";
        }
        if (winProbability >= 25.0) {
            return "상";
        }
        if (winProbability >= 15.0) {
            return "중";
        }
        if (winProbability >= 8.0) {
            return "하";
        }
        return "최하";
    }

    private List<String> buildKeyFeatures(PredictionRow row) {
        List<String> features = new ArrayList<>();

        if (row.rating() != null) {
            features.add("레이팅 " + formatNumber(row.rating()) + "점");
        }

        if (row.gateNo() != null) {
            if (row.gateNo() <= 3) {
                features.add("안쪽 게이트 " + row.gateNo() + "번");
            } else if (row.gateNo() >= 10) {
                features.add("바깥 게이트 " + row.gateNo() + "번");
            } else {
                features.add("중간 게이트 " + row.gateNo() + "번");
            }
        }

        if (row.oddsWin() != null) {
            features.add("단승 예상 배당 " + formatNumber(row.oddsWin()) + "배");
        }

        if (row.isDebut()) {
            features.add("데뷔전 출전");
        }

        if (row.isComeback()) {
            features.add("휴식 후 복귀전");
        }

        if (row.restDays() != null && row.restDays() > 0) {
            features.add("휴식일 " + row.restDays() + "일");
        }

        if ("UP".equalsIgnoreCase(row.classChange())) {
            features.add("직전 대비 승급전");
        } else if ("DOWN".equalsIgnoreCase(row.classChange())) {
            features.add("직전 대비 강등전");
        }

        if ("UP".equalsIgnoreCase(row.distanceChange())) {
            features.add("거리 연장 적응 필요");
        } else if ("DOWN".equalsIgnoreCase(row.distanceChange())) {
            features.add("거리 단축 변수");
        }

        if (features.size() < 3 && row.winProbability() != null) {
            features.add("우승 확률 " + formatPercent(row.winProbability()));
        }

        if (features.size() < 3 && row.placeProbability() != null) {
            features.add("복승권 확률 " + formatPercent(row.placeProbability()));
        }

        if (features.size() < 3 && row.dataStatus() != null) {
            features.add("데이터 상태 " + translateDataStatus(row.dataStatus()));
        }

        while (features.size() < 3) {
            features.add("모델 종합 점수 반영");
        }

        return features.subList(0, 3);
    }

    private String translateDataStatus(String dataStatus) {
        return switch (dataStatus) {
            case "READY" -> "준비";
            case "UPDATING" -> "갱신 중";
            case "COLLECTED" -> "수집 완료";
            case "JOCKEY_CHANGED" -> "기수 변경";
            default -> dataStatus;
        };
    }

    private String buildModelVersionLabel(String modelName, String modelVersion) {
        if (modelName == null || modelName.isBlank()) {
            return modelVersion;
        }
        if (modelVersion == null || modelVersion.isBlank()) {
            return modelName;
        }
        return modelName + "-" + modelVersion;
    }

    private Double extractMetric(Map<String, Object> metrics, String... keys) {
        for (String key : keys) {
            Object value = metrics.get(key);
            if (value instanceof Number number) {
                return number.doubleValue();
            }
        }
        return null;
    }

    private Long getLongFromMap(Map<String, Object> row, String... keys) {
        for (String key : keys) {
            Object value = row.get(key);
            if (value instanceof Number number) {
                return number.longValue();
            }
        }
        return null;
    }

    private Double getDoubleFromMap(Map<String, Object> row, String... keys) {
        for (String key : keys) {
            Object value = row.get(key);
            if (value instanceof Number number) {
                return number.doubleValue();
            }
        }
        return null;
    }

    private String getStringFromMap(Map<String, Object> row, String... keys) {
        for (String key : keys) {
            Object value = row.get(key);
            if (value != null) {
                return value.toString();
            }
        }
        return null;
    }

    private Integer getInteger(Object value) {
        return value instanceof Number number ? number.intValue() : null;
    }

    private BigDecimal getBigDecimal(Object value) {
        if (value instanceof BigDecimal decimal) {
            return decimal;
        }
        if (value instanceof Number number) {
            return BigDecimal.valueOf(number.doubleValue());
        }
        return null;
    }

    private Double getDouble(Object value, boolean decimalToPercent) {
        if (!(value instanceof Number number)) {
            return null;
        }
        double rawValue = number.doubleValue();
        double convertedValue = decimalToPercent ? rawValue * 100.0 : rawValue;
        return Math.round(convertedValue * 10.0) / 10.0;
    }

    private String formatNumber(BigDecimal value) {
        return value.stripTrailingZeros().toPlainString();
    }

    private String formatPercent(Double value) {
        return String.format(Locale.US, "%.1f%%", value);
    }

    private record RacePredictionMeta(
            Long raceId,
            String raceName
    ) {
    }

    private record ModelAccuracy(
            Double top1Accuracy,
            Double top3Accuracy
    ) {
    }

    private record PredictionRow(
            String modelName,
            String modelVersion,
            Integer predictedRank,
            Double winProbability,
            Double placeProbability,
            Long horseId,
            String horseName,
            Integer gateNo,
            BigDecimal rating,
            BigDecimal oddsWin,
            Integer restDays,
            boolean isDebut,
            boolean isComeback,
            String classChange,
            String distanceChange,
            String dataStatus
    ) {
    }
}
