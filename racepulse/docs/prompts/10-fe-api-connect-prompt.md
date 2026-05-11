# 10. RacePulse FE - BE API 연동 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
React 프론트엔드에서 Spring Boot 백엔드 API를 실제로 호출합니다.
더미 데이터를 제거하고 실제 경주/경주마/경마장 데이터를 화면에 표시합니다.

---

## 프로젝트 환경
- React 18 + TypeScript
- Vite 6.x
- Tailwind CSS v4
- axios 1.x
- @tanstack/react-query (서버 상태 관리)
- React Router v6
- Spring Boot API 주소: http://localhost:8080/api/v1

---

## 현재 파일 구조
```
frontend/src/
├── App.tsx
├── main.tsx
├── index.css
├── api/              ← 비어있음 (이번에 채움)
├── pages/
│   ├── HomePage.tsx          ← 04번으로 생성됨 (더미 데이터 제거)
│   └── RaceListPage.tsx      ← 04번으로 생성됨 (더미 데이터 제거)
└── components/
    └── layout/
        ├── Header.tsx
        └── Layout.tsx
```

---

## 구현 파일 목록

### 1. Axios 기본 설정
`src/api/axiosInstance.ts`
- baseURL: `http://localhost:8080/api/v1`
- 요청 인터셉터: JWT Access Token 자동 첨부
- 응답 인터셉터: 401 시 Refresh Token으로 재발급 후 재요청
- 에러 응답 형식: `{ success: false, data: null, message: "..." }`

### 2. API 호출 파일 (도메인별 분리)
`src/api/raceApi.ts`
```ts
// 경주 목록 조회
fetchRaces(params: { meetCode?: string, rcDate?: string, status?: string, page?: number, size?: number })

// 경주 상세 조회
fetchRaceById(raceId: number)

// 다가오는 경주 조회
fetchUpcomingRaces()
```

`src/api/horseApi.ts`
```ts
// 경주마 목록 조회
fetchHorses(params: { meetCode?: string, name?: string, page?: number, size?: number })

// 경주마 상세 조회
fetchHorseById(horseId: number)
```

`src/api/racecourseApi.ts`
```ts
// 경마장 전체 조회
fetchRacecourses()
```

### 3. TypeScript 타입 정의
`src/types/race.ts`
```ts
interface Race {
  id: number
  meetCode: string
  rcDate: string
  raceNo: number
  raceName: string
  distance: number
  status: 'SCHEDULED' | 'COMPLETED' | 'CANCELLED'
  startTime: string
}

interface PageResponse<T> {
  content: T[]
  totalElements: number
  totalPages: number
  number: number
  size: number
}
```

`src/types/horse.ts`
`src/types/racecourse.ts`

### 4. React Query 훅
`src/hooks/useRaces.ts`
- `useRaces(params)` → 경주 목록 조회
- `useRace(raceId)` → 경주 상세 조회
- `useUpcomingRaces()` → 다가오는 경주

`src/hooks/useHorses.ts`
`src/hooks/useRacecourses.ts`

### 5. React Query Provider 설정
`src/main.tsx` 수정
- `QueryClientProvider` 추가
- 기본 설정: staleTime 5분, retry 1회

### 6. 페이지 컴포넌트 수정
`src/pages/HomePage.tsx`
- 더미 데이터 제거
- `useUpcomingRaces()` 훅으로 실제 데이터 표시
- 로딩 중: 스켈레톤 UI 또는 "데이터 불러오는 중..." 표시
- 데이터 없음: "오늘 예정된 경주가 없습니다" 표시
- 에러: "데이터를 불러오지 못했습니다" 표시

`src/pages/RaceListPage.tsx`
- 더미 데이터 제거
- `useRaces(params)` 훅으로 실제 데이터 표시
- 필터 변경 시 API 재호출
- 페이지네이션 구현

---

## 데이터 상태 표시 컴포넌트
`src/components/DataStatusBadge.tsx`

data_status 값에 따라 뱃지 표시:
```
READY         → "준비중"         (회색 뱃지)
UPDATING      → "업데이트 예정"  (파란색 뱃지)
COLLECTED     → "데이터 수집 중" (노란색 뱃지, 깜빡임)
JOCKEY_CHANGED → "기수변경"      (빨간색 뱃지)
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- @tanstack/react-query 개념 설명 (왜 쓰는지, useState와 차이)
- 인터셉터가 무엇인지 설명 (요청/응답 가로채기)
- TypeScript interface가 무엇인지 설명
- async/await와 Promise 개념 쉽게 설명
- 로딩/에러/성공 상태 처리 이유 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 확인

---

## 완료 기준
1. `http://localhost:3000` 홈 화면에 실제 경마장 데이터 표시
2. `http://localhost:3000/races` 에서 실제 경주 목록 표시
3. 필터(경마장/날짜) 변경 시 API 재호출 확인
4. 로딩 중 상태 표시 확인
5. 데이터 없을 때 빈 상태 메시지 표시 확인
6. Chrome 개발자 도구 → Network 탭에서 API 호출 확인
