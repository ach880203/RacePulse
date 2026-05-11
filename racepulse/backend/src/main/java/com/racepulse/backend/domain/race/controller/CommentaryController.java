package com.racepulse.backend.domain.race.controller;

// =============================================================================
// CommentaryController.java — AI 해설 조회 API
// =============================================================================
// 이 컨트롤러는 FastAPI ML 서버(포트 8000)에서 생성된 해설을
// 프론트엔드(포트 3000)에 제공하는 "프록시(Proxy)" 역할을 합니다.
//
// 프록시란? "중간에서 대신 요청해주는 역할"입니다.
// 프론트엔드 → Spring Boot → FastAPI 순서로 요청이 흐릅니다.
// 프론트엔드가 FastAPI를 직접 호출하지 않아도 되므로 보안과 CORS 관리가 쉬워집니다.
// =============================================================================

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;

import com.racepulse.backend.global.response.ApiResponse;

import java.util.Map;

@Tag(name = "Commentary", description = "AI 경주 해설 조회 API")
@Slf4j
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/commentary")
public class CommentaryController {

    // RestTemplate = Spring에서 HTTP 요청을 보내는 내장 클라이언트입니다.
    private final RestTemplate restTemplate;

    // ML 서버(FastAPI) 주소 — application.yaml에서 주입합니다.
    @Value("${ml.server.url:http://localhost:8000}")
    private String mlServerUrl;

    @Operation(summary = "경주 사전 해설 조회",
               description = "출전표 확정 후 GPT가 생성한 사전 해설을 조회합니다.")
    @GetMapping("/{raceId}/pre")
    public ResponseEntity<ApiResponse<Object>> getPreRaceCommentary(
            @PathVariable Long raceId
    ) {
        // FastAPI ML 서버에서 해설을 가져옵니다.
        String url = mlServerUrl + "/commentary/" + raceId + "/pre";
        try {
            // RestTemplate.getForObject = GET 요청을 보내고 응답을 자바 객체로 변환합니다.
            Object mlResponse = restTemplate.getForObject(url, Object.class);
            return ResponseEntity.ok(ApiResponse.success(mlResponse, "사전 해설 조회 성공"));
        } catch (HttpClientErrorException.NotFound e) {
            // 해설이 아직 생성되지 않은 경우
            log.info("[해설] race_id={} 사전 해설 미생성. ML 서버에서 404 응답.", raceId);
            return ResponseEntity.ok(
                    ApiResponse.success(
                            Map.of("message", "해설이 아직 생성되지 않았습니다. 금요일 이후 다시 확인해주세요."),
                            "사전 해설 준비 중"
                    )
            );
        } catch (Exception e) {
            log.error("[해설] ML 서버 연결 실패. url={}, 오류={}", url, e.getMessage());
            return ResponseEntity.ok(
                    ApiResponse.success(
                            Map.of("message", "AI 해설 서버에 연결할 수 없습니다."),
                            "서비스 준비 중"
                    )
            );
        }
    }

    @Operation(summary = "경주 결과 해설 조회",
               description = "경주 종료 후 GPT가 생성한 결과 해설을 조회합니다.")
    @GetMapping("/{raceId}/post")
    public ResponseEntity<ApiResponse<Object>> getPostRaceCommentary(
            @PathVariable Long raceId
    ) {
        String url = mlServerUrl + "/commentary/" + raceId + "/post";
        try {
            Object mlResponse = restTemplate.getForObject(url, Object.class);
            return ResponseEntity.ok(ApiResponse.success(mlResponse, "결과 해설 조회 성공"));
        } catch (HttpClientErrorException.NotFound e) {
            return ResponseEntity.ok(
                    ApiResponse.success(
                            Map.of("message", "결과 해설이 아직 생성되지 않았습니다."),
                            "결과 해설 준비 중"
                    )
            );
        } catch (Exception e) {
            log.error("[해설] ML 서버 연결 실패. url={}, 오류={}", url, e.getMessage());
            return ResponseEntity.ok(
                    ApiResponse.success(
                            Map.of("message", "AI 해설 서버에 연결할 수 없습니다."),
                            "서비스 준비 중"
                    )
            );
        }
    }
}
