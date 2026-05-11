package com.racepulse.backend.domain.user.controller;

// =============================================================================
// PushController.java — Web Push 구독 관리 및 알림 설정 API
// =============================================================================
// 제공 API:
//   POST   /api/v1/push/subscribe             → 구독 등록
//   DELETE /api/v1/push/unsubscribe           → 구독 취소
//   POST   /api/v1/push/test                  → 테스트 알림 전송 (개발용)
//   GET    /api/v1/user/notifications         → 알림 설정 조회
//   PATCH  /api/v1/user/notifications/{type}  → 알림 설정 변경
// =============================================================================

import com.racepulse.backend.domain.user.dto.NotificationSettingResponse;
import com.racepulse.backend.domain.user.dto.SubscribeRequest;
import com.racepulse.backend.domain.user.entity.NotificationSetting;
import com.racepulse.backend.domain.user.entity.NotificationType;
import com.racepulse.backend.domain.user.service.WebPushService;
import com.racepulse.backend.global.response.ApiResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.UUID;

@Tag(name = "Push", description = "Web Push 알림 구독 및 설정 API")
@Slf4j
@RestController
@RequiredArgsConstructor
public class PushController {

    private final WebPushService webPushService;

    // 브라우저가 구독할 때 필요한 VAPID 공개키를 응답으로 내려줍니다.
    @Value("${vapid.public-key}")
    private String vapidPublicKey;

    // =========================================================================
    // Push 구독
    // =========================================================================

    @Operation(summary = "VAPID 공개키 조회",
               description = "브라우저가 구독 등록 전에 VAPID 공개키를 받아가야 합니다.")
    @GetMapping("/api/v1/push/vapid-public-key")
    public ResponseEntity<ApiResponse<Map<String, String>>> getVapidPublicKey() {
        return ResponseEntity.ok(ApiResponse.success(
                Map.of("publicKey", vapidPublicKey),
                "VAPID 공개키 조회 성공"
        ));
    }

    @Operation(summary = "푸시 알림 구독 등록",
               description = "브라우저의 구독 정보(endpoint + 암호화 키)를 서버에 저장합니다.")
    @PostMapping("/api/v1/push/subscribe")
    public ResponseEntity<ApiResponse<Void>> subscribe(
            @Valid @RequestBody SubscribeRequest request,
            @AuthenticationPrincipal UUID userId,
            HttpServletRequest httpRequest
    ) {
        // User-Agent 헤더에서 브라우저 정보를 읽어서 저장합니다.
        // 요청 body에 userAgent 가 없으면 헤더 값을 사용합니다.
        String userAgent = request.getUserAgent() != null
                ? request.getUserAgent()
                : httpRequest.getHeader("User-Agent");

        webPushService.subscribe(userId, request, userAgent);
        return ResponseEntity.ok(ApiResponse.success(null, "구독 등록 성공"));
    }

    @Operation(summary = "푸시 알림 구독 취소",
               description = "특정 endpoint의 구독을 삭제합니다.")
    @DeleteMapping("/api/v1/push/unsubscribe")
    public ResponseEntity<ApiResponse<Void>> unsubscribe(
            @RequestParam String endpoint,
            @AuthenticationPrincipal UUID userId
    ) {
        webPushService.unsubscribe(userId, endpoint);
        return ResponseEntity.ok(ApiResponse.success(null, "구독 취소 성공"));
    }

    // =========================================================================
    // 테스트 알림 전송 (개발용)
    // =========================================================================

    @Operation(summary = "테스트 알림 전송",
               description = "현재 로그인한 유저에게 테스트 알림을 보냅니다. (개발 환경 전용)")
    @PostMapping("/api/v1/push/test")
    public ResponseEntity<ApiResponse<Void>> sendTestNotification(
            @AuthenticationPrincipal UUID userId
    ) {
        webPushService.sendNotification(
                userId,
                "🏇 RacePulse 테스트 알림",
                "Web Push 알림이 정상적으로 작동합니다!"
        );
        log.info("[테스트 알림] userId={}", userId);
        return ResponseEntity.ok(ApiResponse.success(null, "테스트 알림 전송 완료"));
    }

    // =========================================================================
    // 알림 설정 조회/변경
    // =========================================================================

    @Operation(summary = "알림 설정 전체 조회",
               description = "로그인한 유저의 모든 알림 설정(RACE_START/JOCKEY_CHANGE/RESULT)을 조회합니다.")
    @GetMapping("/api/v1/user/notifications")
    public ResponseEntity<ApiResponse<List<NotificationSettingResponse>>> getNotificationSettings(
            @AuthenticationPrincipal UUID userId
    ) {
        List<NotificationSetting> settings = webPushService.getNotificationSettings(userId);
        List<NotificationSettingResponse> response = settings.stream()
                .map(NotificationSettingResponse::from)
                .toList();

        return ResponseEntity.ok(ApiResponse.success(response, "알림 설정 조회 성공"));
    }

    @Operation(summary = "알림 설정 변경",
               description = "특정 알림 유형을 켜거나 끕니다. type: RACE_START / JOCKEY_CHANGE / RESULT")
    @PatchMapping("/api/v1/user/notifications/{type}")
    public ResponseEntity<ApiResponse<NotificationSettingResponse>> updateNotificationSetting(
            @PathVariable String type,
            @RequestParam boolean enabled,
            @AuthenticationPrincipal UUID userId
    ) {
        NotificationType notificationType;
        try {
            // 경로 변수 type 문자열을 NotificationType Enum으로 변환합니다.
            notificationType = NotificationType.valueOf(type.toUpperCase());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(
                    ApiResponse.<NotificationSettingResponse>builder()
                            .success(false)
                            .message("알 수 없는 알림 유형입니다: " + type
                                    + " (허용 값: RACE_START, JOCKEY_CHANGE, RESULT)")
                            .build()
            );
        }

        NotificationSetting updated = webPushService.updateNotificationSetting(userId, notificationType, enabled);
        return ResponseEntity.ok(ApiResponse.success(
                NotificationSettingResponse.from(updated),
                "알림 설정 변경 성공"
        ));
    }
}
