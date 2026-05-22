package com.racepulse.backend.domain.wallet.entity;

// =============================================================================
// TransactionType.java - 지갑 거래가 왜 발생했는지 기록하는 Enum
// =============================================================================
// 거래 종류를 Enum으로 관리하는 이유:
//   1) "EARN_AD_30S" 같은 문자열 오타를 컴파일 단계에서 막을 수 있습니다.
//   2) DB에는 문자열로 저장하더라도 Java 코드에서는 정해진 값만 다루게 되어 더 안전합니다.
//   3) 나중에 통계 화면에서 거래 종류별로 묶어 볼 때 기준값이 흔들리지 않습니다.
// =============================================================================

public enum TransactionType {
    EARN_ATTENDANCE,
    EARN_AD_30S,
    EARN_AD_60S,
    EARN_QUIZ,
    EARN_PURCHASE,
    EARN_HAY_15S,
    EARN_HAY_ATTENDANCE,
    SPEND_TOP1,
    SPEND_ENSEMBLE,
    SPEND_AI_PRE,
    SPEND_COUNTERFACTUAL,
    SPEND_TOP3,
    SPEND_AI_POST,
    SPEND_STAT,
    SPEND_CHANGE_DETAIL,
    ADMIN_GRANT,
    EXPIRE
}
