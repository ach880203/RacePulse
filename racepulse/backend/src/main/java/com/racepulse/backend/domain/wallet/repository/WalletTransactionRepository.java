package com.racepulse.backend.domain.wallet.repository;

import com.racepulse.backend.domain.wallet.entity.WalletTransaction;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.UUID;

// =============================================================================
// WalletTransactionRepository.java - wallet_transactions 테이블 조회/저장 Repository
// =============================================================================
// 거래 내역은 삭제하지 않고 계속 쌓는 감사 로그입니다. 그래서 delete용 메서드는 따로 만들지 않습니다.
// =============================================================================

public interface WalletTransactionRepository extends JpaRepository<WalletTransaction, Long> {

    // 최신 거래가 먼저 보이도록 createdAt 내림차순으로 조회합니다.
    Page<WalletTransaction> findByUserIdOrderByCreatedAtDesc(UUID userId, Pageable pageable);
}
