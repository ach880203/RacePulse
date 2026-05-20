package com.racepulse.backend.global.scheduler;

// =============================================================================
// MaintenancePushScheduler.java — 정기 점검 Web Push 자동 발송 스케줄러
// =============================================================================
// @Scheduled(cron = "...")란?
//   Spring이 지정한 시각에 자동으로 메서드를 실행해줍니다.
//   cron 표현식 형식: "초 분 시 일 월 요일"
//   예: "0 0 22 * * MON" = 매주 월요일 22:00:00
//       0(초) 0(분) 22(시) *(매일) *(매월) MON(월요일)
//
// 이 스케줄러가 동작하려면 BackendApplication에 @EnableScheduling이 있어야 합니다.
//
// Web Push 흐름:
//   이 스케줄러 실행 → WebPushService.sendToAll() 호출
//   → push_subscriptions 테이블의 모든 구독자에게 HTTP POST
//   → Google FCM / Mozilla Autopush → 브라우저 알림창 표시
// =============================================================================

import com.racepulse.backend.domain.user.service.WebPushService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

@Slf4j
@Component
@RequiredArgsConstructor
public class MaintenancePushScheduler {

    // WebPushService = 모든 구독자에게 Web Push를 발송하는 서비스입니다.
    // sendToAll()은 push_subscriptions 테이블 전체 구독자에게 동시 발송합니다.
    private final WebPushService webPushService;

    /**
     * 매주 월요일 22:00 KST에 정기 점검 사전 공지 푸시 알림을 발송합니다.
     *
     * cron 표현식 설명:
     *   "0 0 22 * * MON"
     *    초 분 시 일 월  요일
     *    0  0  22 *  *   MON  = 매주 월요일 22:00:00
     *
     * zone = "Asia/Seoul"로 지정해야 한국 시간 기준으로 동작합니다.
     * 생략하면 서버 JVM 기본 시간대(보통 UTC)로 동작해 시각이 달라집니다.
     */
    @Scheduled(cron = "0 0 22 * * MON", zone = "Asia/Seoul")
    public void sendMaintenanceWarningPush() {
        log.info("[점검 알림] 월요일 22:00 — 점검 사전 공지 발송 시작");

        try {
            webPushService.sendToAll(
                    "RacePulse 점검 안내",
                    "내일 새벽 2시~6시 정기 점검이 예정되어 있습니다."
            );
            log.info("[점검 알림] 발송 완료");
        } catch (Exception e) {
            // 발송 실패해도 서비스 전체에 영향을 주면 안 됩니다.
            log.error("[점검 알림] 발송 실패: {}", e.getMessage(), e);
        }
    }
}
