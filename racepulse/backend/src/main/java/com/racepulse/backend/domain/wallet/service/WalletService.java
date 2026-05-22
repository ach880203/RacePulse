package com.racepulse.backend.domain.wallet.service;

import com.racepulse.backend.domain.user.entity.User;
import com.racepulse.backend.domain.user.repository.UserRepository;
import com.racepulse.backend.domain.wallet.dto.SpendResponse;
import com.racepulse.backend.domain.wallet.dto.TransactionHistoryResponse;
import com.racepulse.backend.domain.wallet.dto.WalletContentType;
import com.racepulse.backend.domain.wallet.entity.CurrencyType;
import com.racepulse.backend.domain.wallet.entity.TransactionType;
import com.racepulse.backend.domain.wallet.entity.UserWallet;
import com.racepulse.backend.domain.wallet.entity.WalletTransaction;
import com.racepulse.backend.domain.wallet.repository.UserWalletRepository;
import com.racepulse.backend.domain.wallet.repository.WalletTransactionRepository;
import com.racepulse.backend.global.exception.BusinessException;
import com.racepulse.backend.global.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.util.UUID;

// =============================================================================
// WalletService.java - 편자 지갑의 핵심 비즈니스 로직
// =============================================================================
// Controller는 HTTP 요청/응답만 맡고, 실제 잔액 변경 규칙은 Service에 모아 둡니다.
// 이렇게 하면 출석, 광고, 소비 규칙이 여러 Controller에 흩어지지 않아 유지보수가 쉬워집니다.
// =============================================================================

@Service
@RequiredArgsConstructor
public class WalletService {

    private final UserRepository userRepository;
    private final UserWalletRepository userWalletRepository;
    private final WalletTransactionRepository walletTransactionRepository;
    private final StringRedisTemplate redisTemplate;

    // 한국 서비스 기준으로 "오늘"과 "자정"을 계산하기 위해 서울 시간대를 명확히 사용합니다.
    private static final ZoneId SEOUL_ZONE = ZoneId.of("Asia/Seoul");
    private static final int DAILY_AD_HORSESHOE_LIMIT = 10;
    private static final int DAILY_QUIZ_LIMIT = 3;

    /**
     * 지갑을 조회합니다. 없으면 첫 조회 시 빈 지갑을 자동으로 만듭니다.
     */
    @Transactional
    public UserWallet getWallet(UUID userId) {
        return findWalletOrCreate(userId);
    }

    /**
     * 편자/건초 획득을 처리합니다.
     */
    @Transactional
    public UserWallet earn(UUID userId, TransactionType type, int amount, CurrencyType currency, String description) {
        if (amount <= 0) {
            throw new BusinessException(ErrorCode.INVALID_INPUT);
        }

        UserWallet wallet = findWalletWithLockOrCreate(userId);

        if (currency == CurrencyType.EVENT) {
            wallet.addEventHorseshoe(amount, OffsetDateTime.now(SEOUL_ZONE).plusMonths(6));
            saveTransaction(wallet.getUser(), type, currency, amount, wallet.getEventHorseshoe(), description);
        } else if (currency == CurrencyType.PAID) {
            wallet.addPaidHorseshoe(amount);
            saveTransaction(wallet.getUser(), type, currency, amount, wallet.getPaidHorseshoe(), description);
        } else if (currency == CurrencyType.HAY) {
            wallet.addHay(amount);
            saveTransaction(wallet.getUser(), type, currency, amount, wallet.getHay(), description);
        }

        return wallet;
    }

    /**
     * 출석 보상을 지급합니다. 하루 한 번만 가능하도록 Redis에 오늘 출석 여부를 저장합니다.
     */
    @Transactional
    public UserWallet earnAttendance(UUID userId) {
        String key = dailyKey("wallet:attendance:", userId);
        Boolean firstAttendance = redisTemplate.opsForValue().setIfAbsent(key, "1", secondsUntilMidnight());
        if (!Boolean.TRUE.equals(firstAttendance)) {
            throw new BusinessException(ErrorCode.ATTENDANCE_ALREADY_DONE);
        }

        UserWallet wallet = earn(userId, TransactionType.EARN_ATTENDANCE, 1, CurrencyType.EVENT, "출석 체크 이벤트 편자 지급");
        wallet.addHay(3);
        saveTransaction(wallet.getUser(), TransactionType.EARN_HAY_ATTENDANCE, CurrencyType.HAY, 3, wallet.getHay(), "출석 체크 건초 지급");
        return wallet;
    }

    /**
     * 광고 시청 보상을 지급합니다.
     * Redis를 쓰는 이유는 광고 횟수처럼 자주 바뀌는 카운터를 DB보다 빠르게 처리하고,
     * TTL을 걸어 자정에 자동 초기화할 수 있기 때문입니다.
     */
    @Transactional
    public UserWallet earnAd(UUID userId, int durationSeconds) {
        if (durationSeconds == 15) {
            return earn(userId, TransactionType.EARN_HAY_15S, 2, CurrencyType.HAY, "15초 광고 건초 지급");
        }

        if (durationSeconds == 30) {
            increaseDailyAdEarned(userId, 1);
            return earn(userId, TransactionType.EARN_AD_30S, 1, CurrencyType.EVENT, "30초 광고 이벤트 편자 지급");
        }

        if (durationSeconds == 60) {
            increaseDailyAdEarned(userId, 2);
            return earn(userId, TransactionType.EARN_AD_60S, 2, CurrencyType.EVENT, "60초 광고 이벤트 편자 지급");
        }

        throw new BusinessException(ErrorCode.INVALID_INPUT);
    }

    /**
     * 퀴즈 보상을 지급합니다. 하루 3세트까지만 지급합니다.
     */
    @Transactional
    public UserWallet earnQuiz(UUID userId) {
        String key = dailyKey("wallet:quiz:", userId);
        Long count = redisTemplate.opsForValue().increment(key);
        if (count != null && count == 1) {
            redisTemplate.expire(key, secondsUntilMidnight());
        }
        if (count != null && count > DAILY_QUIZ_LIMIT) {
            redisTemplate.opsForValue().decrement(key);
            throw new BusinessException(ErrorCode.QUIZ_LIMIT_REACHED);
        }

        return earn(userId, TransactionType.EARN_QUIZ, 1, CurrencyType.EVENT, "퀴즈 정답 이벤트 편자 지급");
    }

    /**
     * Phase 4 결제 연동 전까지 구매 API 껍데기만 둡니다.
     */
    @Transactional
    public UserWallet earnPurchasePlaceholder(UUID userId) {
        // TODO: [Phase 4] 포트원 결제 검증 후 구매 편자 수량을 확정해 지급합니다.
        return findWalletOrCreate(userId);
    }

    /**
     * 편자를 소비합니다. 만료가 있는 이벤트 편자를 먼저 써야 사용자가 손해를 보지 않습니다.
     */
    @Transactional
    public SpendResponse spend(UUID userId, WalletContentType contentType, Long raceId) {
        UserWallet wallet = findWalletWithLockOrCreate(userId);
        int cost = contentType.getCost();

        if (wallet.getTotalHorseshoe() < cost) {
            throw new BusinessException(ErrorCode.INSUFFICIENT_HORSESHOE);
        }

        int eventSpend = Math.min(wallet.getEventHorseshoe(), cost);
        int paidSpend = cost - eventSpend;
        String description = buildSpendDescription(contentType, raceId);

        if (eventSpend > 0) {
            wallet.subtractEventHorseshoe(eventSpend);
            saveTransaction(wallet.getUser(), contentType.getTransactionType(), CurrencyType.EVENT,
                    -eventSpend, wallet.getEventHorseshoe(), description);
        }

        if (paidSpend > 0) {
            wallet.subtractPaidHorseshoe(paidSpend);
            saveTransaction(wallet.getUser(), contentType.getTransactionType(), CurrencyType.PAID,
                    -paidSpend, wallet.getPaidHorseshoe(), description);
        }

        return SpendResponse.builder()
                .success(true)
                .contentType(contentType)
                .cost(cost)
                .remainingTotal(wallet.getTotalHorseshoe())
                .remainingEvent(wallet.getEventHorseshoe())
                .remainingPaid(wallet.getPaidHorseshoe())
                .build();
    }

    /**
     * 오늘 광고로 받은 편자 수를 조회합니다.
     */
    @Transactional(readOnly = true)
    public int checkDailyAdLimit(UUID userId) {
        String value = redisTemplate.opsForValue().get(dailyKey("wallet:ad:", userId));
        if (value == null) {
            return 0;
        }
        return Integer.parseInt(value);
    }

    /**
     * 거래 내역을 페이지 단위로 조회합니다.
     */
    @Transactional(readOnly = true)
    public Page<TransactionHistoryResponse> getTransactionHistory(UUID userId, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return walletTransactionRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable)
                .map(TransactionHistoryResponse::from);
    }

    public int getDailyAdHorseshoeLimit() {
        return DAILY_AD_HORSESHOE_LIMIT;
    }

    private UserWallet findWalletOrCreate(UUID userId) {
        return userWalletRepository.findByUserId(userId)
                .orElseGet(() -> createWallet(userId));
    }

    private UserWallet findWalletWithLockOrCreate(UUID userId) {
        return userWalletRepository.findWithLockByUserId(userId)
                .orElseGet(() -> createWallet(userId));
    }

    private UserWallet createWallet(UUID userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new BusinessException(ErrorCode.USER_NOT_FOUND));
        UserWallet wallet = UserWallet.builder()
                .user(user)
                .build();
        return userWalletRepository.save(wallet);
    }

    private void saveTransaction(
            User user,
            TransactionType transactionType,
            CurrencyType currencyType,
            int amount,
            int balanceAfter,
            String description
    ) {
        WalletTransaction transaction = WalletTransaction.builder()
                .user(user)
                .transactionType(transactionType)
                .currencyType(currencyType)
                .amount(amount)
                .balanceAfter(balanceAfter)
                .description(description)
                .build();
        walletTransactionRepository.save(transaction);
    }

    private void increaseDailyAdEarned(UUID userId, int amount) {
        String key = dailyKey("wallet:ad:", userId);
        Long count = redisTemplate.opsForValue().increment(key, amount);
        if (count != null && count == amount) {
            redisTemplate.expire(key, secondsUntilMidnight());
        }
        if (count != null && count > DAILY_AD_HORSESHOE_LIMIT) {
            redisTemplate.opsForValue().decrement(key, amount);
            throw new BusinessException(ErrorCode.AD_LIMIT_REACHED);
        }
    }

    private String dailyKey(String prefix, UUID userId) {
        LocalDate today = LocalDate.now(SEOUL_ZONE);
        return prefix + userId + ":" + today;
    }

    private Duration secondsUntilMidnight() {
        ZonedDateTime now = ZonedDateTime.now(SEOUL_ZONE);
        ZonedDateTime tomorrowMidnight = now.toLocalDate().plusDays(1).atStartOfDay(SEOUL_ZONE);
        return Duration.between(now, tomorrowMidnight);
    }

    private String buildSpendDescription(WalletContentType contentType, Long raceId) {
        if (raceId == null) {
            return contentType.name() + " 콘텐츠 편자 소비";
        }
        return contentType.name() + " 콘텐츠 편자 소비, raceId=" + raceId;
    }
}
