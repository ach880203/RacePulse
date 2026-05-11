package com.racepulse.backend.domain.race.entity;

// 경주로 상태를 enum으로 제한해 잘못된 문자열 저장을 막습니다.
public enum TrackCondition {
    DRY,
    WET,
    HUMID,
    SATURATED
}
