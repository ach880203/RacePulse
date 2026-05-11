package com.racepulse.backend.domain.race.dto;

import java.util.List;

import com.racepulse.backend.domain.race.entity.Racecourse;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

// =============================================================================
// RacecourseResponse.java — 경마장 목록 API 응답 한 건의 모양
// =============================================================================
// 엔티티를 그대로 노출하지 않고 DTO를 두는 이유:
// DB 컬럼 전체를 노출하지 않고, API 계약에 맞는 필드만 골라서 보내기 위해서입니다.
// =============================================================================

@Getter
@Builder
@AllArgsConstructor
public class RacecourseResponse {

    private final Long id;
    private final String meetCode;
    private final String name;
    private final String location;
    private final List<String> trackTypes;

    // 엔티티를 API 응답용 DTO로 바꾸는 변환 메서드입니다.
    public static RacecourseResponse from(Racecourse racecourse) {
        return RacecourseResponse.builder()
                .id(racecourse.getId())
                .meetCode(racecourse.getMeetCode().name())
                .name(racecourse.getName())
                .location(racecourse.getLocation())
                .trackTypes(racecourse.getTrackTypes())
                .build();
    }
}
