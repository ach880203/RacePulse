package com.racepulse.backend.global.config;

// =============================================================================
// VapidKeyGenerator.java — VAPID 키 쌍 최초 1회 생성 유틸리티
// =============================================================================
// 이 클래스는 서버를 처음 설정할 때 딱 한 번만 실행하는 도구입니다.
// 생성된 키 값을 .env 파일에 저장한 뒤 다시는 실행하지 않습니다.
//
// 실행 방법 (IntelliJ 터미널 또는 커맨드라인):
//   프로젝트 루트에서: ./gradlew bootRun 후 아래 API를 한 번 호출하거나,
//   직접 main 메서드를 실행합니다.
//
// 경고: 키를 다시 생성하면 기존에 등록된 모든 구독이 무효화됩니다.
//       한 번 저장한 키는 절대 바꾸지 마세요!
// =============================================================================

import nl.martijndwars.webpush.Utils;
import org.bouncycastle.jce.interfaces.ECPrivateKey;
import org.bouncycastle.jce.interfaces.ECPublicKey;
import org.bouncycastle.jce.provider.BouncyCastleProvider;

import java.security.KeyPair;
import java.security.KeyPairGenerator;
import java.security.Security;
import java.security.spec.ECGenParameterSpec;
import java.util.Base64;

public class VapidKeyGenerator {

    /**
     * VAPID 키 쌍을 생성하고 Base64url 인코딩된 문자열로 출력합니다.
     *
     * 생성된 값을 .env 파일에 아래 형식으로 저장하세요:
     *   VAPID_PUBLIC_KEY=생성된_공개키
     *   VAPID_PRIVATE_KEY=생성된_비밀키
     */
    public static void main(String[] args) throws Exception {
        // BouncyCastle = 타원곡선 암호화(ECDH)를 지원하는 라이브러리입니다.
        Security.addProvider(new BouncyCastleProvider());

        // P-256 타원곡선 위에서 키 쌍을 생성합니다.
        // P-256 = Web Push 표준에서 요구하는 타원곡선 알고리즘입니다.
        KeyPair keyPair = generateKeyPair();

        // Base64url 인코딩 = URL 안에서 안전하게 쓸 수 있는 Base64 형식입니다.
        // 일반 Base64의 +, /를 -, _로 바꾸고 = 패딩을 제거합니다.
        String publicKey = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(Utils.encode((ECPublicKey) keyPair.getPublic()));

        String privateKey = Base64.getUrlEncoder()
                .withoutPadding()
                .encodeToString(Utils.encode((ECPrivateKey) keyPair.getPrivate()));

        System.out.println("=".repeat(60));
        System.out.println("VAPID 키 쌍 생성 완료 — .env 파일에 저장하세요!");
        System.out.println("=".repeat(60));
        System.out.println("VAPID_PUBLIC_KEY=" + publicKey);
        System.out.println("VAPID_PRIVATE_KEY=" + privateKey);
        System.out.println("=".repeat(60));
        System.out.println("⚠️  주의: 이 키를 다시 생성하면 모든 기존 구독이 무효화됩니다.");
    }

    /**
     * 서비스 코드에서도 공개키를 쉽게 가져올 수 있도록 정적 헬퍼를 제공합니다.
     */
    public static KeyPair generateKeyPair() throws Exception {
        if (Security.getProvider(BouncyCastleProvider.PROVIDER_NAME) == null) {
            Security.addProvider(new BouncyCastleProvider());
        }
        KeyPairGenerator keyPairGenerator = KeyPairGenerator.getInstance("EC", BouncyCastleProvider.PROVIDER_NAME);
        keyPairGenerator.initialize(new ECGenParameterSpec("secp256r1"));
        return keyPairGenerator.generateKeyPair();
    }
}
