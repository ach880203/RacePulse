package com.racepulse.backend.global.response;

// ResponseEntity = HTTP 상태 코드와 본문을 함께 제어할 수 있게 도와주는 스프링 객체입니다.
import org.springframework.http.ResponseEntity;
// @GetMapping = GET 요청을 처리하는 메서드라는 뜻입니다.
import org.springframework.web.bind.annotation.GetMapping;
// @RequestMapping = 클래스 공통 URL 앞부분을 지정합니다.
import org.springframework.web.bind.annotation.RequestMapping;
// @RestController = 이 클래스의 반환값을 JSON으로 바로 내려주는 컨트롤러라는 뜻입니다.
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

// @RestController = "템플릿 화면"이 아니라 "JSON API"를 만드는 컨트롤러라고 스프링에 알려줍니다.
@RestController
// @RequestMapping = 이 클래스 안의 모든 API는 /api/v1 아래에 매핑됩니다.
@RequestMapping("/api/v1")
public class HealthController {

    // 헬스체크 API는 서버가 살아 있는지 가장 빠르게 확인할 때 사용합니다.
    @GetMapping("/health")
    public ResponseEntity<ApiResponse<Map<String, String>>> health() {
        return ResponseEntity.ok(
                ApiResponse.success(
                        Map.of(
                                "status", "UP",
                                "service", "RacePulse Backend"
                        ),
                        "헬스 체크 성공"
                )
        );
    }
}
