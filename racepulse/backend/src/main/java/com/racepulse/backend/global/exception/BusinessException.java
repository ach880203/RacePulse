package com.racepulse.backend.global.exception;

// 비즈니스 로직에서 의도적으로 던지는 커스텀 예외입니다.
// throw new BusinessException(ErrorCode.USER_NOT_FOUND) 형태로 사용하며,
// GlobalExceptionHandler가 이를 잡아 ApiResponse 형태로 응답합니다.
public class BusinessException extends RuntimeException {

    private final ErrorCode errorCode;

    public BusinessException(ErrorCode errorCode) {
        // 부모 생성자에 메시지를 넘겨 e.getMessage()로도 꺼낼 수 있게 합니다.
        super(errorCode.getMessage());
        this.errorCode = errorCode;
    }

    public ErrorCode getErrorCode() {
        return errorCode;
    }
}
