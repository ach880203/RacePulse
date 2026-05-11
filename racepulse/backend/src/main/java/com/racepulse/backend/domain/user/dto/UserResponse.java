package com.racepulse.backend.domain.user.dto;

// GET /api/v1/auth/me — 내 정보 조회 응답 DTO

import com.racepulse.backend.domain.user.entity.User;
import lombok.Builder;
import lombok.Getter;

import java.util.UUID;

@Getter
@Builder
public class UserResponse {

    private UUID id;
    private String email;
    private String nickname;
    private String role;
    private String tier;
    private String authProvider;

    /**
     * User Entity를 UserResponse DTO로 변환하는 정적 팩토리 메서드입니다.
     * Entity를 직접 노출하지 않고 필요한 필드만 골라서 응답합니다.
     */
    public static UserResponse from(User user) {
        return UserResponse.builder()
                .id(user.getId())
                .email(user.getEmail())
                .nickname(user.getNickname())
                .role(user.getRole().name())
                .tier(user.getTier().name())
                .authProvider(user.getAuthProvider().name())
                .build();
    }
}
