package com.racepulse.backend.domain.user.entity;

/**
 * UserTier — 구독 등급을 구분하는 열거형입니다.
 *
 * FREE = 무료 플랜 (기본값, 기능 일부 제한)
 * PRO  = 유료 플랜 (AI 분석, 상세 통계 등 전체 기능 이용 가능)
 */
public enum UserTier {
    FREE,
    PRO
}
