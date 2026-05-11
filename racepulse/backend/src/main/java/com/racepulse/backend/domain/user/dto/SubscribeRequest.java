package com.racepulse.backend.domain.user.dto;

// =============================================================================
// SubscribeRequest.java — 푸시 구독 등록 요청 DTO
// =============================================================================
// 브라우저의 ServiceWorker가 Push 서버에서 발급받은 구독 정보를 담습니다.
//
// 프론트엔드에서 보내는 데이터 예시 (JavaScript):
//   const sub = await swRegistration.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: vapidPublicKey });
//   const subJson = sub.toJSON();
//   // { endpoint: "https://...", keys: { p256dh: "...", auth: "..." } }
// =============================================================================

import jakarta.validation.constraints.NotBlank;
import lombok.Getter;

@Getter
public class SubscribeRequest {

    // 브라우저가 Push 서버에서 발급받은 고유 URL
    // 우리가 이 주소로 HTTP POST를 보내면 브라우저에 알림이 도착합니다.
    @NotBlank(message = "endpoint는 필수입니다.")
    private String endpoint;

    // 메시지 암호화에 사용하는 ECDH 공개키 (Base64url 인코딩)
    @NotBlank(message = "p256dhKey는 필수입니다.")
    private String p256dhKey;

    // 메시지 인증에 사용하는 대칭키 (Base64url 인코딩)
    @NotBlank(message = "authKey는 필수입니다.")
    private String authKey;

    // 어느 브라우저인지 (선택값, User-Agent 헤더에서 읽어옵니다)
    private String userAgent;
}
