package com.racepulse.backend.domain.trainer.controller;

import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.racepulse.backend.domain.trainer.dto.TrainerResponse;
import com.racepulse.backend.domain.trainer.service.TrainerService;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.response.PageResponse;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.constraints.Min;
import lombok.RequiredArgsConstructor;

@Tag(name = "Trainers", description = "조교사 조회 API")
@Validated
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/trainers")
public class TrainerController {

    private final TrainerService trainerService;

    @Operation(summary = "조교사 목록 조회", description = "경마장 코드와 이름으로 조교사 목록을 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<PageResponse<TrainerResponse>>> getTrainers(
            @RequestParam(required = false) String meetCode,
            @RequestParam(required = false) String name,
            @RequestParam(defaultValue = "0") @Min(0) int page,
            @RequestParam(defaultValue = "20") @Min(1) int size
    ) {
        PageRequest pageRequest = PageRequest.of(
                page,
                size,
                Sort.by(Sort.Order.asc("name"), Sort.Order.asc("id"))
        );

        PageResponse<TrainerResponse> response = PageResponse.from(
                trainerService.getTrainers(meetCode, name, pageRequest)
        );

        return ResponseEntity.ok(ApiResponse.success(response, "조회 성공"));
    }

    @Operation(summary = "조교사 단건 조회", description = "조교사 ID로 상세 정보를 조회합니다.")
    @GetMapping("/{trainerId}")
    public ResponseEntity<ApiResponse<TrainerResponse>> getTrainerById(
            @PathVariable Long trainerId
    ) {
        return ResponseEntity.ok(ApiResponse.success(trainerService.getTrainerById(trainerId), "조회 성공"));
    }
}
