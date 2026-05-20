package com.racepulse.backend.global.response;

// @AllArgsConstructor = 모든 필드를 받는 생성자를 Lombok이 자동으로 만들어줍니다.
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.AllArgsConstructor;
// @Builder = builder() 문법으로 읽기 쉬운 객체 생성을 돕습니다.
import lombok.Builder;
// @Getter = 각 필드의 getter 메서드를 자동 생성합니다.
import lombok.Getter;

// =============================================================================
// ApiResponse.java — 모든 API가 공통으로 사용하는 응답 껍데기
// =============================================================================
// 왜 필요한가?
// 1) 프론트엔드가 어떤 API를 호출하더라도 같은 응답 모양을 기대할 수 있습니다.
// 2) success, message, data 위치가 항상 같아서 예외 처리와 화면 표시가 쉬워집니다.
// =============================================================================

// @Getter = success/data/message 값을 읽을 수 있는 메서드를 자동 생성합니다.
@Getter
// @Builder = new 대신 builder를 써서 필드 이름을 보며 안전하게 객체를 만들 수 있습니다.
@Builder
// @AllArgsConstructor = builder 내부 동작과 정적 팩토리 메서드에서 사용할 전체 생성자를 만듭니다.
@AllArgsConstructor
public class ApiResponse<T> {

    // API 성공 여부를 담습니다.
    private final boolean success;

    // 실제 응답 본문(목록, 상세 데이터, 페이지 정보 등)을 담습니다.
    private final T data;

    // 사람이 읽을 안내 문구를 담습니다.
    private final String message;

    // 성공 응답을 더 짧고 일관되게 만들기 위한 편의 메서드입니다.
    public static <T> ApiResponse<T> success(T data, String message) {
        return ApiResponse.<T>builder()
                .success(true)
                .data(data)
                .message(message)
                .build();
    }

    public static <T> ApiResponse<T> error(ErrorCode errorCode) {
        return ApiResponse.<T>builder()
                .success(false)
                .data(null)
                .message(errorCode.getMessage())
                .build();
    }
}
