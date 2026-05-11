package com.racepulse.backend.domain.user.dto;

// 이메일 로그인 요청 DTO

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import lombok.Getter;

@Getter
public class LoginRequest {

    @NotBlank(message = "이메일은 필수입니다.")
    @Email(message = "올바른 이메일 형식이 아닙니다.")
    private String email;

    @NotBlank(message = "비밀번호는 필수입니다.")
    private String password;

    // 로그인 유지 여부 (true = Refresh Token 유효기간 3일, false = 24시간)
    private boolean rememberMe = false;
}
