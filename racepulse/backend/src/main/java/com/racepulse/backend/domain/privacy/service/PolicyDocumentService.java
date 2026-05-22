package com.racepulse.backend.domain.privacy.service;

// =============================================================================
// PolicyDocumentService.java — 약관/개인정보처리방침 문서 제공 서비스
// =============================================================================
// 지금 단계에서는 문서를 코드 상수로 둡니다.
// 이렇게 하면 문구 변경이 Git diff에 남아 "언제 어떤 약관으로 바뀌었는지" 추적하기 쉽습니다.
// =============================================================================

import com.racepulse.backend.domain.privacy.dto.PolicyDocumentResponse;
import com.racepulse.backend.domain.user.entity.User;
import org.springframework.stereotype.Service;

@Service
public class PolicyDocumentService {

    // 시행일은 프론트에서 "2026-06-01 시행"처럼 표시할 때 사용합니다.
    private static final String EFFECTIVE_DATE = "2026-06-01";

    // 이용약관 본문입니다.
    // TODO: [Phase 4] 실제 서비스 배포 전 법률 검토를 거친 전문으로 교체합니다.
    private static final String TERMS_CONTENT = """
            제1조 (목적)
            RacePulse(이하 "서비스")는 경마 데이터를 기반으로 통계 분석, 예측 정보, 해설 정보를 제공하는 순수 분석 서비스입니다.
            이 서비스는 베팅, 도박, 사행 행위와 무관하며 이를 권장하지 않습니다.

            제2조 (서비스 이용)
            이용자는 서비스가 제공하는 정보를 학습과 참고 목적으로만 이용해야 합니다.
            서비스의 예측 결과와 해설은 데이터 기반 분석이며 실제 경주 결과를 보장하지 않습니다.

            제3조 (계정 관리)
            이용자는 본인의 계정 정보를 안전하게 관리해야 하며, 타인에게 계정을 양도하거나 공유해서는 안 됩니다.

            제4조 (금지 행위)
            서비스 데이터를 무단 수집하거나, 사행 행위를 조장하거나, 다른 이용자의 이용을 방해하는 행위를 금지합니다.

            제5조 (약관 변경)
            서비스는 필요한 경우 약관을 변경할 수 있으며, 중요한 변경이 있을 때는 재동의를 요청할 수 있습니다.
            """;

    // 개인정보처리방침 본문입니다.
    // TODO: [Phase 4] 실제 운영 전 개인정보 처리 위탁, 국외 이전, 보관 기간 등 법률 검토 항목을 보강합니다.
    private static final String PRIVACY_CONTENT = """
            제1조 (수집하는 개인정보)
            서비스는 회원가입과 이용 과정에서 이메일 주소, 닉네임, 인증 제공자 정보, 서비스 이용 기록을 수집할 수 있습니다.

            제2조 (개인정보 이용 목적)
            수집한 개인정보는 회원 식별, 로그인 유지, 서비스 제공, 고객 문의 대응, 공지사항 발송에 사용합니다.
            마케팅 정보는 이용자가 선택 동의한 경우에만 발송합니다.

            제3조 (보유 및 이용 기간)
            개인정보는 회원 탈퇴 시 지체 없이 삭제합니다.
            다만 관계 법령에 따라 보관이 필요한 정보는 해당 법령에서 정한 기간 동안 보관할 수 있습니다.

            제4조 (선택 동의 거부 권리)
            이용자는 마케팅 정보 수신 동의를 거부하거나 언제든지 철회할 수 있습니다.
            선택 동의를 거부해도 기본 서비스 이용에는 제한이 없습니다.

            제5조 (개인정보 보호)
            서비스는 개인정보가 분실, 도난, 유출, 변조되지 않도록 접근 권한 관리와 암호화 등 필요한 보호 조치를 적용합니다.
            """;

    public PolicyDocumentResponse getTerms() {
        return PolicyDocumentResponse.builder()
                .version(User.CURRENT_TERMS_VERSION)
                .effectiveDate(EFFECTIVE_DATE)
                .content(TERMS_CONTENT)
                .build();
    }

    public PolicyDocumentResponse getPrivacy() {
        return PolicyDocumentResponse.builder()
                .version(User.CURRENT_TERMS_VERSION)
                .effectiveDate(EFFECTIVE_DATE)
                .content(PRIVACY_CONTENT)
                .build();
    }
}
