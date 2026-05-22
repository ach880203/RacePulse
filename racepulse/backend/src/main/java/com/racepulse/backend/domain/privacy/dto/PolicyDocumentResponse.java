package com.racepulse.backend.domain.privacy.dto;

// =============================================================================
// PolicyDocumentResponse.java — 약관/개인정보처리방침 조회 응답 DTO
// =============================================================================
// DTO는 API 응답 모양을 고정하기 위한 전용 객체입니다.
// 약관 문서는 DB 대신 코드 상수로 관리하여 Git 변경 이력으로 문구 변경을 추적합니다.
// =============================================================================

import lombok.Builder;
import lombok.Getter;

// @Getter = version, effectiveDate, content 값을 JSON 응답으로 읽을 수 있게 합니다.
@Getter
// @Builder = 필드 이름을 보면서 응답 객체를 만들 수 있어 실수를 줄입니다.
@Builder
public class PolicyDocumentResponse {

    // 약관/처리방침 버전입니다. User.termsVersion과 비교할 때 사용합니다.
    private final String version;

    // 문서가 효력을 시작하는 날짜입니다. 프론트에서 "시행일"로 표시합니다.
    private final String effectiveDate;

    // 실제 약관/개인정보처리방침 본문입니다. 화면에 그대로 표시되므로 반드시 한글 UTF-8로 저장합니다.
    private final String content;
}
