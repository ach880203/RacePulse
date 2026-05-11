# 11. RacePulse 상세 페이지 구현 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
경주 상세 / 출전 명단 / 경주마 상세 / 기수 상세 / 조교사 상세 페이지를 구현합니다.
Spring Boot API를 호출해서 실제 데이터를 표시합니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4 (brand 토큰 사용)
- @tanstack/react-query
- React Router v6 (useParams로 URL 파라미터 읽기)
- Spring Boot API: http://localhost:8080/api/v1

---

## 현재 파일 구조
```
frontend/src/
├── api/
│   ├── axiosInstance.ts    ← 10번으로 생성됨
│   ├── raceApi.ts          ← 10번으로 생성됨
│   └── horseApi.ts         ← 10번으로 생성됨
├── hooks/
│   ├── useRaces.ts         ← 10번으로 생성됨
│   └── useHorses.ts        ← 10번으로 생성됨
└── pages/
    ├── HomePage.tsx
    └── RaceListPage.tsx
```

---

## 구현할 페이지 5개

### 1. 경주 상세 페이지
`src/pages/race/RaceDetailPage.tsx` → 라우트: `/races/:raceId`

표시 내용:
```
- 경주 기본 정보 (경마장, 날짜, 거리, 트랙 상태, 출발 시각)
- 날씨 정보 (기온, 강수확률, 풍속)
- 경주 시작까지 카운트다운 타이머
- 출전 명단 보기 버튼 → /races/:raceId/entries
- 예측 결과 보기 버튼 → /races/:raceId/prediction
- AI 해설 보기 버튼 → /races/:raceId/commentary
```

### 2. 출전 명단 페이지
`src/pages/race/RaceEntriesPage.tsx` → 라우트: `/races/:raceId/entries`

표시 내용:
```
- 경주 요약 정보 (상단)
- 출전마 목록 (테이블 또는 카드 형태)
  - 마번(게이트 번호) / 말 이름 / 기수 / 조교사
  - 마체중 / 부담중량 / 배당률
  - 데이터 상태 뱃지 (기수변경 등)
- 말 이름 클릭 → /horses/:horseId 이동
- 기수 이름 클릭 → /jockeys/:jockeyId 이동
```

### 3. 경주마 상세 페이지
`src/pages/horse/HorseDetailPage.tsx` → 라우트: `/horses/:horseId`

표시 내용:
```
- 말 기본 정보 (이름, 성별, 출생연도, 소속 경마장)
- 레이팅 정보 (rating_1~4)
- 최근 5경주 성적 스파크라인 차트
- 경주 이력 테이블
  - 날짜 / 경마장 / 경주번호 / 착순 / 기록 / 기수
- 즐겨찾기 버튼 (로그인 시 활성화)
```

### 4. 기수 상세 페이지
`src/pages/jockey/JockeyDetailPage.tsx` → 라우트: `/jockeys/:jockeyId`

표시 내용:
```
- 기수 기본 정보 (이름, 소속 경마장)
- 통산 성적 (승률, 연대율)
- 최근 30/60/90일 성적
- 최근 출전 경주 목록
```

### 5. 조교사 상세 페이지
`src/pages/trainer/TrainerDetailPage.tsx` → 라우트: `/trainers/:trainerId`

표시 내용:
```
- 조교사 기본 정보
- 통산 성적
- 관리 중인 경주마 목록
```

---

## 추가 구현

### API 추가
`src/api/raceApi.ts` 에 추가:
```ts
fetchRaceEntries(raceId: number)   // 출전 명단
fetchRaceResult(raceId: number)    // 경주 결과
fetchWeather(meetCode: string, date: string)  // 날씨
```

`src/api/jockeyApi.ts` 신규 생성
`src/api/trainerApi.ts` 신규 생성

### 공통 컴포넌트
`src/components/CountdownTimer.tsx`
- 경주 시작까지 남은 시간을 실시간으로 표시
- HH:MM:SS 형식

`src/components/SparklineChart.tsx`
- 최근 5경주 착순을 간단한 선 차트로 표시
- Recharts 라이브러리 사용

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- `useParams()` 훅으로 URL 파라미터 읽는 방법 설명
- Recharts 차트 컴포넌트 사용법 설명
- `setInterval`로 카운트다운 만드는 방법 설명
- 페이지 간 이동 (`Link`, `useNavigate`) 차이 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 확인

---

## 완료 기준
1. `/races/1` 접속 시 경주 상세 페이지 표시
2. `/races/1/entries` 접속 시 출전 명단 표시
3. `/horses/1` 접속 시 경주마 상세 표시
4. 출전 명단에서 말 이름 클릭 시 경주마 상세로 이동
5. 카운트다운 타이머 실시간 동작 확인
