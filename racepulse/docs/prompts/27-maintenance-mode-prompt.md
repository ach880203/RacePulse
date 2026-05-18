# 27. RacePulse 점검 모드 페이지 + 월요일 배너 + 푸시 알림 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표

정기 점검(매주 화요일 02:00~06:00) 대응 UI 3종을 구현합니다.

1. **점검 모드 페이지** — 점검 중 전체 화면 대체
2. **월요일 오후 배너** — "내일 새벽 2시 점검 예정" 사전 공지
3. **월요일 22:00 푸시 알림** — 웹 푸시 발송 (Web Push API)

4차 회의 확정: 매주 화요일 02:00~06:00 정기 점검일, 월요일 22:00 사전 공지.

---

## 프로젝트 환경

- **FE**: React 18 / TypeScript / Vite / Tailwind CSS v4
- **BE**: Spring Boot (푸시 알림 발송) / Web Push (VAPID 이미 설정됨)
- 디자인 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 컬러: `#07091A`(배경), `#D4A843`(골드)
- 폰트: Playfair Display / Inter / JetBrains Mono

---

## 현재 파일/폴더 구조

```
frontend/src/
├── pages/
│   ├── error/                    ← 에러 페이지 참고용
│   └── (MaintenancePage.tsx 새로 생성)
├── components/
│   └── (MaintenanceBanner.tsx 새로 생성)
└── App.tsx                       ← 점검 모드 조건부 라우팅 추가

backend/src/main/java/.../
└── domain/user/
    ├── service/WebPushService.java   ← 이미 구현됨
    └── controller/PushController.java
```

---

## 구현 사항

### 1. `MaintenancePage.tsx` — 점검 모드 전체 화면

**트리거 조건**: 매주 화요일 02:00~06:00 (KST) 또는 BE API가 503 응답 시

**화면 구성**:
```
┌─────────────────────────────────────┐
│         [RacePulse 로고]            │
│                                     │
│    🔧 정기 점검 중입니다             │
│                                     │
│    매주 화요일 02:00 ~ 06:00        │
│    서비스를 더 잘 만들기 위해        │
│    잠시 점검 중입니다.               │
│                                     │
│    완료 예정: 오전 6:00             │
│    [남은 시간 카운트다운]            │
│                                     │
│    이전 경주 결과 보기 →            │
└─────────────────────────────────────┘
```

**스타일**:
- 배경: `brand-navy-950` (#07091A)
- 로고: 골드 글로우 효과
- 카운트다운: JetBrains Mono 폰트, 골드 색상
- 부드러운 펄스 애니메이션 (점검 중 느낌)

**구현 로직**:
```typescript
// 화요일 02:00~06:00 KST 판별
function isMaintenanceTime(): boolean {
  const now = new Date()
  const kst = new Date(now.getTime() + 9 * 60 * 60 * 1000)
  return kst.getDay() === 2 && kst.getHours() >= 2 && kst.getHours() < 6
}
```

### 2. `MaintenanceBanner.tsx` — 월요일 오후 배너

**표시 조건**: 월요일 14:00~23:59 (KST)

**위치**: 앱 최상단 (Header 위)

**디자인**:
```
┌─────────────────────────────────────────────────────┐
│ ⚠️  내일 새벽 2시~6시 정기 점검 예정입니다   [닫기 X] │
└─────────────────────────────────────────────────────┘
```

- 배경: `#1a1200` (어두운 앰버)
- 테두리: `brand-gold-600` 좌측 4px 라인
- 닫기 버튼 클릭 시 `sessionStorage`에 저장 (새 탭 열면 다시 표시)

**App.tsx 통합**:
```tsx
// Header 위에 조건부 렌더링
{isMaintenanceWarningTime() && !dismissed && <MaintenanceBanner />}
```

### 3. 웹 푸시 알림 — 월요일 22:00 발송

**BE: Spring Boot**

`WebPushService.java`가 이미 VAPID 설정으로 구현됨.
APScheduler 또는 Spring Scheduled로 월요일 22:00 자동 발송 추가:

```java
// PushController.java 또는 ScheduledPushService.java에 추가
@Scheduled(cron = "0 0 22 * * MON", zone = "Asia/Seoul")
public void sendMaintenanceWarningPush() {
    String title = "RacePulse 점검 안내";
    String body  = "내일 새벽 2시~6시 정기 점검이 예정되어 있습니다.";
    // 모든 구독자에게 발송
    webPushService.sendToAll(title, body);
}
```

`WebPushService.java`에 `sendToAll()` 메서드 추가 (기존 sendToUser를 확장).

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `getDay() === 2`가 왜 화요일인지 설명 (0=일, 1=월, 2=화...)
- KST 변환 공식 설명 (+9시간)
- `sessionStorage` vs `localStorage` 차이 설명
- `@Scheduled` cron 표현식 설명
- Web Push가 어떻게 동작하는지 쉽게 설명 (브라우저 서버 역할)
- VAPID 키가 왜 필요한지 설명

---

## 인코딩 주의사항 ⚠️

- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석 깨짐 없도록 확인

---

## Git 규칙

```
브랜치: feat/phase2-maintenance-mode
커밋 메시지: feat: [prompt-27] 점검 모드 페이지 + 월요일 배너 + 푸시 알림 구현
```

---

## 완료 기준

```bash
# 1. FE 빌드 성공
npm run build

# 2. 동작 확인
# - App.tsx에서 isMaintenanceTime()을 임시로 true로 설정
# - /races 접속 시 MaintenancePage 표시 확인
# - 카운트다운 동작 확인

# 3. 배너 확인
# - isMaintenanceWarningTime()을 임시로 true로 설정
# - Header 위에 배너 표시 확인
# - [닫기] 버튼 동작 확인

# 4. BE 컴파일 성공
cd racepulse/backend && .\gradlew compileJava
```
