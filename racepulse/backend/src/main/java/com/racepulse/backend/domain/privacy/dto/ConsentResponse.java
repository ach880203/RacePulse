package com.racepulse.backend.domain.privacy.dto;

// =============================================================================
// ConsentResponse.java — 현재 유저의 약관/마케팅 동의 상태 응답 DTO
// =============================================================================
// needsReConsent는 저장된 약관 버전과 현재 약관 버전이 다를 때 true가 됩니다.
// 프론트는 이 값을 보고 재동의 팝업을 띄울지 결정할 수 있습니다.
// =============================================================================

import com.racepulse.backend.domain.user.entity.User;
import lombok.Builder;
import lombok.Getter;

import java.time.OffsetDateTime;

@Getter
@Builder
public class ConsentResponse {

    // 약관 동의 시각이 있으면 최소 한 번은 약관에 동의한 유저입니다.
    private final boolean termsAgreed;

    // OffsetDateTime은 +09:00 같은 타임존까지 포함하므로 프론트가 날짜를 지역 기준으로 안전하게 표시할 수 있습니다.
    private final OffsetDateTime termsAgreedAt;

    // 유저가 마지막으로 동의한 약관 버전입니다.
    private final String termsVersion;

    // 서버가 현재 사용 중인 최신 약관 버전입니다.
    private final String currentTermsVersion;

    // 약관 버전이 올라가면 기존 동의만으로는 부족할 수 있어 재동의를 유도해야 합니다.
    private final boolean needsReConsent;

    // 마케팅 수신 동의는 선택 항목이라 true/false 상태만 내려줍니다.
    private final boolean marketingAgreed;

    public static ConsentResponse from(User user) {
        boolean termsAgreed = user.getTermsAgreedAt() != null;
        boolean needsReConsent = !User.CURRENT_TERMS_VERSION.equals(user.getTermsVersion());

        return ConsentResponse.builder()
                .termsAgreed(termsAgreed)
                .termsAgreedAt(user.getTermsAgreedAt())
                .termsVersion(user.getTermsVersion())
                .currentTermsVersion(User.CURRENT_TERMS_VERSION)
                .needsReConsent(needsReConsent)
                .marketingAgreed(user.isMarketingAgreed())
                .build();
    }
}
