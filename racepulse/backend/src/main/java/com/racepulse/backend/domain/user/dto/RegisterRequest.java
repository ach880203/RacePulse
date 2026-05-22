package com.racepulse.backend.domain.user.dto;

// =============================================================================
// RegisterRequest.java — 이메일 회원가입 요청 DTO
// =============================================================================
// DTO(Data Transfer Object)란? API 요청/응답 데이터를 담는 단순 데이터 클래스입니다.
// Entity(DB 테이블 클래스)와 분리하는 이유:
//   - Entity를 직접 노출하면 DB 구조가 외부에 드러납니다.
//   - 입력 검증(@NotBlank 등)을 DTO에서 처리하면 Entity가 깔끔해집니다.
// =============================================================================

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Getter;

@Getter
public class RegisterRequest {

    // @NotBlank = 비어있거나 공백만 있으면 검증 실패 (400 Bad Request 응답)
    // @Email = 이메일 형식이 아니면 검증 실패
    @NotBlank(message = "이메일은 필수입니다.")
    @Email(message = "올바른 이메일 형식이 아닙니다.")
    private String email;

    // @Size(min, max) = 비밀번호 길이를 8~100자 사이로 제한합니다.
    @NotBlank(message = "비밀번호는 필수입니다.")
    @Size(min = 8, max = 100, message = "비밀번호는 8자 이상이어야 합니다.")
    private String password;

    @NotBlank(message = "닉네임은 필수입니다.")
    @Size(min = 2, max = 50, message = "닉네임은 2~50자 사이여야 합니다.")
    private String nickname;

    // @NotNull은 요청값이 아예 빠진 경우를 Controller 진입 전에 400 응답으로 막아줍니다.
    // 이용약관 동의는 서비스 가입의 필수 조건이므로 DTO에서 먼저 검증하고, Service에서 true 여부를 한 번 더 확인합니다.
    @NotNull(message = "이용약관 동의는 필수입니다.")
    private Boolean termsAgreed;

    // 마케팅 정보 수신 동의는 선택 항목입니다.
    // 개인정보보호법상 필수 동의와 선택 동의를 분리해야 하므로 null이면 동의하지 않은 것으로 처리합니다.
    private Boolean marketingAgreed;
}
