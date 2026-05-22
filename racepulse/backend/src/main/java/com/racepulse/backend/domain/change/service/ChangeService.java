package com.racepulse.backend.domain.change.service;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import com.racepulse.backend.domain.change.dto.ChangeEventMessage;
import com.racepulse.backend.domain.change.dto.ChangeResponse;
import com.racepulse.backend.domain.change.entity.EquipmentChange;
import com.racepulse.backend.domain.change.entity.TrainerChange;
import com.racepulse.backend.domain.change.repository.EquipmentChangeRepository;
import com.racepulse.backend.domain.change.repository.TrainerChangeRepository;
import com.racepulse.backend.domain.horse.entity.Horse;
import com.racepulse.backend.domain.race.entity.Race;
import com.racepulse.backend.domain.race.repository.RaceRepository;
import com.racepulse.backend.domain.user.entity.NotificationType;
import com.racepulse.backend.domain.user.service.WebPushService;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

// =============================================================================
// ChangeService.java — 변경 감지 API와 실시간 이벤트 처리 서비스
// =============================================================================
// 역할을 두 갈래로 나눕니다.
// 1) trainer_changes/equipment_changes 테이블을 읽어 API 응답 DTO로 변환합니다.
// 2) Redis로 들어온 변경 이벤트를 받아 관심 사용자에게 Web Push를 보냅니다.
//
// 변경 감지 원천은 ML/배치 쪽에서 계속 늘어날 수 있으므로, 컨트롤러가 아닌 서비스에
// 변환/발송 규칙을 모아 두어 API 표면을 안정적으로 유지합니다.
// =============================================================================

@Slf4j
@Service
@RequiredArgsConstructor
public class ChangeService {

    private static final ZoneId KOREA_ZONE = ZoneId.of("Asia/Seoul");
    private static final String RACE_CHANGE_TARGET_TYPE = "RACE_CHANGE";

    private final TrainerChangeRepository trainerChangeRepository;
    private final EquipmentChangeRepository equipmentChangeRepository;
    private final RaceRepository raceRepository;
    private final JdbcTemplate jdbcTemplate;
    private final WebPushService webPushService;
    private final RestTemplate restTemplate;

    @Value("${ml.server.url:http://localhost:8000}")
    private String mlServerUrl;

    @Transactional(readOnly = true)
    public ChangeResponse.RaceChanges getRaceChanges(Long raceId) {
        if (!raceRepository.existsById(raceId)) {
            throw new BusinessException(ErrorCode.RACE_NOT_FOUND);
        }

        List<ChangeResponse.ChangeItem> changes = new ArrayList<>();
        changes.addAll(trainerChangeRepository.findByRaceIdOrderByDetectedAtDesc(raceId)
                .stream()
                .map(this::toTrainerChangeItem)
                .toList());
        changes.addAll(equipmentChangeRepository.findByRaceIdOrderByDetectedAtDesc(raceId)
                .stream()
                .map(this::toEquipmentChangeItem)
                .toList());

        List<ChangeResponse.ChangeItem> sortedChanges = sortByDetectedAtDesc(changes);
        return new ChangeResponse.RaceChanges(raceId, !sortedChanges.isEmpty(), sortedChanges);
    }

    @Transactional(readOnly = true)
    public ChangeResponse.TodayChanges getTodayChanges() {
        LocalDate today = LocalDate.now(KOREA_ZONE);
        List<ChangeResponse.ChangeItem> changes = new ArrayList<>();
        changes.addAll(trainerChangeRepository.findByChangeDateOrderByDetectedAtDesc(today)
                .stream()
                .map(this::toTrainerChangeItem)
                .toList());
        changes.addAll(equipmentChangeRepository.findByChangeDateOrderByDetectedAtDesc(today)
                .stream()
                .map(this::toEquipmentChangeItem)
                .toList());

        List<ChangeResponse.ChangeItem> sortedChanges = sortByDetectedAtDesc(changes);
        int highImpactCount = (int) sortedChanges.stream()
                .filter(item -> "HIGH".equals(item.impact()) || "VERY_HIGH".equals(item.impact()))
                .count();

        return new ChangeResponse.TodayChanges(today, sortedChanges.size(), highImpactCount, sortedChanges);
    }

    @Transactional
    public ChangeResponse.SubscribeResult subscribeToRaceChanges(UUID userId, Long raceId, boolean subscribe) {
        if (userId == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }
        if (!raceRepository.existsById(raceId)) {
            throw new BusinessException(ErrorCode.RACE_NOT_FOUND);
        }

        if (subscribe) {
            // user_favorites는 이미 "사용자 + 대상" 관계를 저장하는 범용 테이블입니다.
            // 별도 구독 테이블을 추가하지 않고 target_type만 RACE_CHANGE로 구분해 중복 스키마를 피합니다.
            jdbcTemplate.update(
                    """
                    insert into user_favorites (user_id, target_type, target_id)
                    values (?, ?, ?)
                    on conflict (user_id, target_type, target_id) do nothing
                    """,
                    userId,
                    RACE_CHANGE_TARGET_TYPE,
                    raceId
            );
        } else {
            jdbcTemplate.update(
                    """
                    delete from user_favorites
                    where user_id = ?
                      and target_type = ?
                      and target_id = ?
                    """,
                    userId,
                    RACE_CHANGE_TARGET_TYPE,
                    raceId
            );
        }

        return new ChangeResponse.SubscribeResult(subscribe);
    }

    public void processChangeEvent(ChangeEventMessage event) {
        if (event == null || event.getType() == null) {
            log.warn("[변경 감지] 비어 있는 이벤트를 수신했습니다.");
            return;
        }

        Set<UUID> recipientIds = findRecipientUserIds(event.getRaceId(), event.getHorseId());
        if (recipientIds.isEmpty()) {
            log.debug("[변경 감지] 알림 대상 사용자가 없습니다. type={}, raceId={}, horseId={}",
                    event.getType(), event.getRaceId(), event.getHorseId());
            triggerCommentaryRegeneration(event);
            return;
        }

        String title = buildNotificationTitle(event.getType());
        String body = buildNotificationBody(event);
        for (UUID userId : recipientIds) {
            // 현재 알림 설정 enum에는 변경 감지 전용 타입이 없어서 JOCKEY_CHANGE 설정을 재사용합니다.
            // 기수 변경이 가장 민감한 변경 알림 축이므로, 사용자가 관련 알림을 꺼두면 이 발송도 멈춥니다.
            webPushService.sendNotification(
                    userId,
                    title,
                    body,
                    NotificationType.JOCKEY_CHANGE,
                    "CHANGE_EVENT",
                    event.getRaceId()
            );
        }

        triggerCommentaryRegeneration(event);
        log.info("[변경 감지] 이벤트 처리 완료. type={}, recipients={}", event.getType(), recipientIds.size());
    }

    private List<ChangeResponse.ChangeItem> sortByDetectedAtDesc(List<ChangeResponse.ChangeItem> changes) {
        return changes.stream()
                .sorted(Comparator.comparing(
                        ChangeResponse.ChangeItem::detectedAt,
                        Comparator.nullsLast(Comparator.reverseOrder())
                ))
                .toList();
    }

    private ChangeResponse.ChangeItem toTrainerChangeItem(TrainerChange change) {
        Horse horse = change.getHorse();
        Race race = change.getRace();
        return new ChangeResponse.ChangeItem(
                "TRAINER",
                "🟠 조교사",
                "MEDIUM",
                race != null ? race.getId() : null,
                horse.getId(),
                horse.getName(),
                change.getOldTrainer() != null ? change.getOldTrainer().getName() : "이전 조교사 없음",
                change.getNewTrainer().getName(),
                null,
                change.getDetectedAt()
        );
    }

    private ChangeResponse.ChangeItem toEquipmentChangeItem(EquipmentChange change) {
        Horse horse = change.getHorse();
        Race race = change.getRace();
        return new ChangeResponse.ChangeItem(
                "EQUIPMENT",
                "🟡 장비",
                change.isBlinkerFirstTime() ? "HIGH" : "MEDIUM",
                race != null ? race.getId() : null,
                horse.getId(),
                horse.getName(),
                change.getOldValue() != null ? change.getOldValue() : "이전 장비 없음",
                change.getNewValue(),
                change.isBlinkerFirstTime(),
                change.getDetectedAt()
        );
    }

    private Set<UUID> findRecipientUserIds(Long raceId, Long horseId) {
        Set<UUID> recipientIds = new HashSet<>();
        if (raceId != null) {
            recipientIds.addAll(findFavoriteUserIds("RACE", raceId));
            recipientIds.addAll(findFavoriteUserIds(RACE_CHANGE_TARGET_TYPE, raceId));
        }
        if (horseId != null) {
            recipientIds.addAll(findFavoriteUserIds("HORSE", horseId));
        }
        return recipientIds;
    }

    private List<UUID> findFavoriteUserIds(String targetType, Long targetId) {
        return jdbcTemplate.query(
                """
                select distinct user_id
                from user_favorites
                where target_type = ?
                  and target_id = ?
                """,
                (rs, rowNum) -> rs.getObject("user_id", UUID.class),
                targetType,
                targetId
        );
    }

    private String buildNotificationTitle(String type) {
        return switch (type.toUpperCase()) {
            case "JOCKEY" -> "기수 변경 알림";
            case "CANCELLED", "SCRATCH" -> "출전 취소 알림";
            case "TRAINER" -> "조교사 변경 알림";
            case "EQUIPMENT" -> "장비 변경 알림";
            case "TRACK" -> "트랙 상태 변경 알림";
            default -> "경주 변경 알림";
        };
    }

    private String buildNotificationBody(ChangeEventMessage event) {
        String horseName = event.getHorseName() != null ? event.getHorseName() : "관심 출전마";
        String oldValue = event.getOldValue() != null ? event.getOldValue() : "이전 값";
        String newValue = event.getNewValue() != null ? event.getNewValue() : "새 값";

        return switch (event.getType().toUpperCase()) {
            case "JOCKEY" -> horseName + "의 기수가 " + oldValue + "에서 " + newValue + "(으)로 변경되었습니다. 예측 영향이 큽니다.";
            case "CANCELLED", "SCRATCH" -> horseName + "의 출전 상태가 변경되었습니다.";
            case "TRAINER" -> horseName + "의 조교사가 " + oldValue + "에서 " + newValue + "(으)로 변경되었습니다.";
            case "EQUIPMENT" -> horseName + "의 장비가 " + oldValue + "에서 " + newValue + "(으)로 변경되었습니다.";
            case "TRACK" -> "트랙 상태가 " + oldValue + "에서 " + newValue + "(으)로 변경되었습니다.";
            default -> horseName + " 관련 변경 사항이 감지되었습니다.";
        };
    }

    private void triggerCommentaryRegeneration(ChangeEventMessage event) {
        String type = event.getType().toUpperCase();
        if (!"JOCKEY".equals(type) && !"TRAINER".equals(type) && !"EQUIPMENT".equals(type)) {
            return;
        }

        try {
            // 해설 재생성은 부가 작업입니다. 실패해도 API/알림 처리는 성공해야 하므로 로그만 남깁니다.
            // ML 서버의 실제 엔드포인트가 확정되면 이 URL만 맞추면 됩니다.
            String url = mlServerUrl + "/ml/commentary/regenerate";
            restTemplate.postForEntity(url, event, Void.class);
        } catch (Exception e) {
            log.warn("[변경 감지] 해설 재생성 요청 실패. type={}, raceId={}, error={}",
                    event.getType(), event.getRaceId(), e.getMessage());
        }
    }
}
