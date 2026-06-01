# RacePulse — Claude 작업 규칙

## 프로젝트 개요
- **프로젝트명**: RacePulse (경마 데이터 분석·예측 플랫폼)
- **현재 Phase**: Phase 4 진행 중
- **회의록**: `horse_racing_team_v4.md` (항상 먼저 읽고 시작)
- **Codex 프롬프트**: `codex-prompts/phase4-01~08.md`

---

## ⚠️ 절대 원칙

**모든 최종 결정은 창현님이 합니다.** Claude는 의견·근거·선택지만 제시.

---

## Codex 프롬프트 작성 규칙

새 Codex 프롬프트를 작성할 때 **반드시 `## ⚠️ 프로젝트 필수 규칙` 섹션을 포함**해야 합니다.

### 공통 (모든 프롬프트)
- 커밋 메시지: `feat: [prompt-N] 작업 설명` 형식 명시
- 코드 주석: 함수·중요 로직마다 WHY를 설명하는 주석 한 줄 이상
- 화면에 표시되는 텍스트: 한글 전용 (변수명·클래스명·enum·브랜드명 제외)

### BE 프롬프트 필수 포함
- 예외: `ResponseStatusException` 금지 → `BusinessException(ErrorCode.XXX)` 사용
- 응답: `ApiResponse<T>` 래퍼 필수, 목록은 `PageResponse<T>`
- URL: `/api/v1/` prefix 전체 적용
- `application-dev.yaml` 민감키 기본값 하드코딩 금지
- Controller → Service → Repository 도메인 구조 유지

### FE 프롬프트 필수 포함
- `axiosInstance` 재사용 (`src/services/axiosInstance.ts`) — 새 인스턴스 생성 금지
- `localhost` URL 하드코딩 금지 — axiosInstance baseURL이 자동 처리
- `Toast` 컴포넌트 재사용 (`src/components/Toast.tsx`) — 새로 만들지 말 것
- FastAPI(`8000`) 직접 호출 금지 — FE → Spring Boot 단일 창구
- `lazy()` + `Suspense` 패턴 유지
- `data_status` ENUM: `READY / UPDATING / COLLECTED / JOCKEY_CHANGED`

### ML/Python 프롬프트 필수 포함
- 기존 함수 구조와 동일 패턴으로 작성
- 에러 격리: 예외 발생 시 해당 단계만 실패, 전체 파이프라인 중단 금지
- KRA API `SKIPPED`: 해당 job만 건너뜀, 파이프라인 계속 진행
- `print()` 직접 사용 금지 — 기존 로그 패턴 사용
- `nightly_pipeline.py` 수정 프롬프트는 반드시 순차 실행 (동일 파일 충돌)

---

## 프로젝트 코딩 컨벤션

### Git
- 브랜치: `feat/*` → develop(PR, Merge commit) → main(Phase PR, Squash merge)
- 커밋: 프롬프트 1개 = 커밋 1개
- 컨벤션: `feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`

### 아키텍처
- FE → Spring Boot(8080) 단일 창구, FastAPI(8000) 직접 호출 절대 금지
- 데이터 수집·예측·AI 해설: FastAPI 전담
- 인증·유저·경주 데이터: Spring Boot 전담

### 주요 파일 경로
```
BE:           racepulse/backend/
FE:           racepulse/frontend/
ML 서버:       racepulse/ml-server/
DB 마이그레이션: racepulse/backend/src/main/resources/db/migration/
Codex 프롬프트: codex-prompts/
```

### 사행성 방지 (AI 해설 관련 작업 시)
- 절대 금지: "베팅 추천", "이 말에 투자", "확실한 1위", "다크호스"
- 면책 문구 필수 고정: "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."
