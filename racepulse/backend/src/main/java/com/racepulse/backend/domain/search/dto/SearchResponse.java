package com.racepulse.backend.domain.search.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
@AllArgsConstructor
public class SearchResponse {
    private String query;
    private List<SearchItemResponse> horses;
    private List<SearchItemResponse> jockeys;
    private List<SearchItemResponse> trainers;
    private List<SearchItemResponse> races;
}
