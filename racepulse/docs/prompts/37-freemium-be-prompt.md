# 37. RacePulse 편자 시스템 BE 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, Spring Boot 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (편자 시스템 전체)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: `prompt-29 (V13 마이그레이션)` 완료 필수
- `user_wallets` 테이블 (편자 이원화)
- `wallet_transactions` 테이블 (거래 내역)

---

## 🗂️ 지금까지 한 작업 요약

### 편자 시스템 확정 내용 (14차 회의)

**화폐 2종 + 건초:**
| 화폐 | 색상 | 소비 순서 | 유효기간 |
|------|------|---------|---------|
| 🔩 이벤트 편자 | 은색 | 1순위 | 6개월 |
| 🥇 구매 편자 | 금색 | 2순위 | 무기한 |
| 🌾 건초 | — | 다마고치 전용 | — |

**획득 방법:**
| 방법 | 이벤트 편자 | 건초 |
|------|------|------|
| 출석 체크 | 1개/일 | 3개/일 |
| 30초 광고 시청 | 1개 | — |
| 60초 광고 시청 | 2개 | — |
| 15초 광고 시청 | — | 2개 |
| 하루 광고 상한 | 10개/일 | — |
| 퀴즈 (5문제 중 3개 정답, 30초 제한) | 1개/세트 (하루 3세트) | — |

**콘텐츠 접근 비용 (편자 소비):**
| 콘텐츠 | 광고 직접 시청 | 편자 비용 |
|--------|-------------|---------|
| 말 Stat 개별 항목 | ✅ 15초 | 1편자 |
| 변경사항 상세 | ✅ 15초 | 1편자 |
| Top-3 확률 전체 | ✅ 30초 | 3편자 |
| AI **결과** 해설 | ✅ 30초 | 3편자 |
| AI **사전** 해설 | ❌ 불가 | 25편자 |
| Counterfactual | ❌ 불가 | 18편자 |
| Top-1 확률 | ❌ 불가 | 35편자 |
| 앙상블 전체 | ❌ 불가 | 50편자 |

**인앱 결제 패키지:**
| 패키지 | 편자 | 가격 |
|--------|------|------|
| 스타터 | 50개 | 990원 |
| 위클리 | 150개 | 2,500원 |
| 경기일 | 400개 | 5,900원 |
| 시즌 | 1,000개 | 12,900원 |

**소비 순서**: 이벤트 편자(🔩) 먼저 → 없으면 구매 편자(🥇) 사용

---

## 목표

Spring Boot BE에 편자 지갑 API를 구현합니다.

신규 패키지: `domain/wallet/`
- Entity 2개: `UserWallet`, `WalletTransaction`
- Repository 2개
- Service 1개: `WalletService`
- Controller 1개: `WalletController`

---

## 프로젝트 환경

- **BE**: Spring Boot / Java 21 / JPA / PostgreSQL
- **기존 패키지 참고**:
  - `domain/user/` — User Entity, AuthController 패턴 참고
  - `global/response/ApiResponse.java` — 공통 응답 (반드시 사용)
  - `global/exception/` — BusinessException, ErrorCode (반드시 사용)
  - `global/security/` — JWT 인증 (USER 권한 API에 사용)

---

## 현재 파일 구조 (추가할 위치)

```
backend/src/main/java/com/racepulse/backend/
├── domain/
│   ├── user/                    ← 기존
│   └── wallet/                  ← 신규 패키지
│       ├── entity/
│       │   ├── UserWallet.java
│       │   └── WalletTransaction.java
│       ├── repository/
│       │   ├── UserWalletRepository.java
│       │   └── WalletTransactionRepository.java
│       ├── service/
│       │   └── WalletService.java
│       ├── controller/
│       │   └── WalletController.java
│       └── dto/
│           ├── WalletResponse.java
│           ├── SpendRequest.java
│           ├── EarnRequest.java
│           └── TransactionHistoryResponse.java
```

---

## 구현 사항

### 1. `UserWallet.java` Entity

```java
@Entity @Table(name = "user_wallets")
// users 테이블과 1:1 관계 — 한 유저는 지갑이 하나입니다.
public class UserWallet {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // users 테이블과 1:1 연결
    @OneToOne @JoinColumn(name = "user_id", nullable = false, unique = true)
    private User user;

    // 🔩 이벤트 편자 (은색) — 출석/광고/퀴즈로 획득, 6개월 만료
    @Column(name = "event_horseshoe", nullable = false)
    @Builder.Default
    private int eventHorseshoe = 0;

    // 이벤트 편자 만료 시각
    @Column(name = "event_horseshoe_expires_at")
    private OffsetDateTime eventHorseshoeExpiresAt;

    // 🥇 구매 편자 (금색) — 결제로 획득, 만료 없음
    @Column(name = "paid_horseshoe", nullable = false)
    @Builder.Default
    private int paidHorseshoe = 0;

    // 🌾 건초 — 다마고치 전용, 편자와 교환 불가
    @Column(name = "hay", nullable = false)
    @Builder.Default
    private int hay = 0;

    // 총 보유 편자 수 반환 (이벤트 + 구매)
    public int getTotalHorseshoe() {
        return this.eventHorseshoe + this.paidHorseshoe;
    }
}
```

### 2. `WalletTransaction.java` Entity

```java
@Entity @Table(name = "wallet_transactions")
// 편자/건초 증감 내역을 모두 기록합니다. 한 번 쌓인 기록은 절대 삭제하지 않습니다.
public class WalletTransaction {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne @JoinColumn(name = "user_id", nullable = false)
    private User user;

    // 거래 종류 (Enum)
    // EARN_ATTENDANCE, EARN_AD_30S, EARN_AD_60S, EARN_QUIZ, EARN_PURCHASE,
    // EARN_HAY_15S, EARN_HAY_ATTENDANCE,
    // SPEND_TOP1, SPEND_ENSEMBLE, SPEND_AI_PRE, SPEND_COUNTERFACTUAL,
    // SPEND_TOP3, SPEND_AI_POST, SPEND_STAT, SPEND_CHANGE_DETAIL,
    // ADMIN_GRANT, EXPIRE
    @Enumerated(EnumType.STRING)
    @Column(name = "transaction_type", nullable = false, length = 30)
    private TransactionType transactionType;

    // 화폐 종류: EVENT / PAID / HAY
    @Enumerated(EnumType.STRING)
    @Column(name = "currency_type", nullable = false, length = 10)
    private CurrencyType currencyType;

    // 변화량: 양수 = 획득, 음수 = 소비
    @Column(nullable = false)
    private int amount;

    // 거래 후 해당 화폐 잔액
    @Column(name = "balance_after", nullable = false)
    private int balanceAfter;

    @Column(length = 200)
    private String description;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;
}
```

### 3. `WalletService.java` — 핵심 비즈니스 로직

**메서드 1**: `getWallet(UUID userId) → UserWallet`
- 지갑 조회. 없으면 자동 생성 (첫 조회 시 빈 지갑 자동 초기화)

**메서드 2**: `earn(UUID userId, TransactionType type, int amount, CurrencyType currency)`
```java
// 편자/건초 획득 처리
// 1. 하루 광고 상한 확인 (10편자/일) — type이 광고 관련이면 Redis 카운터 확인
// 2. UserWallet 업데이트
// 3. WalletTransaction INSERT (감사 로그)
// 4. 이벤트 편자 만료일 설정 (획득 시점 + 6개월)
```

**메서드 3**: `spend(UUID userId, TransactionType type, int cost) → boolean`
```java
// 편자 소비 처리 (이벤트 편자 먼저 소비 → 부족하면 구매 편자 사용)
// 1. 총 보유 편자 확인 (이벤트 + 구매 합산)
// 2. 부족하면 BusinessException(INSUFFICIENT_HORSESHOE) 던지기
// 3. 이벤트 편자부터 차감 → 부족분은 구매 편자에서 차감
// 4. WalletTransaction INSERT

// 소비 순서 예시:
//   이벤트 편자 5개 + 구매 편자 20개 → Top-1(35편자) 구매
//   → 이벤트 5개 전부 소비 + 구매 30개 소비 → 구매 편자 잔액 20-30 = -10 → 에러 (부족)
//   → 이벤트 5 + 구매 30 = 35 충분 → 이벤트 5 → 0, 구매 30 → 0  ← 이 경우는 OK
```

**메서드 4**: `checkDailyAdLimit(UUID userId) → int` (오늘 광고 획득 편자 수)
- Redis 키: `wallet:ad:{userId}:{date}` TTL=자정까지
- 10개 도달 시 `BusinessException(AD_LIMIT_REACHED)` 던지기

**메서드 5**: `getTransactionHistory(UUID userId, int page, int size) → Page<WalletTransaction>`

`ErrorCode.java`에 추가:
```java
INSUFFICIENT_HORSESHOE(400, "INSUFFICIENT_HORSESHOE", "편자가 부족합니다."),
AD_LIMIT_REACHED(429, "AD_LIMIT_REACHED", "오늘 광고 획득 한도(10편자)에 도달했습니다."),
```

### 4. `WalletController.java` — API 엔드포인트

모든 API는 JWT 인증 필요 (USER 권한)

```
GET  /api/v1/wallet                    — 내 지갑 조회
POST /api/v1/wallet/earn/attendance    — 출석 체크 (1편자 + 3건초)
POST /api/v1/wallet/earn/ad            — 광고 시청 완료 (duration 파라미터: 15/30/60초)
POST /api/v1/wallet/earn/quiz          — 퀴즈 정답 완료
POST /api/v1/wallet/spend              — 편자 소비 (SpendRequest: contentType)
GET  /api/v1/wallet/transactions       — 거래 내역 조회 (페이지네이션)
```

**`WalletResponse.java`** DTO:
```json
{
  "eventHorseshoe": 5,
  "eventHorseshoeExpiresAt": "2026-11-01T00:00:00+09:00",
  "paidHorseshoe": 20,
  "totalHorseshoe": 25,
  "hay": 15,
  "todayAdEarned": 4,
  "todayAdLimit": 10
}
```

**`SpendRequest.java`** DTO:
```json
{
  "contentType": "TOP_1",
  "raceId": 123
}
```
`contentType` 유효 값: `TOP_1(35)`, `ENSEMBLE(50)`, `AI_PRE(25)`, `COUNTERFACTUAL(18)`, `TOP_3(3)`, `AI_POST(3)`, `STAT(1)`, `CHANGE_DETAIL(1)`

**`SpendResponse.java`** DTO:
```json
{
  "success": true,
  "contentType": "TOP_1",
  "cost": 35,
  "remainingTotal": 140,
  "remainingEvent": 0,
  "remainingPaid": 140
}
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `@OneToOne`이 무엇인지 설명 (유저 1명 = 지갑 1개 → 1대1 관계)
- `@ManyToOne`이 무엇인지 설명 (거래내역 여러개 → 유저 1명)
- 이벤트 편자를 먼저 소비하는 이유 설명 (만료가 있는 것 먼저 써야 손해 없음)
- Redis로 광고 상한을 관리하는 이유 설명 (빠른 카운터 + 자정 자동 리셋)
- `TransactionType` Enum을 쓰는 이유 설명 (String 오타 방지 + 타입 안전성)
- `balanceAfter`를 저장하는 이유 설명 (나중에 시점별 잔액을 재계산 없이 알 수 있음)
- 편자가 "현금 가치 없는 앱 내 화폐"인 이유 설명 (경품 규제 해당 안 됨)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-be-freemium
커밋 메시지: feat: [prompt-37] 편자 시스템 BE — UserWallet + WalletTransaction + 지갑 API 7개
```

---

## 완료 기준

```bash
# 1. BE 컴파일
cd racepulse/backend
.\gradlew compileJava

# 2. 지갑 조회 (인증 토큰 필요)
curl http://localhost:8080/api/v1/wallet \
  -H 'Authorization: Bearer {JWT_TOKEN}'
# → {"success": true, "data": {"totalHorseshoe": 0, ...}}

# 3. 출석 체크
curl -X POST http://localhost:8080/api/v1/wallet/earn/attendance \
  -H 'Authorization: Bearer {JWT_TOKEN}'
# → {"success": true, "data": {"eventHorseshoe": 1, "hay": 3, ...}}

# 4. 출석 중복 시도 → 에러
# (하루 1회 제한 — Redis로 판단)
# → {"success": false, "message": "오늘 이미 출석했습니다."}

# 5. 편자 소비
curl -X POST http://localhost:8080/api/v1/wallet/spend \
  -H 'Authorization: Bearer {JWT_TOKEN}' \
  -H 'Content-Type: application/json' \
  -d '{"contentType": "TOP_3", "raceId": 1}'
# → {"success": false, "message": "편자가 부족합니다."} (처음엔 0개라 부족)

# 6. 거래 내역 조회
curl 'http://localhost:8080/api/v1/wallet/transactions?page=0&size=10' \
  -H 'Authorization: Bearer {JWT_TOKEN}'
# → {"success": true, "data": {"content": [...], "totalElements": 1}}
```

---

## ⚠️ 주의사항

1. 편자 잔액은 절대 음수가 되면 안 됩니다 — DB CHECK 제약 + 서비스 레이어 이중 검증
2. `wallet_transactions`는 삭제 없이 쌓기만 합니다 — DELETE 쿼리 사용 금지
3. 광고 상한 카운터는 Redis TTL로 자정 자동 초기화 — DB에 따로 저장하지 않습니다
4. 인앱 결제(포트원 연동)는 Phase 4에서 구현 — 이번에는 `earn/purchase` API 껍데기만 만들어두고 `TODO: [Phase 4]` 주석 처리
