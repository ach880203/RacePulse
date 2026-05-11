# 16. RacePulse 예측 결과 페이지 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
ML 모델이 예측한 경주 결과를 유저에게 보여주는 페이지를 구현합니다.
각 말의 예측 승률, 근거 데이터, 컨디션 등급을 시각적으로 표시합니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4 (brand 토큰)
- Recharts
- @tanstack/react-query
- Spring Boot API: http://localhost:8080/api/v1

---

## 관련 Spring Boot API
```
GET /api/v1/predictions/{raceId}
```

응답 형식:
```json
{
  "success": true,
  "data": {
    "raceId": 1,
    "raceName": "서울 3경주",
    "modelVersion": "xgb-v1.0",
    "predictions": [
      {
        "horseId": 10,
        "horseName": "천하제일",
        "gateNo": 3,
        "predictedRank": 1,
        "winProbability": 34.5,
        "placeProbability": 58.2,
        "conditionGrade": "상",
        "keyFeatures": ["최근 3경주 연속 2위", "이 트랙 승률 42%", "기수 궁합 우수"]
      }
    ]
  }
}
```

---

## 구현 파일 목록

### 1. 예측 결과 페이지
`src/pages/race/RacePredictionPage.tsx` → 라우트: `/races/:raceId/prediction`

구성:
```
① 상단 경주 정보
   - 경주명, 날씨, 트랙 상태, 거리
   - 면책 문구: "본 예측은 순수 데이터 분석 목적입니다"

② 예측 순위 목록 (메인)
   - 말별 카드 (예측 순위 순으로 정렬)
   - 각 카드 내용:
     ① 예측 순위 번호 (크게)
     ② 말 이름 + 게이트 번호
     ③ 승률 바 차트 (스윕 애니메이션)
     ④ 컨디션 등급 색상 코딩
     ⑤ 핵심 근거 3가지 (예: "최근 3경주 연속 2위")

③ 모델 정보
   - 사용 모델 버전
   - 해당 모델 누적 정확도
```

### 2. 컨디션 등급 색상 규칙
```
최하 → 빨간색  (bg-red-500)
하   → 주황색  (bg-orange-400)
중   → 노란색  (bg-yellow-400)
상   → 연두색  (bg-lime-400)
최상 → 초록색  (bg-green-500)
```

### 3. API 호출
`src/api/predictionApi.ts` 신규 생성
- `fetchPrediction(raceId: number)` → 예측 결과 조회

`src/hooks/usePrediction.ts`
- `usePrediction(raceId)` → React Query 훅

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 승률을 바 차트로 표현하는 방법 설명
- 조건부 색상 클래스 적용 방법 설명
- 면책 문구가 왜 필요한지 설명
- 예측 순위와 실제 순위의 차이 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 확인

---

## 완료 기준
1. `/races/1/prediction` 접속 시 예측 결과 표시
2. 예측 순위 순으로 말 카드 정렬 확인
3. 승률 바 차트 스윕 애니메이션 동작
4. 컨디션 등급 색상 코딩 정상 표시
5. 면책 문구 표시 확인
