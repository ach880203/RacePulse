# 43. RacePulse /admin 패널 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록, 기존 admin API 구현 내용
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: 모든 BE 프롬프트(33~37) 완료 — 관리자가 볼 데이터 API가 모두 준비됨

---

## 🗂️ 지금까지 한 작업 요약

### 기존 admin 엔드포인트 (Phase 2)
- `GET /api/v1/admin/collection/**` — 수집 현황
- `GET /api/v1/admin/model/accuracy` — ML 정확도
- `POST /api/v1/admin/commentary/regenerate` — 해설 재생성

### Phase 3에서 추가된 데이터
- **AI 해설 품질 점수**: `ai_commentary.quality_score` (V13)
- **변경 감지 이력**: `trainer_changes`, `equipment_changes`
- **편자 거래 내역**: `wallet_transactions`
- **ML 스케줄**: `change_detection_sat/sun/mon` APScheduler 잡

### 권한 구조
- `anyRequest().authenticated()` — 현재 모든 미허용 경로는 JWT 필요
- ADMIN 역할: `UserRole.ADMIN` enum 존재
- `/api/v1/admin/**` → ADMIN 권한으로 별도 제한 추가 필요

---

## 목표

### BE: 신규 admin API 4개 추가
`backend/src/main/java/com/racepulse/backend/domain/admin/`

1. `GET /api/v1/admin/commentary/quality` — AI 해설 품질 현황
2. `GET /api/v1/admin/changes/status` — 변경 감지 현황
3. `GET /api/v1/admin/wallet/stats` — 편자 통계
4. `GET /api/v1/admin/scheduler/jobs` — ML 스케줄러 잡 현황 (ML 서버 프록시)

### FE: `/admin` 페이지 신규
`frontend/src/pages/admin/AdminPage.tsx`

---

## 프로젝트 환경

- **BE**: Spring Boot / Java 21 / JPA / PostgreSQL
- **FE**: React 18 / TypeScript / Tailwind CSS v4
- **권한**: `@PreAuthorize("hasRole('ADMIN')")` — ADMIN 유저만 접근
- **디자인**: "Bloomberg Terminal × Premium Sports Analytics" 동일

---

## BE 구현 사항

### SecurityConfig 수정 — admin 경로 ADMIN 권한 제한

```java
.requestMatchers("/api/v1/admin/**").hasRole("ADMIN")
```

### 1. `GET /api/v1/admin/commentary/quality`

```json
// 응답 예시
{
  "success": true,
  "data": {
    "total": 120,
    "highCount": 95,       // quality_score >= 80
    "medCount": 18,        // 50~79
    "lowCount": 7,         // < 50
    "avgScore": 84.2,
    "fallbackCount": 2,    // retry 초과로 fallback 사용
    "recentLow3": false,   // 최근 3회 연속 LOW 여부 (알림 트리거)
    "byModel": {
      "gpt-4.1": { "count": 80, "avgScore": 88.1 },
      "gpt-4.1-mini": { "count": 40, "avgScore": 76.3 }
    }
  }
}
```

### 2. `GET /api/v1/admin/changes/status`

```json
{
  "success": true,
  "data": {
    "todayTotal": 5,
    "byType": {
      "JOCKEY": 2,
      "SCRATCH": 1,
      "TRAINER": 0,
      "EQUIPMENT": 1,
      "TRACK": 1
    },
    "lastDetectedAt": "2026-06-07T10:30:00+09:00",
    "schedulerRunning": true,
    "nextRunAt": "2026-06-07T11:00:00+09:00"
  }
}
```

### 3. `GET /api/v1/admin/wallet/stats`

```json
{
  "success": true,
  "data": {
    "totalUsers": 1240,
    "usersWithWallet": 980,
    "totalEventHorseshoe": 15200,
    "totalPaidHorseshoe": 4300,
    "todayEarned": { "EVENT": 320, "HAY": 960 },
    "todaySpent": { "TOP_1": 105, "AI_PRE": 50, "ENSEMBLE": 0 },
    "topSpentContent": "TOP_1"
  }
}
```

### 4. `GET /api/v1/admin/scheduler/jobs`

ML 서버(`FastAPI`)의 `/scheduler/jobs` 를 Spring Boot에서 프록시해서 반환:

```java
// RestTemplate으로 ML 서버 호출 (내부 네트워크)
ResponseEntity<String> response = restTemplate.getForEntity(
    mlServerUrl + "/scheduler/jobs", String.class
);
```

```json
{
  "success": true,
  "data": {
    "jobs": [
      { "id": "change_detection_sat", "nextRun": "2026-06-07T09:00:00" },
      { "id": "ai_pre_commentary",    "nextRun": "2026-06-07T08:30:00" }
    ]
  }
}
```

---

## FE 구현 사항

### `frontend/src/pages/admin/AdminPage.tsx`

**4개 섹션 탭 구조:**

```
[AI 해설 품질] [변경 감지 현황] [편자 통계] [수집 현황]
```

#### 탭 1: AI 해설 품질

```
┌─────────────────────────────────────────────────────┐
│ 🤖 AI 해설 품질 현황                               │
├────────────┬───────────┬────────────┬───────────────┤
│  HIGH 95건  │  MED 18건  │  LOW 7건   │ 평균 84.2점   │
│  ████████░  │           │           │               │
├─────────────────────────────────────────────────────┤
│ GPT-4.1      80건  avg 88.1점  ████████░░           │
│ GPT-4.1-mini 40건  avg 76.3점  ███████░░░           │
├─────────────────────────────────────────────────────┤
│ ⚠️ fallback 사용 2건            [재생성 트리거 →]    │
└─────────────────────────────────────────────────────┘
```

#### 탭 2: 변경 감지 현황

```
┌─────────────────────────────────────────────────────┐
│ 🔄 변경 감지 현황 (오늘)                            │
├───────────────────────────────────────────────────  │
│ 🔴 기수변경 2건   ⚫ 출전취소 1건   🟡 장비변경 1건 │
│ 🔵 트랙급변 1건   🟠 조교사변경 0건                 │
├─────────────────────────────────────────────────────┤
│ 마지막 감지: 10:30  ✅ 스케줄러 정상               │
│ 다음 실행: 11:00                                    │
└─────────────────────────────────────────────────────┘
```

#### 탭 3: 편자 통계

```
┌─────────────────────────────────────────────────────┐
│ 🔩 편자 시스템 통계                                 │
├──────────────┬──────────────┬────────────────────── │
│ 총 이벤트편자 │ 총 구매편자  │ 지갑 보유 유저       │
│   15,200개   │   4,300개    │   980명 / 1,240명    │
├─────────────────────────────────────────────────────┤
│ 오늘 획득 이벤트 320개    오늘 획득 건초 960개      │
├─────────────────────────────────────────────────────┤
│ 오늘 소비:  TOP-1 105편자 · AI사전 50편자           │
└─────────────────────────────────────────────────────┘
```

#### 탭 4: 수집 현황 (기존 admin API 활용)

기존 Phase 2 admin API 연결:
- ML 모델 정확도 표시
- 스케줄러 잡 목록 표시 (다음 실행 시각)
- 수집 체크포인트 표시

---

### `src/App.tsx` 수정

```tsx
const AdminPage = lazy(() => import('./pages/admin/AdminPage'))

// ADMIN 전용 라우트 (PrivateRoute + role 검사)
<Route element={<AdminRoute />}>
  <Route path="/admin" element={<AdminPage />} />
</Route>
```

`src/components/AdminRoute.tsx` 신규:
```tsx
// 로그인 여부 + ADMIN 역할 동시 검사
// ADMIN이 아니면 /unauthorized 페이지로 리다이렉트
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `hasRole('ADMIN')`이 왜 별도로 필요한지 설명 (관리자 기능은 일반 유저와 완전히 분리)
- RestTemplate으로 ML 서버를 프록시하는 이유 설명 (FE가 ML 서버에 직접 접근 금지 규칙)
- `recentLow3`가 왜 필요한지 설명 (연속 품질 저하 시 관리자가 빠르게 대응 가능)
- 탭 구조가 왜 관리자 UI에 적합한지 설명 (많은 정보를 카테고리별로 정리)

---

## 인코딩 주의사항 ⚠️

- 모든 파일 **UTF-8 (BOM 없음)** 저장

---

## Git 규칙

```
브랜치: feat/phase3-admin
커밋 메시지: feat: [prompt-43] /admin 패널 — AI 해설 품질 / 변경 감지 / 편자 통계 / 수집 현황 4탭
```

---

## 완료 기준

```bash
# 1. BE 컴파일
cd racepulse/backend
.\gradlew compileJava

# 2. FE 빌드
cd racepulse/frontend
npm run build

# 3. API 확인 (ADMIN 토큰 필요)
curl http://localhost:8080/api/v1/admin/commentary/quality \
  -H 'Authorization: Bearer {ADMIN_JWT}'
# → 200 OK + 품질 통계

# 4. /admin 페이지 접근 확인
# - ADMIN 계정 로그인 → /admin 접속 → 4탭 모두 표시
# - 일반 유저 로그인 → /admin 접속 → /unauthorized 리다이렉트
```
