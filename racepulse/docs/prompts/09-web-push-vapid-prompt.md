# 09. RacePulse Web Push 알림 + VAPID 설정 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
Spring Boot 백엔드에 Web Push 알림 기능을 구현합니다.
유저가 경주 시작 / 기수변경 / 결과 알림을 받을 수 있게 합니다.
브라우저를 닫아도 알림이 옵니다.

---

## Web Push란?
스마트폰 앱 알림처럼 브라우저에 알림을 보내는 기술입니다.
PWA와 함께 사용하면 앱과 동일한 알림 경험을 제공합니다.

---

## 프로젝트 환경
- Java 21
- Spring Boot 3.5.14
- PostgreSQL 16
- 패키지 루트: `com.racepulse.backend`

---

## 현재 파일 구조
```
src/main/java/com/racepulse/backend/
├── domain/
│   └── user/
│       ├── entity/User.java          ← 07번으로 생성됨
│       └── repository/UserRepository.java
└── global/
    └── response/ApiResponse.java
```

---

## DB 테이블 (이미 생성됨)

### push_subscriptions 테이블
```sql
id, user_id(FK → users.id),
endpoint(TEXT),    ← 브라우저 고유 푸시 주소
p256dh_key,        ← 암호화 키
auth_key,          ← 인증 키
user_agent,        ← 어떤 브라우저인지
created_at
```

### notification_settings 테이블
```sql
id, user_id(FK),
type(ENUM: RACE_START/JOCKEY_CHANGE/RESULT),
is_enabled(BOOL),
created_at, updated_at
```

---

## 구현할 API 엔드포인트
```
POST /api/v1/push/subscribe          ← 푸시 알림 구독 등록
DELETE /api/v1/push/unsubscribe      ← 구독 취소
POST /api/v1/push/test               ← 테스트 알림 전송 (개발용)
GET  /api/v1/user/notifications      ← 알림 설정 조회
PATCH /api/v1/user/notifications/{type} ← 알림 설정 변경
```

---

## 구현 파일 목록

### 1. VAPID 키 생성
VAPID(Voluntary Application Server Identification) = 푸시 서버 신원 확인용 키 쌍

```
build.gradle에 의존성 추가:
implementation 'nl.martijndwars:web-push:5.1.1'
implementation 'org.bouncycastle:bcprov-jdk15on:1.70'
```

application-dev.yaml에 추가:
```yaml
vapid:
  public-key: ${VAPID_PUBLIC_KEY}
  private-key: ${VAPID_PRIVATE_KEY}
  subject: mailto:admin@racepulse.com
```

### 2. PushSubscription Entity
`domain/user/entity/PushSubscription.java`
- push_subscriptions 테이블 매핑

### 3. PushSubscription Repository
`domain/user/repository/PushSubscriptionRepository.java`
- `findByUserId()`, `deleteByUserIdAndEndpoint()` 메서드

### 4. Web Push 서비스
`domain/user/service/WebPushService.java`

구현 메서드:
- `subscribe(userId, subscriptionRequest)` → 구독 정보 저장
- `unsubscribe(userId)` → 구독 취소
- `sendNotification(userId, title, body)` → 특정 유저에게 알림 전송
- `sendToAll(title, body)` → 전체 유저에게 알림 전송 (관리자용)
- `sendRaceStartAlert(raceId)` → 경주 시작 알림
- `sendJockeyChangeAlert(raceId, horseId)` → 기수변경 알림
- `sendResultAlert(raceId)` → 경주 결과 알림

### 5. NotificationSetting Entity
`domain/user/entity/NotificationSetting.java`
- notification_settings 테이블 매핑

### 6. Push Controller
`domain/user/controller/PushController.java`
- 위 5개 엔드포인트 구현

### 7. VAPID 키 생성 유틸리티
`global/config/VapidKeyGenerator.java`
- 최초 1회 VAPID 키 쌍 생성 후 .env에 저장하는 유틸

---

## 알림 페이로드 형식
```json
{
  "title": "🏇 RacePulse",
  "body": "서울 3경주가 10분 후 시작합니다",
  "icon": "/icon-192x192.png",
  "badge": "/icon-192x192.png",
  "data": {
    "type": "RACE_START",
    "raceId": 123,
    "url": "/races/123"
  }
}
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Web Push 동작 원리 설명 (브라우저 → 푸시 서버 → 우리 서버)
- VAPID 키가 무엇이고 왜 필요한지 설명
- endpoint, p256dh_key, auth_key가 각각 무엇인지 설명
- Service Worker가 알림을 받는 과정 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- IntelliJ: File → File Properties → File Encoding → UTF-8
- 한글 알림 메시지가 깨지지 않도록 확인

---

## 완료 기준
1. VAPID 공개키/비밀키 생성 후 .env에 저장
2. `POST http://localhost:8080/api/v1/push/subscribe` 구독 등록 성공
3. `push_subscriptions` 테이블에 구독 정보 저장 확인
4. `POST http://localhost:8080/api/v1/push/test` 테스트 알림 전송 성공
5. 브라우저에 실제 알림 수신 확인
6. `GET http://localhost:8080/api/v1/user/notifications` 알림 설정 조회 성공
