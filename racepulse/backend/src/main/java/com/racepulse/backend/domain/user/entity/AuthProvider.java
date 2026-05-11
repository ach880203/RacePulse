package com.racepulse.backend.domain.user.entity;

/**
 * AuthProvider — 회원 가입/로그인 방식을 구분하는 열거형(Enum)입니다.
 *
 * Enum이란? 미리 정해진 상수 값들의 집합입니다.
 * 예: AuthProvider.LOCAL, AuthProvider.KAKAO 두 가지만 허용됩니다.
 *
 * LOCAL = 이메일 + 비밀번호로 직접 가입한 회원
 * KAKAO = 카카오 소셜 로그인으로 가입한 회원
 */
public enum AuthProvider {
    LOCAL,
    KAKAO
}
