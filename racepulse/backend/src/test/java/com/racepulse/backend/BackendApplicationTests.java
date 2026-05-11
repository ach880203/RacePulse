package com.racepulse.backend;

import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest(properties = {
		// 테스트 실행 환경에는 .env가 없으므로, 컨텍스트 기동에 필요한 필수 값만 더미로 채웁니다.
		"JWT_SECRET=lPVVwc4XO9Up5YFKz2AUK7uqNzzoKd2U7fwwK93LNd6IdJQZX6AiHQClahNqoyTI",
		"KAKAO_CLIENT_ID=test-kakao-client-id",
		"KAKAO_CLIENT_SECRET=test-kakao-client-secret",
		"VAPID_PUBLIC_KEY=BBwrl6_6mhefxrXiWVrmBu0c0gpirgq8oELIn-jQ52eTyFlwTVgiMg8BtRaedcR8hbZo122yFbBzDXrnFeXfOb0",
		"VAPID_PRIVATE_KEY=GYzBKO--WpjZ3OQy_J2vkMbv_Ktgtt_R7f2v9536pWs"
})
class BackendApplicationTests {

	@Test
	void contextLoads() {
	}

}
