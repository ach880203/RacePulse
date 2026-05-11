package com.racepulse.backend.domain.search.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
@AllArgsConstructor
public class SearchItemResponse {
    private Long id;
    private String name;
    private String subText;
    private String thumbnailUrl;
}
