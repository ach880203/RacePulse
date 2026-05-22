package com.racepulse.backend.domain.privacy.dto;

// =============================================================================
// ConsentRequest.java — 로그인 유저의 동의 상태 변경 요청 DTO
// =============================================================================
// termsAgreed는 약관 동의/재동의가 필요할 때 true로 보냅니다.
// marketingAgreed는 선택 동의라서 사용자가 언제든지 켜고 끌 수 있습니다.
// =============================================================================

import lombok.Getter;

@Getter
public class ConsentRequest {

    // Boolean 객체 타입을 쓰면 true/false뿐 아니라 "요청에 값이 없음(null)"도 구분할 수 있습니다.
    // 이 구분이 있어야 마케팅 동의만 바꿀 때 기존 약관 동의 시각을 덮어쓰지 않습니다.
    private Boolean termsAgreed;

    // 마케팅 수신 동의는 선택 항목입니다.
    // 개인정보보호법상 선택 동의를 거부해도 회원가입과 서비스 이용은 막지 않아야 합니다.
    private Boolean marketingAgreed;
}
