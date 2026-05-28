package com.racepulse.backend.global.exception;

// 프로젝트 전체에서 사용하는 에러 코드를 한 곳에 모아 관리합니다.
// BusinessException을 던질 때 이 enum 값을 인자로 넘기면
// HTTP 상태코드와 메시지가 자동으로 응답에 담깁니다.
public enum ErrorCode {

        // 지갑
        INSUFFICIENT_HORSESHOE(400, "편자가 부족합니다."),
        AD_LIMIT_REACHED(429, "오늘 광고 획득 한도(10편자)에 도달했습니다."),
        ATTENDANCE_ALREADY_DONE(409, "오늘 이미 출석했습니다."),
        QUIZ_LIMIT_REACHED(429, "오늘 퀴즈 보상 한도(3세트)에 도달했습니다."),

        // 공통
        INVALID_INPUT(400, "잘못된 입력입니다."),
        INTERNAL_SERVER_ERROR(500, "서버 내부오류입니다."),

        // 인증 — JWT 검증 및 권한 관련
        UNAUTHORIZED(401, "인증이 필요합니다."),
        FORBIDDEN(403, "권한이 없습니다."),
        TOKEN_EXPIRED(401, "토큰이 만료됐습니다."),
        TOKEN_INVALID(401, "토큰이 유효하지 않습니다."),

        // 유저
        USER_NOT_FOUND(404, "사용자를 찾을 수 없습니다."),
        EMAIL_DUPLICATE(409, "이미 존재하는 이메일입니다."),
        TERMS_NOT_AGREED(400, "이용약관 동의가 필요합니다."),

        // 관리자 수집
        ADMIN_COLLECTION_RUNNING(409, "이미 수집이 실행 중입니다."),
        ADMIN_COLLECTION_TRIGGER_FAILED(503, "수집 시작에 실패했습니다."),

        // 경주
        RACE_NOT_FOUND(404, "경주를 찾을 수 없습니다."),
        HORSE_NOT_FOUND(404, "말을 찾을 수 없습니다."),
        JOCKEY_NOT_FOUND(404, "기수를 찾을 수 없습니다."),
        TRAINER_NOT_FOUND(404, "조교사를 찾을 수 없습니다."),
        RACECOURSE_NOT_FOUND(404, "경마장을 찾을 수 없습니다.");

        private final int status;   // HTTP 상태코드
        private final String message; // 클라이언트에 전달할 메시지

        ErrorCode(int status, String message) {
            this.status = status;
            this.message = message;
        }

        public int getStatus() {
            return status;
        }
        public String getMessage() {
            return message;
        }
    }
    

