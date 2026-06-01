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

    // 프론트 첫 화면에서 인증 없이 백엔드 연결 상태를 확인할 수 있도록 공개 홈 API를 제공합니다.
    // health와 같은 단순 응답이지만, /home 경로를 별도로 두면 화면 코드가 서버 상태를 빠르게 판별할 수 있습니다.
    @GetMapping("/home")
    public ResponseEntity<ApiResponse<Map<String, String>>> home() {
        return ResponseEntity.ok(
                ApiResponse.success(
                        Map.of(
                                "service", "RacePulse Backend",
                                "message", "홈 조회 성공"
                        ),
                        "홈 조회 성공"
                )
        );
    }
}
