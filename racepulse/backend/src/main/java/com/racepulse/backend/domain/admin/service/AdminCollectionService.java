package com.racepulse.backend.domain.admin.service;

import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.atomic.AtomicBoolean;

// =============================================================================
// AdminCollectionService.java — 관리자 수동 데이터 수집 트리거
// =============================================================================
// Spring Boot는 관리자 권한과 공통 응답을 담당하고, 실제 KRA 수집은 FastAPI ML 서버에 위임합니다.
// =============================================================================

@Slf4j
@Service
@RequiredArgsConstructor
public class AdminCollectionService {

    private final RestTemplate restTemplate;
    private final JdbcTemplate jdbcTemplate;

    @Value("${ml.server.url:http://ml-server:8000}")
    private String mlServerUrl;

    // AtomicBoolean은 동시에 여러 관리자가 눌러도 같은 수집이 중복 실행되지 않도록 막는 스레드 안전 플래그입니다.
    private final AtomicBoolean entriesRunning = new AtomicBoolean(false);
    private final AtomicBoolean resultsRunning = new AtomicBoolean(false);

    public TriggerResponse triggerEntriesCollection() {
        // 출전표 수집은 외부 API 호출량이 크므로 이미 실행 중이면 즉시 409로 막아 중복 비용을 줄입니다.
        return triggerCollection(CollectionType.ENTRIES, entriesRunning, "/collection/entries");
    }

    public TriggerResponse triggerResultsCollection() {
        // 결과 수집도 같은 날짜를 중복 저장할 수 있으므로 실행 중 플래그로 한 번만 시작하게 합니다.
        return triggerCollection(CollectionType.RESULTS, resultsRunning, "/collection/results");
    }

    public CollectionStatusResponse getCollectionStatus() {
        // 화면은 "마지막 상태"가 필요하므로 FastAPI가 남긴 collection_logs의 최신 행을 읽습니다.
        LastCollectionLog entriesLog = findLastLog("entry_info");
        LastCollectionLog resultsLog = findLastLog("race_results");

        return new CollectionStatusResponse(
                entriesLog.collectedAt(),
                resultsLog.collectedAt(),
                entriesRunning.get() ? "RUNNING" : entriesLog.status(),
                resultsRunning.get() ? "RUNNING" : resultsLog.status()
        );
    }

    private TriggerResponse triggerCollection(CollectionType type, AtomicBoolean runningFlag, String path) {
        if (!runningFlag.compareAndSet(false, true)) {
            throw new BusinessException(ErrorCode.ADMIN_COLLECTION_RUNNING);
        }

        LocalDateTime triggeredAt = LocalDateTime.now();

        try {
            CompletableFuture.runAsync(() -> {
                try {
                    // 실제 수집은 오래 걸릴 수 있으므로 HTTP 요청을 백그라운드에서 보내고 관리자 API는 즉시 응답합니다.
                    restTemplate.postForEntity(mlServerUrl + path, null, String.class);
                    log.info("[관리자 수집] {} 수집 요청 완료", type);
                } catch (RestClientException e) {
                    log.error("[관리자 수집] {} 수집 요청 실패: {}", type, e.getMessage(), e);
                } finally {
                    runningFlag.set(false);
                }
            });
        } catch (RuntimeException e) {
            // 백그라운드 작업 등록 자체가 실패하면 수집이 시작되지 않았으므로 503으로 명확히 알립니다.
            runningFlag.set(false);
            throw new BusinessException(ErrorCode.ADMIN_COLLECTION_TRIGGER_FAILED);
        }

        return new TriggerResponse(triggeredAt, type.name());
    }

    private LastCollectionLog findLastLog(String apiName) {
        try {
            return jdbcTemplate.queryForObject(
                    """
                    SELECT collected_at, status::text
                    FROM collection_logs
                    WHERE api_name = ?
                    ORDER BY collected_at DESC
                    LIMIT 1
                    """,
                    (rs, rowNum) -> new LastCollectionLog(
                            rs.getTimestamp("collected_at").toLocalDateTime(),
                            rs.getString("status")
                    ),
                    apiName
            );
        } catch (Exception e) {
            // 수집 로그가 아직 없을 수 있으므로 UNKNOWN으로 내려 화면이 빈 값 대신 안전한 상태를 표시하게 합니다.
            return new LastCollectionLog(null, "UNKNOWN");
        }
    }

    private enum CollectionType {
        ENTRIES,
        RESULTS
    }

    public record TriggerResponse(
            LocalDateTime triggeredAt,
            String type
    ) {
    }

    public record CollectionStatusResponse(
            LocalDateTime lastEntriesCollection,
            LocalDateTime lastResultsCollection,
            String lastEntriesStatus,
            String lastResultsStatus
    ) {
    }

    private record LastCollectionLog(
            LocalDateTime collectedAt,
            String status
    ) {
    }
}
