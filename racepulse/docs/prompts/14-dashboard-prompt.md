# 14. RacePulse 예측 정확도 대시보드 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
ML 예측 정확도를 실시간으로 보여주는 대시보드 페이지를 구현합니다.
누적 적중률을 공개 표시하고 유저가 모델 성능을 직접 확인할 수 있게 합니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4 (brand 토큰)
- Recharts (차트 라이브러리)
- @tanstack/react-query
- Spring Boot API: http://localhost:8080/api/v1

---

## 구현할 페이지

### 1. 정확도 대시보드 (`/dashboard`)
`src/pages/DashboardPage.tsx`

구성 섹션:
```
① 핵심 지표 카드 (상단)
   - 전체 예측 수
   - Top-1 정확도 (1위 적중률) → 원형 게이지
   - Top-3 정확도 (3위 이내 적중률) → 원형 게이지
   - 최근 30일 정확도

② 정확도 추이 차트
   - 월별 Top-1 / Top-3 정확도 꺾은선 그래프
   - Recharts LineChart 사용
   - X축: 날짜 / Y축: 정확도(%)

③ 경마장별 정확도
   - 서울 / 부산 / 제주 정확도 비교 바 차트
   - Recharts BarChart 사용

④ 최근 예측 목록
   - 경주명 / 예측 / 실제 결과 / 적중 여부
   - 적중: 초록 체크 / 미적중: 빨간 X
```

### 2. 주간 분석 페이지 (`/dashboard/weekly`)
`src/pages/WeeklyDashboardPage.tsx`

구성:
```
- 이번 주 경주 요약 (총 경주 수, 예측 수)
- 이번 주 예측 정확도
- 주목할 경주 하이라이트
- 다음 주 예정 경주 수
```

---

## 관련 Spring Boot API
`/api/v1/dashboard/accuracy` 응답 형식:
```json
{
  "success": true,
  "data": {
    "totalPredictions": 1250,
    "top1Accuracy": 42.5,
    "top3Accuracy": 68.2,
    "last30DaysTop1": 44.1,
    "byMeetCode": {
      "SC": { "top1": 43.0, "top3": 69.1 },
      "BU": { "top1": 41.5, "top3": 67.3 },
      "JJ": { "top1": 40.2, "top3": 65.8 }
    },
    "monthlyTrend": [
      { "month": "2026-01", "top1": 38.2, "top3": 64.5 },
      { "month": "2026-02", "top1": 40.1, "top3": 66.2 }
    ]
  }
}
```

---

## 동적 UI 컴포넌트

### 원형 게이지 컴포넌트
`src/components/CircularGauge.tsx`
- 정확도 퍼센트를 원형으로 표시
- 카운트업 애니메이션 (0%에서 실제값까지)
- 70% 이상: 골드 색상 / 60% 미만: 빨간색 / 그 사이: 노란색

### 예측 vs 실제 비교 컴포넌트
`src/components/PredictionResult.tsx`
- 예측 순위와 실제 순위 나란히 표시
- 적중 여부 아이콘

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- Recharts 컴포넌트 (LineChart, BarChart, PieChart) 사용법 설명
- 카운트업 애니메이션 구현 방법 설명 (useEffect + setInterval)
- 조건부 스타일링 (정확도에 따라 색상 변경) 설명
- Top-1 / Top-3 정확도 개념 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/레이블이 깨지지 않도록 확인

---

## 완료 기준
1. `http://localhost:3000/dashboard` 대시보드 페이지 표시
2. 원형 게이지 카운트업 애니메이션 동작
3. 월별 추이 꺾은선 차트 표시
4. 경마장별 정확도 바 차트 표시
5. 모바일 화면(375px)에서 레이아웃 정상 확인
