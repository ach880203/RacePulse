package com.racepulse.backend.global.config;

// =============================================================================
// VapidConfig.java — VAPID 설정 및 PushService Bean 등록
// =============================================================================
// VAPID(Voluntary Application Server Identification)란?
//   Web Push 메시지를 보낼 때 "우리가 신뢰할 수 있는 서버"임을 증명하는 키 쌍입니다.
//   공개키(public key) = 브라우저에 전달하는 열린 키
//   비밀키(private key) = 서버에만 보관하는 잠금 키
//
// 비유: 택배 회사의 인감도장 같은 것입니다.
//   인감도장(비밀키)을 가진 서버만 푸시 메시지를 보낼 수 있습니다.
//   받는 브라우저는 공개키로 "이 도장이 진짜인지" 확인합니다.
//
// BouncyCastle이란?
//   Java에서 타원곡선 암호(ECDH)를 지원하는 암호화 라이브러리입니다.
//   web-push 라이브러리가 내부에서 ECDH를 사용하므로 반드시 등록해야 합니다.
// =============================================================================

import lombok.extern.slf4j.Slf4j;
import nl.martijndwars.webpush.PushService;
import org.bouncycastle.jce.provider.BouncyCastleProvider;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.security.Security;

@Slf4j
@Configuration
public class VapidConfig {

    // application.yaml 의 vapid 설정 값을 주입받습니다.
    @Value("${vapid.public-key}")
    private String publicKey;

    @Value("${vapid.private-key}")
    private String privateKey;

    // subject = 알림을 보내는 주체를 식별하는 이메일 또는 URL
    @Value("${vapid.subject}")
    private String subject;

    /**
     * PushService Bean 등록.
     * PushService = web-push 라이브러리의 핵심 클래스로,
     * 실제로 Push 서버(Google FCM, Mozilla 등)에 HTTP 요청을 보내는 역할을 합니다.
     */
    @Bean
    public PushService pushService() throws Exception {
        // BouncyCastle 암호화 제공자를 JVM에 등록합니다.
        // ECDH(타원곡선 디피-헬만) 키 교환에 필요하며, 이미 등록됐으면 건너뜁니다.
        if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
            Security.addProvider(new BouncyCastleProvider());
            log.info("[VAPID] BouncyCastle 암호화 제공자 등록 완료.");
        }

        // PushService 생성: VAPID 공개키, 비밀키, subject 를 넘겨줍니다.
        // 이 객체 하나로 모든 Push 알림 전송을 처리합니다.
        PushService service = new PushService(publicKey, privateKey, subject);
        log.info("[VAPID] PushService 초기화 완료.");
        return service;
    }
}
