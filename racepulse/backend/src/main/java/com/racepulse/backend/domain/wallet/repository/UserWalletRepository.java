package com.racepulse.backend.domain.wallet.repository;

import com.racepulse.backend.domain.wallet.entity.UserWallet;
import jakarta.persistence.LockModeType;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;

import java.util.Optional;
import java.util.UUID;

// =============================================================================
// UserWalletRepository.java - user_wallets 테이블을 조회/저장하는 Repository
// =============================================================================
// JpaRepository를 상속하면 save(), findById() 같은 기본 DB 기능을 직접 만들지 않아도 됩니다.
// =============================================================================

public interface UserWalletRepository extends JpaRepository<UserWallet, Long> {

    // user_id는 UNIQUE이므로 유저 1명당 지갑 1개만 조회됩니다.
    Optional<UserWallet> findByUserId(UUID userId);

    // 지갑 잔액을 바꾸는 동안 동시에 다른 요청이 같은 지갑을 수정하지 못하게 DB 잠금을 겁니다.
    // 편자 잔액이 음수가 되는 경쟁 상황을 막기 위한 안전장치입니다.
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    Optional<UserWallet> findWithLockByUserId(UUID userId);
}
