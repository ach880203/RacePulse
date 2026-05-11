# 19. RacePulse 검색 페이지 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
경주마, 기수, 조교사, 경주를 통합 검색하는 페이지를 구현합니다.
검색어 입력 시 실시간으로 결과를 보여줍니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4
- @tanstack/react-query
- Spring Boot API: http://localhost:8080/api/v1

---

## 관련 Spring Boot API
```
GET /api/v1/search?q={검색어}&type={타입}&page={페이지}
```

응답 형식:
```json
{
  "success": true,
  "data": {
    "query": "천하",
    "horses": [
      { "id": 1, "name": "천하제일", "meetCode": "SC", "thumbnailUrl": null }
    ],
    "jockeys": [],
    "trainers": [],
    "races": []
  }
}
```

---

## 구현 파일 목록

### 1. 검색 페이지
`src/pages/SearchPage.tsx` → 라우트: `/search`

구성:
```
① 검색창
   - 큰 입력창 (placeholder: "경주마, 기수, 조교사, 경주 검색")
   - 검색어 입력 중 실시간 검색 (300ms 디바운스)
   - 최근 검색어 (localStorage 저장)

② 필터 탭
   - 전체 / 경주마 / 기수 / 조교사 / 경주

③ 검색 결과
   - 타입별 섹션으로 구분
   - 결과 없음: "검색 결과가 없습니다" 메시지
   - 로딩 중: 스켈레톤 UI

④ 결과 카드
   - 경주마: 이름 / 소속 경마장 → /horses/:id 이동
   - 기수: 이름 / 소속 경마장 → /jockeys/:id 이동
   - 경주: 경주명 / 날짜 → /races/:id 이동
```

### 2. 디바운스 훅
`src/hooks/useDebounce.ts`
- 입력 후 300ms 뒤에 검색 실행 (타이핑마다 API 호출 방지)

### 3. API 호출
`src/api/searchApi.ts`
- `search(query: string, type?: string)` → 통합 검색

### 4. 최근 검색어
- localStorage에 최대 10개 저장
- 검색창 클릭 시 최근 검색어 드롭다운 표시
- 각 검색어 삭제 버튼

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 디바운스(debounce)가 무엇인지 설명 (왜 필요한지)
- useDebounce 훅 동작 원리 설명
- localStorage로 최근 검색어 저장하는 방법 설명
- 스켈레톤 UI가 무엇인지 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 검색어가 깨지지 않도록 확인
- URL 인코딩 처리 (`encodeURIComponent`)

---

## 완료 기준
1. `/search` 접속 시 검색 페이지 표시
2. "천하" 검색 시 관련 경주마 목록 표시
3. 300ms 디바운스 동작 확인 (Network 탭에서 요청 횟수 확인)
4. 최근 검색어 localStorage 저장 확인
5. 검색 결과 클릭 시 해당 상세 페이지로 이동 확인
