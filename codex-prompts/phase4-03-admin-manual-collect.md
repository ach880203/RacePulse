# Codex 프롬프트 — Phase 4-3: 수동 데이터 수집 API + 관리자 화면

## 작업 개요
자동 수집(Task Scheduler)이 실패할 경우를 대비한 수동 수집 기능을 추가합니다.
BE API 3개 신규 구현 + FE 관리자 수집 현황 페이지 구현이 함께 필요합니다.

---

## Part 1: BE — 수동 수집 API 구현

### 파일 위치
```
racepulse/backend/src/main/java/com/racepulse/backend/
└── domain/admin/
    ├── controller/AdminCollectionController.java  ← 수정/신규
    └── service/AdminCollectionService.java        ← 수정/신규
```

기존 `/api/v1/admin/collection/**` 구조가 있다면 그것을 확장합니다.

### API 1: 출전표 수동 수집

```
POST /api/v1/admin/collection/trigger/entries
권한: ADMIN
```

동작:
1. FastAPI ML 서버(`http://ml-server:8000/collection/entries`)에 수집 요청
2. 요청 성공 시 즉시 202 Accepted 반환 (동기 대기 없음)
3. 수집은 백그라운드에서 진행

응답:
```json
{
  "success": true,
  "data": { "triggeredAt": "2026-05-27T14:30:00", "type": "ENTRIES" },
  "message": "출전표 수집이 시작되었습니다."
}
```

### API 2: 경기 결과 수동 수집

```
POST /api/v1/admin/collection/trigger/results
권한: ADMIN
```

동작: FastAPI(`http://ml-server:8000/collection/results`)에 요청, 202 반환

응답:
```json
{
  "success": true,
  "data": { "triggeredAt": "2026-05-27T14:30:00", "type": "RESULTS" },
  "message": "경기 결과 수집이 시작되었습니다."
}
```

### API 3: 수집 상태 조회

```
GET /api/v1/admin/collection/trigger/status
권한: ADMIN
```

응답:
```json
{
  "success": true,
  "data": {
    "lastEntriesCollection": "2026-05-27T03:05:12",
    "lastResultsCollection": "2026-05-27T03:05:45",
    "lastEntriesStatus": "SUCCESS",  // SUCCESS | FAILED | RUNNING | UNKNOWN
    "lastResultsStatus": "SUCCESS"
  },
  "message": "수집 상태 조회 성공"
}
```

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-3] 수동 수집 API + 관리자 수집 현황 화면`

### BE 규칙
- **예외 처리**: `ResponseStatusException` 금지 — `BusinessException(ErrorCode.XXX)` 사용
- **공통 응답**: `ApiResponse<T>` 래퍼 필수
- **권한**: `@PreAuthorize("hasRole('ADMIN')")` 기존 패턴 사용
- **URL prefix**: `/api/v1/` 전체 적용
- **민감키 노출 금지**: `application-dev.yaml`에 키 기본값 하드코딩 금지
- **주석**: 각 메서드에 WHY 설명 한 줄 이상

### FE 규칙
- **axios**: 기존 `axiosInstance` 사용 — 새 axios 인스턴스 생성 금지 (`src/services/axiosInstance.ts`)
- **환경변수**: API URL 하드코딩 금지 — axiosInstance의 baseURL이 자동 처리
- **Toast**: 기존 `Toast` 컴포넌트 재사용 (`src/components/Toast.tsx`) — 새로 만들지 말 것
- **화면 문구**: 화면에 표시되는 모든 텍스트 한글 전용 (변수명·클래스명·enum 제외)
- **라우팅**: `lazy()` + `Suspense` 패턴 유지

### 코드 작성 규칙
- `ADMIN` 권한은 기존 `@PreAuthorize("hasRole('ADMIN')")` 패턴 사용
- FastAPI 호출은 `RestClient` 또는 `WebClient` 사용 (기존 코드 패턴 확인)
- 중복 실행 방지: 이미 실행 중이면 409 Conflict 반환
- 주석: 각 메서드에 WHY 설명 필수

---

## Part 2: FE — 수집 현황 페이지 구현

### 파일 위치
```
racepulse/frontend/src/pages/
└── admin/
    └── CollectionStatusPage.tsx    ← 신규 (또는 기존 Placeholder 교체)
```

라우트: `/admin/collection`

### 화면 구성

```
┌──────────────────────────────────────────────────────┐
│ 관리자 — 데이터 수집 현황                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│ [자동 수집 스케줄]                                    │
│ ● 03:00  BulkCollect (Task Scheduler)  ✅ 정상       │
│ ● 05:00  NightlyPipeline               ✅ 정상       │
│                                                      │
│ [마지막 수집]                                         │
│ 출전표:    2026-05-27 03:05  ✅ 성공                  │
│ 경기결과:  2026-05-27 03:05  ✅ 성공                  │
│                                                      │
│ [수동 수집]                                           │
│ ┌──────────────────┐ ┌──────────────────┐           │
│ │  📥 출전표 수집   │ │  📊 결과 수집    │           │
│ │  예정 경주 데이터 │ │  완료 경기 데이터 │           │
│ └──────────────────┘ └──────────────────┘           │
│ ┌──────────────────────────────────────┐            │
│ │          🔄 전체 수집                 │            │
│ │      출전표 + 결과 동시 실행          │            │
│ └──────────────────────────────────────┘            │
│                                                      │
│ ⚠️ 수집 중에는 버튼이 비활성화됩니다.                 │
└──────────────────────────────────────────────────────┘
```

### 구현 요구사항

1. **상태 조회**: 페이지 진입 시 `GET /api/v1/admin/collection/trigger/status` 호출
2. **수집 버튼**:
   - 클릭 시 해당 API 호출 + 버튼 비활성화 (로딩 스피너)
   - 성공: 초록 Toast "수집이 시작되었습니다"
   - 실패: 빨간 Toast "수집 시작에 실패했습니다. 다시 시도해주세요."
3. **전체 수집**: 두 API 순차 호출 (entries → results)
4. **자동 새로고침**: 수집 트리거 후 10초마다 상태 폴링 (최대 5회)

### 코드 작성 규칙
- 디자인 시스템: `bg-brand-navy-950` / `border-white/10` / `text-brand-gold-400` 패턴 사용
- 버튼 스타일: 골드 버튼 (기존 다른 페이지 버튼 스타일 참고)
- 주석: 각 함수/상태 변수에 역할 설명
- TypeScript: 응답 타입 정의 필수

### App.tsx 라우트 등록
`/admin/collection` 라우트의 `<Placeholder>` 를 새 컴포넌트로 교체:
```tsx
const CollectionStatusPage = lazy(() => import('./pages/admin/CollectionStatusPage'))
// ...
<Route path="/admin/collection" element={<CollectionStatusPage />} />
```

---

## 완료 기준
1. BE: 3개 API curl 테스트 성공
2. FE: `/admin/collection` 접근 시 실제 화면 렌더링
3. 수집 버튼 클릭 → Toast 표시 → 버튼 비활성화 동작 확인
