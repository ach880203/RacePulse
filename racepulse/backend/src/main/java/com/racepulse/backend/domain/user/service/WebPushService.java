package com.racepulse.backend.domain.user.service;

// =============================================================================
// WebPushService.java — Web Push 구독 관리 및 알림 전송 서비스
// =============================================================================
// Web Push 전체 흐름:
//
//  [구독 등록 단계]
//   브라우저 ServiceWorker → Push 서버(Google/Mozilla) → 구독 정보(endpoint+키) 발급
//   → 브라우저가 구독 정보를 우리 서버 POST /push/subscribe 로 전송
//   → 우리 서버가 push_subscriptions 테이블에 저장 ← 여기서 처리
//
//  [알림 전송 단계]
//   이벤트 발생(경주 시작 등)
//   → 우리 서버가 저장된 endpoint+키로 메시지를 암호화
//   → Push 서버(Google FCM/Mozilla Autopush)로 HTTP POST 전송
//   → Push 서버가 브라우저에 알림 전달
//   → 브라우저의 ServiceWorker가 알림창 표시
//
// Service Worker란?
//   브라우저 백그라운드에서 실행되는 JavaScript 파일입니다.
//   페이지가 닫혀 있어도 Push 메시지를 받아서 알림창을 띄울 수 있습니다.
// =============================================================================

import com.fasterxml.jackson.databind.ObjectMapper;
import com.racepulse.backend.domain.user.dto.SubscribeRequest;
import com.racepulse.backend.domain.user.entity.*;
import com.racepulse.backend.domain.user.repository.*;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import nl.martijndwars.webpush.Notification;
import nl.martijndwars.webpush.PushService;
import nl.martijndwars.webpush.Subscription;
import nl.martijndwars.webpush.Subscription.Keys;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class WebPushService {

    private final PushSubscriptionRepository pushSubscriptionRepository;
    private final NotificationSettingRepository notificationSettingRepository;
    private final UserRepository userRepository;

    // PushService = web-push 라이브러리의 HTTP 클라이언트입니다.
    // VapidConfig 에서 Bean으로 등록된 것을 주입받습니다.
    private final PushService pushService;

    // ObjectMapper = Java 객체를 JSON 문자열로 변환하는 도구입니다.
    private final ObjectMapper objectMapper;

    // =========================================================================
    // 구독 관리
    // =========================================================================

    /**
     * 브라우저의 Push 구독 정보를 DB에 저장합니다.
     * 이미 같은 endpoint 가 있으면 중복 등록하지 않습니다.
     *
     * @param userAgent 브라우저 User-Agent (request 에 없으면 HTTP 헤더에서 읽어온 값)
     */
    @Transactional
    public void subscribe(UUID userId, SubscribeRequest request, String userAgent) {
        // 이미 등록된 endpoint 면 중복 저장하지 않습니다.
        if (pushSubscriptionRepository.existsByEndpoint(request.getEndpoint())) {
            log.debug("[Push 구독] 이미 등록된 endpoint. userId={}", userId);
            return;
        }

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("유저를 찾을 수 없습니다."));

        PushSubscription subscription = PushSubscription.builder()
                .user(user)
                .endpoint(request.getEndpoint())
                .p256dhKey(request.getP256dhKey())
                .authKey(request.getAuthKey())
                .userAgent(userAgent)
                .build();

        pushSubscriptionRepository.save(subscription);

        // 신규 구독자에게 기본 알림 설정을 만들어줍니다.
        // 모든 알림 유형을 기본 ON으로 초기화합니다.
        initDefaultNotificationSettings(user);

        log.info("[Push 구독] 등록 완료. userId={}", userId);
    }

    /**
     * 특정 endpoint 의 구독을 취소합니다.
     */
    @Transactional
    public void unsubscribe(UUID userId, String endpoint) {
        pushSubscriptionRepository.deleteByUserIdAndEndpoint(userId, endpoint);
        log.info("[Push 구독] 취소 완료. userId={}", userId);
    }

    /**
     * 신규 구독자의 기본 알림 설정(모든 유형 ON)을 초기화합니다.
     * 이미 설정이 있으면 건너뜁니다.
     */
    private void initDefaultNotificationSettings(User user) {
        for (NotificationType type : NotificationType.values()) {
            boolean alreadyExists = notificationSettingRepository
                    .findByUserIdAndType(user.getId(), type)
                    .isPresent();

            if (!alreadyExists) {
                NotificationSetting setting = NotificationSetting.builder()
                        .user(user)
                        .type(type)
                        .enabled(true)
                        .build();
                notificationSettingRepository.save(setting);
            }
        }
    }

    // =========================================================================
    // 알림 전송
    // =========================================================================

    /**
     * 특정 유저에게 푸시 알림을 전송합니다.
     *
     * 알림 페이로드(payload)는 JSON 형식의 문자열입니다.
     * Service Worker가 이 데이터를 받아서 알림창을 표시합니다.
     *
     * @param userId 알림을 받을 유저 ID
     * @param title  알림창 제목
     * @param body   알림창 본문
     */
    public void sendNotification(UUID userId, String title, String body) {
        sendNotification(userId, title, body, null, null, null);
    }

    /**
     * 상세 데이터와 함께 특정 유저에게 푸시 알림을 전송합니다.
     *
     * @param type   알림 유형 (null 이면 유형 체크 없이 전송)
     * @param dataType 페이로드의 type 필드 (RACE_START 등)
     * @param raceId 관련 경주 ID
     */
    public void sendNotification(UUID userId, String title, String body,
                                  NotificationType type, String dataType, Long raceId) {
        List<PushSubscription> subscriptions = pushSubscriptionRepository.findByUserId(userId);
        if (subscriptions.isEmpty()) {
            log.debug("[Push 알림] 구독 없음. userId={}", userId);
            return;
        }

        // 알림 설정이 OFF 면 전송하지 않습니다.
        if (type != null && !isNotificationEnabled(userId, type)) {
            log.debug("[Push 알림] 알림 OFF 설정. userId={}, type={}", userId, type);
            return;
        }

        String payload = buildPayload(title, body, dataType, raceId);

        for (PushSubscription sub : subscriptions) {
            sendToSubscription(sub, payload);
        }
    }

    /**
     * 모든 구독자에게 푸시 알림을 전송합니다. (관리자용 공지)
     */
    public void sendToAll(String title, String body) {
        List<PushSubscription> all = pushSubscriptionRepository.findAll();
        String payload = buildPayload(title, body, "NOTICE", null);

        for (PushSubscription sub : all) {
            sendToSubscription(sub, payload);
        }

        log.info("[Push 전체 발송] title={}, 대상={}", title, all.size());
    }

    // =========================================================================
    // 도메인 이벤트별 알림 전송
    // =========================================================================

    /**
     * 경주 시작 알림을 전송합니다.
     *
     * @param userId  알림을 받을 유저 ID
     * @param raceId  경주 ID
     * @param raceName 경주 이름 (예: "서울 3경주")
     */
    public void sendRaceStartAlert(UUID userId, Long raceId, String raceName) {
        sendNotification(
                userId,
                "🏇 경주 시작 임박",
                raceName + "이(가) 10분 후 시작합니다.",
                NotificationType.RACE_START,
                "RACE_START",
                raceId
        );
    }

    /**
     * 기수 변경 알림을 전송합니다.
     *
     * @param userId    알림을 받을 유저 ID
     * @param raceId    경주 ID
     * @param horseName 말 이름
     */
    public void sendJockeyChangeAlert(UUID userId, Long raceId, String horseName) {
        sendNotification(
                userId,
                "⚠️ 기수 변경",
                horseName + "의 기수가 변경됐습니다.",
                NotificationType.JOCKEY_CHANGE,
                "JOCKEY_CHANGE",
                raceId
        );
    }

    /**
     * 경주 결과 알림을 전송합니다.
     *
     * @param userId   알림을 받을 유저 ID
     * @param raceId   경주 ID
     * @param raceName 경주 이름
     */
    public void sendResultAlert(UUID userId, Long raceId, String raceName) {
        sendNotification(
                userId,
                "🏁 경주 결과",
                raceName + " 결과가 나왔습니다. 확인해보세요!",
                NotificationType.RESULT,
                "RESULT",
                raceId
        );
    }

    // =========================================================================
    // 알림 설정 관리
    // =========================================================================

    /**
     * 특정 유저의 모든 알림 설정을 조회합니다.
     */
    public List<NotificationSetting> getNotificationSettings(UUID userId) {
        return notificationSettingRepository.findByUserId(userId);
    }

    /**
     * 특정 유저의 특정 알림 유형을 켜거나 끕니다.
     */
    @Transactional
    public NotificationSetting updateNotificationSetting(UUID userId, NotificationType type, boolean enabled) {
        NotificationSetting setting = notificationSettingRepository
                .findByUserIdAndType(userId, type)
                .orElseGet(() -> {
                    // 설정이 없으면 새로 만들어줍니다.
                    User user = userRepository.findById(userId)
                            .orElseThrow(() -> new IllegalArgumentException("유저를 찾을 수 없습니다."));
                    return notificationSettingRepository.save(
                            NotificationSetting.builder()
                                    .user(user)
                                    .type(type)
                                    .enabled(enabled)
                                    .build()
                    );
                });

        setting.updateEnabled(enabled);
        log.info("[알림 설정] userId={}, type={}, enabled={}", userId, type, enabled);
        return setting;
    }

    // =========================================================================
    // 내부 유틸리티
    // =========================================================================

    /**
     * 특정 유저가 특정 알림 유형을 받도록 설정했는지 확인합니다.
     */
    private boolean isNotificationEnabled(UUID userId, NotificationType type) {
        return notificationSettingRepository
                .findByUserIdAndType(userId, type)
                .map(NotificationSetting::isEnabled)
                .orElse(true); // 설정이 없으면 기본값 ON
    }

    /**
     * 실제로 하나의 구독 endpoint 에 Push 메시지를 전송합니다.
     *
     * 전송 실패(브라우저가 구독을 취소한 경우 등)는 로그만 남기고 계속 진행합니다.
     * 한 기기의 실패가 다른 기기 알림 전송을 막으면 안 됩니다.
     */
    private void sendToSubscription(PushSubscription sub, String payload) {
        try {
            // Subscription = web-push 라이브러리가 요구하는 구독 정보 래퍼입니다.
            Subscription subscription = new Subscription(
                    sub.getEndpoint(),
                    new Keys(sub.getP256dhKey(), sub.getAuthKey())
            );

            // Notification = endpoint + payload 를 묶어서 HTTP 요청으로 변환합니다.
            Notification notification = new Notification(subscription, payload);

            // 실제 Push 서버(Google FCM / Mozilla 등)에 HTTP POST 전송
            pushService.send(notification);
            log.debug("[Push 전송 성공] endpoint={}", sub.getEndpoint().substring(0, 30) + "...");

        } catch (Exception e) {
            // 전송 실패 → 로그만 남기고 다음 구독으로 계속
            log.warn("[Push 전송 실패] endpoint={}, 오류={}", sub.getEndpoint(), e.getMessage());
        }
    }

    /**
     * 알림 JSON 페이로드를 생성합니다.
     *
     * 페이로드 형식:
     * {
     *   "title": "🏇 RacePulse",
     *   "body": "알림 내용",
     *   "icon": "/icon-192x192.png",
     *   "badge": "/icon-192x192.png",
     *   "data": { "type": "RACE_START", "raceId": 123, "url": "/races/123" }
     * }
     *
     * Service Worker의 push 이벤트 핸들러가 이 JSON을 파싱해서 알림창을 만듭니다.
     */
    private String buildPayload(String title, String body, String dataType, Long raceId) {
        try {
            Map<String, Object> data = Map.of(
                    "type",  dataType != null ? dataType : "NOTICE",
                    "raceId", raceId != null ? raceId : 0,
                    "url",    raceId != null ? "/races/" + raceId : "/"
            );

            Map<String, Object> payload = Map.of(
                    "title",  title,
                    "body",   body,
                    "icon",   "/icon-192x192.png",
                    "badge",  "/icon-192x192.png",
                    "data",   data
            );

            // ObjectMapper.writeValueAsString = Java Map을 JSON 문자열로 변환합니다.
            return objectMapper.writeValueAsString(payload);
        } catch (Exception e) {
            log.error("[Push 페이로드] JSON 직렬화 실패: {}", e.getMessage());
            return "{\"title\":\"" + title + "\",\"body\":\"" + body + "\"}";
        }
    }
}
