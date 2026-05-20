package com.racepulse.backend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

// @EnableScheduling = @Scheduled 어노테이션이 붙은 메서드를 자동으로 실행하는 기능을 켭니다.
// 이것이 없으면 MaintenancePushScheduler의 @Scheduled(cron = "...") 가 동작하지 않습니다.
@EnableScheduling
@SpringBootApplication
public class BackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(BackendApplication.class, args);
	}

}
