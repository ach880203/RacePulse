# 34. RacePulse 변경사항 BE API 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

이 프롬프트를 실행하기 **전에** 아래 파일들을 순서대로 전부 읽어야 합니다.

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, Spring Boot 구조 이해
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (변경감지 API 목록)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**:
- `prompt-29 (V13 마이그레이션)` 완료 필수 — trainer_changes / equipment_changes 테이블
- `prompt-33 (변경감지 ML)` 완료 필수 — Redis Pub/Sub 채널 `racepulse:changes` 발행

---

## 🗂️ 지금까지 한 작업 요약 (컨텍스트)

### Spring Boot 현황 (Phase 2 완료)
- **39개 엔드포인트** 구현 완료 (`/api/v1/` prefix)
- 공통 응답: `ApiResponse<T>` / `PageResponse<T>`
- 에러 처리: `global/exception/` 패키지 (BusinessException / GlobalExceptionHandler)
- Redis: `RedisTemplate` 설정 완료 (캐싱 + 웹 푸시 사용 중)
- 웹 푸시: `WebPushService.java` 구현 완료 (즐겨찾기 연동 가능)

### 변경사항 감지 흐름 (prompt-33 완료 후)
```
ML FastAPI (ChangeDetector)
  → Redis Pub/Sub 'racepulse:changes' 발행
    → Spring Boot (RedisSubscriber) 수신
      → DB 저장 + 즐겨찾기 유저 웹 푸시 발송
      → SSE 또는 REST API로 FE에 제공
```

---

## 목표

Spring Boot에 변경사항 관련 **신규 API 3개** + **Redis 구독자** + **웹 푸시 연동**을 구현합니다.

---

## 프로젝트 환경

- **BE**: Spring Boot / Java 21 / JPA / PostgreSQL
- **경로**: `backend/src/main/java/com/racepulse/`
- **기존 구조 참고**:
  - `domain/race/` — 경주 도메인 (기존 패키지 패턴 참고)
  - `global/response/ApiResponse.java` — 공통 응답 (반드시 사용)
  - `global/exception/` — 예외 처리 (반드시 사용)
  - `domain/user/service/WebPushService.java` — 즐겨찾기 푸시 (이미 구현됨)

---

## 현재 파일 구조 (추가할 위치)

```
backend/src/main/java/com/racepulse/
├── domain/
│   ├── race/
│   │   ├── controller/RaceController.java        ← 기존 (여기에 /changes 추가)
│   │   ├── service/RaceService.java
│   │   └── ...
│   └── change/                                   ← 신규 패키지
│       ├── controller/ChangeController.java       ← 신규
│       ├── service/ChangeService.java             ← 신규
│       ├── repository/TrainerChangeRepository.java ← 신규
│       ├── repository/EquipmentChangeRepository.java ← 신규
│       ├── entity/TrainerChange.java              ← 신규
│       ├── entity/EquipmentChange.java            ← 신규
│       └── dto/ChangeEventResponse.java           ← 신규
└── infrastructure/
    └── redis/
        └── ChangeEventSubscriber.java             ← 신규 (Redis 구독)
```

---

## 구현 사항

### 1. Entity 클래스 2개

**`TrainerChange.java`**:
```java
@Entity @Table(name = "trainer_changes")
// V13에서 생성된 trainer_changes 테이블과 매핑
// 필드: id, horse(ManyToOne), race(ManyToOne),
//       oldTrainer(ManyToOne), newTrainer(ManyToOne),
//       detectedAt(OffsetDateTime), changeDate(LocalDate),
//       previousChange(ManyToOne self-ref)
```

**`EquipmentChange.java`**:
```java
@Entity @Table(name = "equipment_changes")
// V13에서 생성된 equipment_changes 테이블과 매핑
// 필드: id, horse(ManyToOne), race(ManyToOne),
//       equipmentType(String), oldValue(String), newValue(String),
//       detectedAt(OffsetDateTime), changeDate(LocalDate),
//       blinkerFirstTime(boolean), previousChange(ManyToOne self-ref)
```

### 2. API 엔드포인트 3개

#### `GET /api/v1/races/{raceId}/changes`
특정 경주의 모든 변경사항 조회 (14차 회의 확정 엔드포인트)

```json
// 응답 예시
{
  "success": true,
  "data": {
    "raceId": 123,
    "hasChanges": true,
    "changes": [
      {
        "type": "JOCKEY",
        "badge": "🔴",
        "impact": "VERY_HIGH",
        "horseId": 456,
        "horseName": "천하무적",
        "oldValue": "박기수",
        "newValue": "김기수",
        "detectedAt": "2026-06-07T09:30:00+09:00"
      },
      {
        "type": "EQUIPMENT",
        "badge": "🟡",
        "impact": "MEDIUM",
        "horseId": 789,
        "horseName": "바람처럼",
        "oldValue": "블링커 없음",
        "newValue": "블링커 착용",
        "blinkerFirstTime": true,
        "detectedAt": "2026-06-07T10:00:00+09:00"
      }
    ]
  }
}
```

#### `GET /api/v1/races/changes/today`
오늘 날짜 전체 변경사항 조회 (홈 경보 배너, 알림 센터용)

```json
// 응답 예시
{
  "success": true,
  "data": {
    "date": "2026-06-07",
    "totalCount": 5,
    "highImpactCount": 2,
    "changes": [ ... ]
  }
}
```

#### `POST /api/v1/races/{raceId}/changes/subscribe` (USER 권한)
특정 경주 변경사항 알림 구독 (즐겨찾기와 별개로 개별 구독 가능)

```json
// 요청
{ "subscribe": true }

// 응답
{ "success": true, "data": { "subscribed": true } }
```

### 3. `ChangeEventSubscriber.java` — Redis 구독자

```java
// ML FastAPI(ChangeDetector)가 'racepulse:changes' 채널에 발행한 이벤트를 수신
// 수신 후:
//   1. ChangeService.processEvent() 호출 → DB 보정 (ML이 이미 저장했지만 BE도 확인)
//   2. 즐겨찾기 유저 + 구독 유저에게 웹 푸시 발송
//   3. 해설 재생성 여부 판단 (기수·조교사·장비 변경 시 → ML API 재생성 요청)

@Component
public class ChangeEventSubscriber implements MessageListener {
    @Override
    public void onMessage(Message message, byte[] pattern) {
        // JSON 파싱 → ChangeEventDto 변환
        // 즐겨찾기 유저 조회 → WebPushService.sendToUsers() 호출
        // 해설 재생성 필요 시 → ML FastAPI POST /ml/commentary/regenerate 호출
    }
}
```

**웹 푸시 메시지 형식:**
```java
// 기수 변경 시
title: "⚡ 기수 변경 알림"
body: "천하무적 — 박기수 → 김기수 (예측 영향: 매우 큼)"

// 출전 취소 시
title: "⛔ 출전 취소 알림"
body: "바람처럼 — 6경주 출전 취소"

// 조교사 변경 시
title: "🔄 조교사 변경 알림"
body: "질주본능 — 김조교사 → 이조교사"
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `@ManyToOne`이 무엇인지 설명 (여러 변경 이력이 하나의 말에 속함)
- 자기참조(self-referencing) FK가 뭔지 설명 (`previousChange`가 같은 테이블을 가리킴)
- `MessageListener`가 왜 필요한지 설명 (Redis 채널 메시지를 자동으로 받는 인터페이스)
- 웹 푸시가 즐겨찾기와 연동되는 이유 설명 (관심 말/경주 변경만 알려줘야 유저가 귀찮지 않음)
- `OffsetDateTime` vs `LocalDateTime` 차이 설명 (타임존 포함 여부)
- `hasChanges` 필드가 왜 별도로 있는지 설명 (FE에서 배지 표시 여부를 빠르게 판단)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장
- 한글 주석 깨짐 없이 확인

---

## Git 규칙

```
브랜치: feat/phase3-be-changes
커밋 메시지: feat: [prompt-34] 변경사항 BE API — GET /races/{id}/changes + Redis 구독 + 즐겨찾기 웹 푸시
```

---

## 완료 기준

```bash
# 1. BE 컴파일 성공
cd racepulse/backend
.\gradlew compileJava

# 2. API 동작 확인
# BE 서버 기동 후:
curl http://localhost:8080/api/v1/races/1/changes
# → {"success": true, "data": {"raceId": 1, "hasChanges": false, "changes": []}}

curl http://localhost:8080/api/v1/races/changes/today
# → {"success": true, "data": {"date": "...", "totalCount": 0, ...}}

# 3. Redis Pub/Sub 연동 테스트
# ML 서버에서 테스트 이벤트 발행:
# redis-cli PUBLISH racepulse:changes '{"type":"JOCKEY","race_id":1,"horse_id":1,"old_value":"박","new_value":"김"}'
# → BE 콘솔에 "변경 이벤트 수신: JOCKEY" 로그 확인
```
