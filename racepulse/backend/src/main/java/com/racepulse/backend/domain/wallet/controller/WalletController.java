package com.racepulse.backend.domain.wallet.controller;

import com.racepulse.backend.domain.wallet.dto.SpendRequest;
import com.racepulse.backend.domain.wallet.dto.SpendResponse;
import com.racepulse.backend.domain.wallet.dto.TransactionHistoryResponse;
import com.racepulse.backend.domain.wallet.dto.WalletResponse;
import com.racepulse.backend.domain.wallet.entity.UserWallet;
import com.racepulse.backend.domain.wallet.service.WalletService;
import com.racepulse.backend.global.response.ApiResponse;
import com.racepulse.backend.global.response.PageResponse;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

// =============================================================================
// WalletController.java - 편자 지갑 API 엔드포인트
// =============================================================================
// 모든 API는 SecurityConfig의 anyRequest().authenticated() 규칙에 따라 JWT 인증이 필요합니다.
// @AuthenticationPrincipal로 JWT에서 꺼낸 userId를 받아 "내 지갑"만 다루게 합니다.
// =============================================================================

@Tag(name = "Wallet", description = "편자 지갑 API")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/v1/wallet")
public class WalletController {

    private final WalletService walletService;

    @Operation(summary = "내 지갑 조회", description = "이벤트 편자, 구매 편자, 건초, 오늘 광고 획득량을 조회합니다.")
    @GetMapping
    public ResponseEntity<ApiResponse<WalletResponse>> getWallet(@AuthenticationPrincipal UUID userId) {
        UserWallet wallet = walletService.getWallet(userId);
        WalletResponse response = WalletResponse.from(
                wallet,
                walletService.checkDailyAdLimit(userId),
                walletService.getDailyAdHorseshoeLimit()
        );
        return ResponseEntity.ok(ApiResponse.success(response, "지갑 조회 성공"));
    }

    @Operation(summary = "출석 체크", description = "하루 한 번 이벤트 편자 1개와 건초 3개를 지급합니다.")
    @PostMapping("/earn/attendance")
    public ResponseEntity<ApiResponse<WalletResponse>> earnAttendance(@AuthenticationPrincipal UUID userId) {
        UserWallet wallet = walletService.earnAttendance(userId);
        return ResponseEntity.ok(ApiResponse.success(toWalletResponse(userId, wallet), "출석 보상 지급 성공"));
    }

    @Operation(summary = "광고 시청 완료", description = "15초 광고는 건초 2개, 30/60초 광고는 이벤트 편자를 지급합니다.")
    @PostMapping("/earn/ad")
    public ResponseEntity<ApiResponse<WalletResponse>> earnAd(
            @AuthenticationPrincipal UUID userId,
            @RequestParam int duration
    ) {
        UserWallet wallet = walletService.earnAd(userId, duration);
        return ResponseEntity.ok(ApiResponse.success(toWalletResponse(userId, wallet), "광고 보상 지급 성공"));
    }

    @Operation(summary = "퀴즈 정답 완료", description = "하루 3세트까지 이벤트 편자 1개를 지급합니다.")
    @PostMapping("/earn/quiz")
    public ResponseEntity<ApiResponse<WalletResponse>> earnQuiz(@AuthenticationPrincipal UUID userId) {
        UserWallet wallet = walletService.earnQuiz(userId);
        return ResponseEntity.ok(ApiResponse.success(toWalletResponse(userId, wallet), "퀴즈 보상 지급 성공"));
    }

    @Operation(summary = "구매 편자 지급 준비 API", description = "Phase 4 포트원 결제 연동 전까지 API 형태만 준비합니다.")
    @PostMapping("/earn/purchase")
    public ResponseEntity<ApiResponse<WalletResponse>> earnPurchase(@AuthenticationPrincipal UUID userId) {
        UserWallet wallet = walletService.earnPurchasePlaceholder(userId);
        return ResponseEntity.ok(ApiResponse.success(toWalletResponse(userId, wallet), "구매 편자 지급 준비 완료"));
    }

    @Operation(summary = "편자 소비", description = "콘텐츠 종류에 맞는 편자를 이벤트 편자부터 소비합니다.")
    @PostMapping("/spend")
    public ResponseEntity<ApiResponse<SpendResponse>> spend(
            @AuthenticationPrincipal UUID userId,
            @Valid @RequestBody SpendRequest request
    ) {
        SpendResponse response = walletService.spend(userId, request.getContentType(), request.getRaceId());
        return ResponseEntity.ok(ApiResponse.success(response, "편자 소비 성공"));
    }

    @Operation(summary = "거래 내역 조회", description = "편자와 건초의 획득/소비 내역을 최신순으로 조회합니다.")
    @GetMapping("/transactions")
    public ResponseEntity<ApiResponse<PageResponse<TransactionHistoryResponse>>> getTransactions(
            @AuthenticationPrincipal UUID userId,
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "10") int size
    ) {
        Page<TransactionHistoryResponse> history = walletService.getTransactionHistory(userId, page, size);
        return ResponseEntity.ok(ApiResponse.success(PageResponse.from(history), "거래 내역 조회 성공"));
    }

    private WalletResponse toWalletResponse(UUID userId, UserWallet wallet) {
        return WalletResponse.from(
                wallet,
                walletService.checkDailyAdLimit(userId),
                walletService.getDailyAdHorseshoeLimit()
        );
    }
}
