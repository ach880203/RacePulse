package com.racepulse.backend.domain.search.controller;

import com.racepulse.backend.domain.search.dto.SearchResponse;
import com.racepulse.backend.domain.search.service.SearchService;
import com.racepulse.backend.global.response.ApiResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/search")
public class SearchController {

    private final SearchService searchService;

    @GetMapping
    public ResponseEntity<ApiResponse<SearchResponse>> search(
            @RequestParam String q,
            @RequestParam(defaultValue = "ALL") String type
    ) {
        return ResponseEntity.ok(ApiResponse.success(searchService.search(q, type), "검색 성공"));
    }
}
