package com.racepulse.backend.global.exception;

import com.racepulse.backend.global.response.ApiResponse;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

// @RestControllerAdvice — 모든 @RestController에서 던진 예외를 이 클래스가 낚아챕니다.
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

    // 위 두 핸들러가 처리하지 못한 모든 예외의 마지막 방어선입니다.
    // 예상치 못한 오류를 500으로 응답하고 스택트레이스가 클라이언트에 노출되지 않습니다.
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResponse<Void>> handleException(Exception e) {
        return ResponseEntity
                .status(500)
                .body(ApiResponse.error(ErrorCode.INTERNAL_SERVER_ERROR));
    }
    
}
