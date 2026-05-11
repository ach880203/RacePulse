package com.racepulse.backend.domain.user.entity;

/**
 * UserRole — 회원 권한을 구분하는 열거형입니다.
 *
 * USER  = 일반 회원 (기본값)
 * ADMIN = 관리자 (시스템 관리 기능 접근 가능)
 *
 * Spring Security에서 권한을 확인할 때 "ROLE_USER", "ROLE_ADMIN" 형태로 씁니다.
 * getAuthority() 메서드가 그 변환을 담당합니다.
 */
public enum UserRole {
    USER,
    ADMIN;

    /**
     * Spring Security가 권한을 비교할 때 사용하는 문자열입니다.
     * 예: "ROLE_USER", "ROLE_ADMIN"
     */
    public String getAuthority() {
        return "ROLE_" + this.name();
    }
}
