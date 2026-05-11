# RacePulse 프로젝트 규칙서

> 모든 프롬프트 작성 전 이 파일을 반드시 참고하세요.
> 모든 코드 생성 시 아래 규칙을 반드시 준수해야 합니다.

---

## 📌 필수 공통 규칙 (모든 작업에 적용)

### 규칙 1: 한국어 주석 필수
이 프로젝트 개발자는 **코딩 입문자**입니다. **학생을 가르친다는 생각**으로 주석을 작성하세요.
- 모든 코드에 한국어 주석 필수 (영어 주석 금지)
- import 한 줄 한 줄마다 어떤 라이브러리인지 설명
- 함수/변수/클래스 하나하나 역할 설명
- 처음 보는 개념(async, useEffect, @Entity 등)은 쉬운 말로 설명
- "이게 뭔지(WHAT)"와 "왜 이렇게 했는지(WHY)" 모두 설명
```tsx
// 예시 스타일
// useEffect = 컴포넌트가 화면에 나타났을 때 자동으로 실행되는 함수
// 두 번째 인자 [] = 처음 한 번만 실행하겠다는 의미 (의존성 없음)
useEffect(() => { ... }, [])
```

---

### 규칙 2: UTF-8 인코딩 필수
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 저장 전 인코딩 확인
- Python 파일 최상단: `# -*- coding: utf-8 -*-`
- IntelliJ: File → File Properties → File Encoding → UTF-8
- VS Code: 우측 하단 인코딩 클릭 → UTF-8 확인

---

### 규칙 3: 환경변수 규칙
- API 키, 비밀번호를 코드에 **절대 직접 작성 금지**
- 모든 민감 정보는 반드시 `.env` 파일에서 관리
- `.env` 파일은 절대 Git에 커밋 금지 (`.gitignore`에 등록됨)

---

### 규칙 4: TODO 주석 형식
미완성 코드는 아래 형식으로 통일해서 표시
```
// TODO: [Phase 숫자] 설명
// 예: // TODO: [Phase 2] 마사회 API 연동 후 실제 데이터로 교체
// 예: // TODO: [Phase 3] AI 해설 로직 추가
```
나중에 `TODO` 검색으로 미완성 코드를 한번에 찾을 수 있습니다.

---

## 🖥️ 백엔드 규칙 (Spring Boot)

### 규칙 5: API 응답 형식 통일
모든 API는 아래 형식으로 응답해야 합니다.
```json
// 성공
{ "success": true, "data": { ... }, "message": "조회 성공" }

// 실패
{ "success": false, "data": null, "message": "오류 내용" }
```
`global/response/ApiResponse.java` 공통 클래스 사용.

---

### 규칙 6: Exception 처리 통일
- 에러 발생 시 `global/exception/` 패키지의 공통 에러 처리 클래스 사용
- 각 API에서 개별적으로 try-catch 남발 금지
- 커스텀 예외는 `global/exception/` 에 정의

---

### 규칙 7: DTO ↔ Entity 구분 필수
- DB와 연결된 **Entity를 API 응답에 직접 사용 금지**
- 반드시 DTO(Response/Request)로 변환 후 응답
- 이유: 보안 문제 + DB 구조 변경 시 API 영향 최소화
```
Entity (DB용) → Service → DTO (API 응답용)
```

---

## 🎨 프론트엔드 규칙 (React)

### 규칙 8: 파일/컴포넌트 네이밍
```
페이지 컴포넌트:  PascalCase  → RaceListPage.tsx
공통 컴포넌트:   PascalCase  → HorseCard.tsx
커스텀 훅:      use로 시작   → useRaceData.ts
API 호출 파일:   camelCase   → raceApi.ts
유틸 함수:      camelCase   → formatDate.ts
```

---

### 규칙 9: API 호출 위치 규칙
- API 호출 코드를 컴포넌트 안에 직접 작성 금지
- 반드시 `src/api/` 폴더에 도메인별 파일로 분리
```
src/api/
├── raceApi.ts
├── horseApi.ts
└── authApi.ts
```

---

### 규칙 10: 컬러 하드코딩 금지
- `#f5c842` 같은 색상 코드를 코드에 직접 작성 금지
- 반드시 Tailwind 브랜드 토큰만 사용
```tsx
// ❌ 금지
style={{ color: '#f5c842' }}

// ✅ 허용
className="text-brand-gold-400"
```

---

### 규칙 11: 이미지/아이콘 위치 규칙
```
이미지:  frontend/public/images/
아이콘:  frontend/src/assets/icons/
영상:    frontend/public/
```

---

## 🗄️ 데이터베이스 규칙

### 규칙 12: DB 인덱스 네이밍
모든 인덱스는 아래 형식으로 통일
```sql
idx_테이블명_컬럼명
-- 예: idx_horses_meet_code
-- 예: idx_races_rc_date
```

---

### 규칙 13: Flyway 마이그레이션 파일 수정 금지
- 한번 실행된 Flyway 파일(V1__, V2__ 등)은 **절대 수정 금지**
- 수정이 필요하면 새 버전 파일 추가 (V5__, V6__ 등)
- 어길 경우 Flyway 체크섬 오류로 서버가 실행되지 않음

---

## 🔀 Git 규칙

### 규칙 14: PR 없이 develop 직접 push 금지
- 아무리 작은 수정도 feature 브랜치 만들고 PR로 머지
- 직접 push는 긴급 hotfix 상황에만 허용

---

### 규칙 15: 커밋 전 체크리스트
```
□ .env 파일이 커밋에 포함됐나? (포함되면 안 됨)
□ TODO 주석 달았나?
□ 한글 깨짐 없나?
□ 커밋 메시지 형식 맞나? (feat/fix/docs/style/refactor/test/chore)
```

---

## 📝 프롬프트 작성 규칙

### 규칙 16: 프롬프트 파일 네이밍
```
형식: 숫자(2자리)-설명.md
예시: 01-intro-video-prompt.md
      02-be-basic-api-prompt.md
      03-pwa-prompt.md
```

---

### 규칙 17: 프롬프트 필수 구조
모든 프롬프트는 아래 순서로 작성
```
1. 목표
2. 프로젝트 환경 (기술스택, 버전)
3. 현재 파일/폴더 구조
4. 구현 사항 (상세)
5. 주석 요구사항 ⚠️ (규칙 1 기준)
6. 인코딩 주의사항 ⚠️ (규칙 2 기준)
7. 완료 기준
```

---

### 규칙 18: 프롬프트 시작 문구 필수 포함
모든 프롬프트 최상단에 아래 문구 포함
```
이 프롬프트를 실행하기 전에 docs/PROJECT_RULES.md 파일을 먼저 읽고
모든 규칙을 준수하여 코드를 작성해주세요.
```

---

## 🗓️ 회의 규칙

### 규칙 19: 회의 종료 체크리스트 (WR 담당)
```
□ md 파일 저장했나?
□ 확정 사항 창현님 동의 받았나?
□ 다음 회의 안건 정리했나?
```

---

### 규칙 20: 확정 규칙
- 창현님은 회의 참여자이자 **최종 결정권자**
- 팀원들이 논의해도 창현님 동의 없이 확정 처리 금지
- 창현님이 명확히 동의한 후에만 ✅ 확정으로 기록

---

*최초 작성일: 2026-05-08*
*총 규칙: 20개*
