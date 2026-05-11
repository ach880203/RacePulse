package com.racepulse.backend.domain.user.entity;

/**
 * NotificationType — 푸시 알림 유형을 구분하는 열거형입니다.
 *
 * RACE_START    = 경주 시작 알림 (경주 10분 전에 미리 알립니다)
 * JOCKEY_CHANGE = 기수 변경 알림 (출전표에서 기수가 바뀌면 알립니다)
 * RESULT        = 경주 결과 알림 (경주가 끝나고 순위가 확정되면 알립니다)
 */
public enum NotificationType {
    RACE_START,
    JOCKEY_CHANGE,
    RESULT
}
