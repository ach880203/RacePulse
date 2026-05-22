package com.racepulse.backend.domain.privacy.service;

// =============================================================================
// UserConsentService.java — 로그인 유저의 개인정보/약관 동의 상태 처리
// =============================================================================
// Controller는 HTTP 요청과 응답만 담당하고, 실제 유저 조회와 동의 변경은 Service에서 처리합니다.
// 이렇게 나누면 API가 늘어나도 동의 처리 규칙을 한 곳에서 관리할 수 있습니다.
// =============================================================================

import com.racepulse.backend.domain.privacy.dto.ConsentRequest;
import com.racepulse.backend.domain.privacy.dto.ConsentResponse;
import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.UUID;

@Service
@RequiredArgsConstructor
public class UserConsentService {

    private final UserRepository userRepository;

    @Transactional(readOnly = true)
    public ConsentResponse getConsent(UUID userId) {
        User user = getUser(userId);
        return ConsentResponse.from(user);
    }

    @Transactional
    public ConsentResponse updateConsent(UUID userId, ConsentRequest request) {
        User user = getUser(userId);
        if (request == null) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        // termsAgreed=false는 "필수 약관에 동의하지 않음"이라는 뜻이므로 저장하지 않고 거부합니다.
        if (Boolean.FALSE.equals(request.getTermsAgreed())) {
            throw new BusinessException(ErrorCode.TERMS_NOT_AGREED);
        }

        // 현재 약관 버전에 동의하지 않은 상태라면 마케팅 동의만 저장할 수 없습니다.
        // 필수 약관 동의가 먼저 있어야 선택 동의도 의미가 있기 때문입니다.
        boolean alreadyAgreedCurrentTerms = User.CURRENT_TERMS_VERSION.equals(user.getTermsVersion());
        if (!alreadyAgreedCurrentTerms && !Boolean.TRUE.equals(request.getTermsAgreed())) {
            throw new BusinessException(ErrorCode.TERMS_NOT_AGREED);
        }

        boolean nextMarketingAgreed = request.getMarketingAgreed() == null
                ? user.isMarketingAgreed()
                : request.getMarketingAgreed();

        if (Boolean.TRUE.equals(request.getTermsAgreed())) {
            user.agreeToTerms(nextMarketingAgreed);
        } else {
            user.updateMarketingAgreed(nextMarketingAgreed);
        }

        return ConsentResponse.from(user);
    }

    private User getUser(UUID userId) {
        if (userId == null) {
            throw new BusinessException(ErrorCode.UNAUTHORIZED);
        }
        return userRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
    }
}
