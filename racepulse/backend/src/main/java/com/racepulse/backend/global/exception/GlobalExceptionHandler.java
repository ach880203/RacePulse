package com.racepulse.backend.global.exception;

import com.racepulse.backend.global.response.ApiResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

// @RestControllerAdvice — 모든 @RestController에서 던진 예외를 이 클래스가 낚아챕니다.
// @Slf4j — 로그를 남기기 위한 Lombok 어노테이션입니다. log.error(), log.warn() 등을 쓸 수 있습니다.
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    // throw new BusinessException(ErrorCode.USER_NOT_FOUND) 형태로 던진 예외를 처리합니다.
    @ExceptionHandler(BusinessException.class)
    public ResponseEntity<ApiResponse<Void>> handleBusinessException(BusinessException e) {
        ErrorCode errorCode = e.getErrorCode();
        return ResponseEntity
                .status(errorCode.getStatus())
                .body(ApiResponse.error(errorCode));
    }

    // @Valid 또는 @Validated 검증 실패 시 Spring이 자동으로 던지는 예외를 처리합니다.
    // 첫 번째 필드 에러 메시지만 꺼내 400으로 응답합니다.
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResponse<Void>> handleValidException(MethodArgumentNotValidException e) {
        String errorMessage = e.getBindingResult()
                .getFieldErrors()
                .get(0)
                .getDefaultMessage();
        return ResponseEntity
                .status(400)
                .body(ApiResponse.error(errorMessage));
    }

    // IllegalStateException — "아직 준비되지 않은 데이터"처럼 일시적 상태 문제일 때 503으로 응답합니다.
    // 500(서버 오류)이 아니라 503(서비스 일시 불가)이 더 정확한 의미입니다.
    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<ApiResponse<Void>> handleIllegalState(IllegalStateException e) {
        log.warn("[503] IllegalStateException: {}", e.getMessage());
        return ResponseEntity
                .status(503)
                .body(ApiResponse.error(e.getMessage()));
    }

    // 위 핸들러들이 처리하지 못한 모든 예외의 마지막 방어선입니다.
    // 예상치 못한 오류를 500으로 응답하고, 서버 콘솔에는 스택트레이스를 남겨 원인 파악이 가능합니다.
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleException(Exception e) {
        // log.error — 500 에러가 발생하면 서버 콘솔에 전체 스택트레이스를 출력합니다.
        // 이렇게 해야 "무슨 에러인지" 알 수 있습니다.
        log.error("[500] Unhandled exception: {}", e.getMessage(), e);
        return ResponseEntity
                .status(500)
                .body(ApiResponse.error(ErrorCode.INTERNAL_SERVER_ERROR));
    }
    
}
