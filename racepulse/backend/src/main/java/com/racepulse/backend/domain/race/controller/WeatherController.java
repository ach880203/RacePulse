package com.racepulse.backend.domain.race.controller;

// =============================================================================
// WeatherController.java — 날씨 조회 프록시 API
// =============================================================================
// 프론트엔드는 Spring Boot만 호출하고, Spring Boot가 FastAPI 날씨 API를 대신 호출합니다.
// 이렇게 해야 브라우저에 ML 서버 주소를 노출하지 않고 CORS/인증 정책도 한 곳에서 관리할 수 있습니다.
// =============================================================================

import com.racepulse.backend.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/weather")
public class WeatherController {

    // RestTemplate = Spring Boot가 FastAPI로 서버 간 HTTP 요청을 보낼 때 사용하는 클라이언트입니다.
    private final RestTemplate restTemplate;

    // ML 서버 주소는 설정 파일에서 읽어 환경별 주소 차이를 코드 밖에서 관리합니다.
    @Value("${ml.server.url:http://localhost:8000}")
    private String mlServerUrl;

    @GetMapping("/{meetCode}/{targetDate}")
    public ResponseEntity<ApiResponse<Object>> getWeather(
            @PathVariable String meetCode,
            @PathVariable String targetDate
    ) {
        String url = mlServerUrl + "/weather/" + meetCode + "/" + targetDate;

        try {
            Map<?, ?> mlResponse = restTemplate.getForObject(url, Map.class);
            Object weatherData = mlResponse != null ? mlResponse.get("data") : null;
            return ResponseEntity.ok(ApiResponse.success(weatherData, "날씨 조회 성공"));
        } catch (HttpClientErrorException.NotFound e) {
            // 날씨 데이터는 보조 정보라서 없어도 경주 상세 화면은 정상 표시되도록 null로 응답합니다.
            log.info("[날씨] meetCode={}, targetDate={} 데이터 없음", meetCode, targetDate);
            return ResponseEntity.ok(ApiResponse.success(null, "날씨 데이터 없음"));
        } catch (Exception e) {
            // ML 서버 장애가 경주 상세 화면 전체 오류로 번지지 않게 null 응답으로 격리합니다.
            log.error("[날씨] ML 서버 연결 실패. url={}, 오류={}", url, e.getMessage());
            return ResponseEntity.ok(ApiResponse.success(null, "날씨 서비스 준비 중"));
        }
    }
}
