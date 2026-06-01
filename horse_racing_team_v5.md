# 🏇 RacePulse — 팀 회의 문서 v5

> **v1 아카이브**: `horse_racing_team.md` (킥오프~3차 회의 / 초기 설계 전체)
> **v2 아카이브**: `horse_racing_team_v2.md` (Phase 2 전체 기록)
> **v3 아카이브**: `horse_racing_team_v3.md` (Phase 3 전체 기록)
> **v4 아카이브**: `horse_racing_team_v4.md` (Phase 4 전체 기록)
> **노션 워크스페이스**: https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad
> **현재 Phase**: Phase 5 — UI/UX 전면 개선 (2026-06-01 시작)

---

## ⚠️ 절대 원칙

> **모든 최종 결정은 반드시 창현님이 합니다.**
> 팀원(AI 역할 포함)은 의견·근거·선택지를 제시할 수 있으나,
> 결론을 내리거나 확정 선언을 하지 않습니다.
> 회의록에 "확정"으로 기록되는 것은 오직 창현님이 승인한 내용만입니다.

---

## 🎯 프로젝트 개요

- **프로젝트명**: RacePulse
- **목표**: 경마 데이터 기반 순수 분석/예측 플랫폼 — 사행성 없음, 베팅 기능 없음
- **핵심 가치**: 예측 정확도 극대화 / 실운영 품질 / "세상에 없는 앱"
- **정확도 기준**: Top-3 60% 미만 → 피처 재검토 / 70% → Phase 2 진행 / **80% → 실운영 전환**
  - ✅ 달성: XGBoost v2.0 Top-3 **99.85%** / LightGBM v2.0 Top-3 **99.4%**

### 절대 하지 않는 것
- ❌ 베팅 기능 (직접 / 시뮬레이션 모두 없음)
- ❌ 포인트, 가상화폐, 랭킹 경쟁
- ❌ "이 말에 걸어라" 식의 직접적 투자 조언 뉘앙스
- ❌ 화면에 표시되는 문구에 영어 사용 (코드 내부 식별자는 허용)

---

## 👥 팀 구성 및 역할 정의

> 모든 역할은 창현님 1인이 AI와 함께 수행합니다.
> 각 역할은 해당 분야의 전문가 관점으로 의견을 제시합니다.

### 🟦 창현님 (프로젝트 오너)
- **권한**: 모든 최종 결정권
- **책임**: 실제 코드 작성 / 실행 환경 관리 / 외부 API 키 관리 / 배포 진행
- **규칙**: 결정 전 충분한 의견 수렴 요구 가능 / 언제든 계획 수정 가능

---

### 1️⃣ BE (백엔드 개발자)
- **기술스택**: Spring Boot 3.5 / Java 21 / JPA / QueryDSL / PostgreSQL / Redis
- **담당**: 인증/인가, REST API 39개, Spring Security, Flyway 마이그레이션
- **우선순위**: 데이터 정합성 > API 응답 속도 > 확장성
- **규칙**:
  - API 변경 시 FE에 사전 공유 필수
  - 공통 응답 `ApiResponse<T>` 형식 준수
  - 예외: `ResponseStatusException` 금지 → `BusinessException(ErrorCode.XXX)` 사용
  - URL prefix: `/api/v1/` 전체 적용
  - `application-dev.yaml` 민감키 기본값 하드코딩 금지
  - 도메인 구조: Controller → Service → Repository 패턴 유지

### 2️⃣ FE (프론트엔드 개발자)
- **기술스택**: React 18 / TypeScript / Tailwind CSS v4 / Vite / PWA
- **담당**: 25개 라우트 UI / 동적 UI 32종 / 번들 최적화
- **우선순위**: 데이터 가독성 > UX 직관성 > 속도
- **규칙**:
  - FE → Spring Boot 단일 창구 (FastAPI 직접 호출 절대 금지)
  - 화면 문구 한글 전용 (변수명·클래스명·enum·브랜드명 제외)
  - 기존 `axiosInstance` 재사용 (`src/services/axiosInstance.ts`) — 새 인스턴스 생성 금지
  - `localhost` URL 하드코딩 금지 — axiosInstance baseURL이 자동 처리
  - 기존 `Toast` 컴포넌트 재사용 (`src/components/Toast.tsx`)
  - `lazy()` + `Suspense` 패턴 유지
  - `data_status` ENUM: `READY / UPDATING / COLLECTED / JOCKEY_CHANGED`

### 3️⃣ ARCH (아키텍처 & DB 담당)
- **기술스택**: PostgreSQL 16 / Redis 7 / Docker / AWS / Terraform
- **담당**: 시스템 설계 / DB 스키마 / 인프라 / 데이터 수집 파이프라인
- **우선순위**: 데이터 신뢰성 > 쿼리 성능 > 배포 안정성

### 4️⃣ ML (ML 엔지니어)
- **기술스택**: FastAPI / Python 3.13 / XGBoost / LightGBM / GPT-4.1 / APScheduler
- **담당**: 예측 모델 / Monte Carlo / AI 해설 / 데이터 수집 스케줄러
- **규칙**:
  - 예측 생성은 조회 API와 분리 권장
  - 사행성 필터 2중 적용 필수
  - 기존 함수 구조와 동일한 패턴으로 작성
  - 에러 격리: 예외 발생 시 해당 단계만 실패 — 전체 파이프라인 중단 금지
  - KRA API SKIPPED 응답: 해당 job만 건너뜀, 파이프라인 계속 진행
  - `print()` 직접 사용 금지 — 기존 로그 패턴 사용
  - `nightly_pipeline.py` 수정 시: 동일 파일 건드리는 프롬프트는 반드시 순차 실행

### 5️⃣ PM (프로젝트 매니저)
- **담당**: 일정 관리 / 우선순위 조율 / 리스크 식별 / MVP 기준 유지
- **우선순위**: 제품 완성 > 기능 수 > 완성도

### 6️⃣ DESIGN (웹디자이너)
- **기술스택**: Figma
- **담당**: 디자인 시스템 / 컴포넌트 가이드 / 반응형 가이드
- **확정 방향**: "Bloomberg Terminal × Premium Sports Analytics" / 다크 네이비 + 골드
- **Figma 파일**: https://www.figma.com/design/CmPgsCrp7e5uWrucHtilue

### 7️⃣ GIT (Git 관리자)
- **담당**: 브랜치 전략 / PR 관리 / CI/CD / 보안 관리
- **브랜치 규칙**: `feat/*` → develop(PR, Merge commit) → main(Phase PR, Squash merge)
- **커밋 규칙**: 프롬프트 1개 = 커밋 1개 / `feat: [prompt-N] 설명`
- **커밋 컨벤션**: `feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`
- **배포**: 매주 화요일 02:00~06:00 정기 점검일
- **사전공지**: 월요일 22:00 푸시 알림 + 오후 배너

### 8️⃣ NOTION (노션 담당자)
- **담당**: API 명세서 / DB 스키마 문서 / 스프린트 대시보드 / 배포 이력 / 포트폴리오
- **규칙**: WR 전사 내용을 가공해 노션에 정리

### 9️⃣ WR (서기)
- **담당**: 회의 내용 실시간 전사 / 회의록 md 저장
- **규칙**: **회의 종료 시 반드시 md 파일 저장 — 예외 없음**

---

## 🏗️ 시스템 아키텍처 (✅ 확정)

```
[사용자 브라우저]
      ↕
[CloudFront CDN]
      ↕
[ALB]
      ↕
[React (Nginx)] ←→ [Spring Boot BE :8080] ←→ [PostgreSQL :5432]
                           ↕                         ↕
                     [FastAPI ML :8000]          [Redis :6379]
                           ↕
              [XGBoost/LightGBM / GPT-4.1]
                           ↕
              [한국마사회 API / 기상청 API]
```

**핵심 규칙**:
- FE → Spring Boot 단일 창구 (FastAPI 직접 호출 절대 금지)
- 데이터 수집 / 예측 / AI해설: FastAPI 전담
- 인증 / 유저 / 경주데이터: Spring Boot 전담

---

## 🗄️ DB 현황 (Flyway V1~V14 / 총 43개 테이블)

| Flyway | 내용 |
|--------|------|
| V1 | Phase 0 — 15개 핵심 테이블 (말/기수/조교사/경주/출전/결과 등) |
| V2 | Phase 1 — 12개 서비스 테이블 (예측/AI해설/즐겨찾기/알림 등) |
| V3~V5 | Phase 1 — push_subscriptions / user_profile / Phase 3 테이블 |
| V6~V12 | Phase 2 — ML 피처스토어 / 경주출전 / 스키마 정렬 / rival+style |
| V13 | Phase 3 — trainer_changes / equipment_changes / user_wallets / AI 품질 컬럼 |
| V14 | Phase 4 — horses 승률 컬럼 4개 (win_rate_total/recent, place_rate_total, debut_year) + races.moisture_level |

### 현재 DB 데이터 현황 (2026-06-01 기준)

| 테이블 | 건수 | 비고 |
|--------|------|------|
| races | ~12,900+ | — |
| horses | 10,574 | father_name·color 수집 예정 (Codex #8 nightly 월요일) |
| race_entries | ~132,800+ | — |
| race_results | ~132,400+ | — |
| predictions | 426 | — |
| jockeys | 164 | 마스터 데이터 수집 완료 |
| trainers | 145 | 마스터 데이터 수집 완료 |
| ml_feature_store | 277경주분 | 22차 세션 일괄 계산 완료 |

---

## 📊 ML 모델 성능 현황

| 모델 | 버전 | Top-1 | Top-3 | 피처 수 | 비고 |
|------|------|-------|-------|---------|------|
| XGBoost | v1.0 | 83.01% | 89.07% | 23개 | Phase 1 |
| LightGBM | v1.0 | 89.25% | 94.03% | 23개 | Phase 1 |
| XGBoost | **v2.0** | **89.85%** | **99.85%** | 28개 | Phase 2 최고 |
| LightGBM | **v2.0** | **94.18%** | **99.4%** | 28개 | Phase 2 최고 |
| XGBoost | v3.0 | 85.31% | 98.85% | 28개 | Phase 3 |
| LightGBM | v3.0 | 91.86% | 99.05% | 28개 | Phase 3 |
| XGBoost | **v1.0 (신규)** | **84.9%** | **94.87%** | 28개 | **22차 세션 — 신규 데이터셋 학습** |

- 22차 신규 v1.0: 학습 28,939건 / 테스트 7,234건 (새로 수집된 데이터 기준 재학습)
- 야간 자동 재학습: Task Scheduler 05:00 → nightly_pipeline.py

---

## 🔌 BE API 엔드포인트 (39개 / `/api/v1/` 전체 적용)

| # | 분류 | 메서드 | 엔드포인트 | 권한 | 상태 |
|---|------|--------|-----------|------|------|
| 1~5 | 인증 | POST/GET | /auth/register, /login, /logout, /me, /refresh | GUEST/USER | ✅ |
| 6~7 | 카카오 | GET | /auth/kakao, /auth/kakao/callback | GUEST | ✅ |
| 8~12 | 경주 | GET | /races, /races/{id}, /races/{id}/full, /races/upcoming, /races/results | GUEST | ✅ (prompt-2 완료) |
| 13~15 | 경주마 | GET | /horses, /horses/{id}, /horses/{id}/history | GUEST | ✅ (prompt-2 완료) |
| 16~17 | 기수/조교사 | GET | /jockeys/{id}, /trainers/{id} | GUEST | ✅ (prompt-2 완료) |
| 18~20 | 예측/AI해설 | GET | /predictions/{raceId}, /commentary/{raceId}/pre, /commentary/{raceId}/post | GUEST | ✅ |
| 21~23 | 경마장/날씨 | GET | /racecourses, /racecourses/{meetCode}, /weather/{meetCode}/{date} | GUEST | ✅ (prompt-2 완료) |
| 24~25 | 검색/홈 | GET | /search, /home | GUEST | ✅ |
| 26~27 | 대시보드 | GET | /dashboard/accuracy, /dashboard/weekly | GUEST | ✅ (prompt-2 완료) |
| 28~34 | 유저 | GET/POST/DELETE/PATCH | /user/favorites, /user/history, /user/preferences, /user/notifications | USER | ✅ |
| 35~38 | 관리자 | GET/POST | /admin/collection/**, /admin/model/accuracy, /admin/commentary/regenerate | ADMIN | ✅ |
| 39 | 헬스체크 | GET | /health | GUEST | ✅ |

---

## ✅ 핵심 확정사항 (v1~v4 계승)

### 인증 / 보안
- JWT (Access 1h / Refresh 24h~3d) + Rotation + Family 감지
- 카카오 OAuth 2.0 병행 / BCrypt(strength 10) / Rate Limiting (5회 실패 → 15분 잠금)
- Cookie: HttpOnly + Secure + SameSite=Strict
- dev: Secure=false / prod: Secure=true

### Monte Carlo
- Phase 2: QMC(Sobol) + Antithetic + Adaptive(10k~100k CI ±0.5%) + 병렬 4코어
- Phase 2: 게이트 브레이크 / 날씨 불확실성 / 스마트머니 / 신뢰도 점수
- Phase 3: Bayesian(Beta-Binomial) + Sequential Race Dynamics + Copula 상관행렬
- 기본값: **70,000회** (4차 회의 확정)

### 디자인 시스템 (Figma 동기화 완료)
- 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 컬러: `#07091A`(배경) / `#D4A843`(골드) / 골드 글로우
- 폰트: Playfair Display(브랜드) + Inter(데이터) + JetBrains Mono(수치/CI)
- Variables: Color×16 / Spacing×8 / Radius×5 / Duration×4
- 다크 모드 기본 / 라이트 모드 토글 가능

### AI 해설 (사행성 방지 규칙)
- 모델: GPT-4.1(사전 해설, temperature 0.7) / GPT-4.1-mini(결과 해설, temperature 0.3)
- 사전 해설: 금요일 08:00 자동 생성 (600~1000자)
- 결과 해설: 월요일 14:00 자동 생성 (800~1200자)
- 1차 필터: GPT 시스템 프롬프트 / 2차 필터: BE 키워드 스캔 / 품질점수 0~100
- 하단 고정 면책: "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."
- 절대 금지: "베팅 추천", "이 말에 투자", "확실한 1위", "다크호스"

### 데이터 수집 스케줄 (APScheduler)

| 시점 | 수집 내용 |
|------|-----------|
| 월요일 14:00 | 주말 경기 결과 |
| 화요일 09:00 | 월요일 경기 결과 |
| 목요일 10:00 | 주말 출전표 초안 |
| 목요일 17:30 | 출전표 업데이트 확인 |
| 금요일 08:00 | 출전표 확정본 |
| 토/일/월 09:05 | 마체중+증감, 기수변경, 트랙 상태 |
| 주 1회 | 경주마명단, 레이팅 |
| 월 1회 | 기수/조교사/마필/진료 정보 |
| **매주 월요일 (nightly 05:00)** | **마스터 데이터 전체 동기화 (sync_master_data — Phase 4 추가)** |

- Rate Limit: 일 3,000콜 → 2,800콜 도달 시 자동 중단
- 지수 백오프 재시도 5회
- 야간 자동화: Task Scheduler 03:00 BulkCollect + 05:00 NightlyPipeline (SYSTEM 계정)

### Freemium / 편자 시스템

| 구분 | FREE | PREMIUM |
|------|------|---------|
| 예측 | 상위 4마리 / Top-3 확률만 | 전체 / Top-1 / 신뢰도 |
| 말 Stat | 속도 1개만 | 8개 전체 |
| 변경사항 | "변경됨" 알림만 | 상세 전체 |
| AI 해설 | 요약 300자 | 전문 1000자 + Q&A |
| 광고 | 시청으로 잠금 해제 | 없음 |
| 체험 | 가입 후 7일 전체 무료 | — |

편자 시스템: 이벤트 편자(은색, 6개월) / 구매 편자(금색, 무기한) / 건초(다마고치 전용)

### Git / 배포 규칙
- 브랜치: `feat/*` → develop(PR, Merge commit) → main(Phase PR, Squash merge)
- 커밋: 프롬프트 1개 = 커밋 1개 / `feat: [prompt-N] 설명`
- feat 브랜치: 논리적으로 묶이는 3~5개 프롬프트 = 브랜치 하나
- 배포: 화요일 02:00~06:00 정기 점검일 / 월요일 22:00 푸시 알림 + 배너 사전공지

### 외부 API

| API | 용도 | 환경변수 |
|-----|------|---------|
| 한국마사회 API | 경주 데이터 수집 | `KMA_API_KEY` |
| 기상청 API | 날씨 예보 | `WEATHER_API_KEY` |
| 카카오 OAuth 2.0 | 소셜 로그인 | `KAKAO_CLIENT_ID / SECRET` |
| OpenAI GPT API | AI 해설 | `OPENAI_API_KEY` |
| 포트원 (PortOne) | 결제 — Phase 5 도입 시 | 도입 시 추가 |

### 실운영 대비
- 마사회 API 상업적 이용: 80% 달성 + 운영 결정 후 진행 (리스크 수용)
- OpenAI 비용: Freemium + 광고 수익화
- 개인정보보호법 준수: Phase 3 완료
- 결제: 포트원 (Phase 5 도입)

---

## 📋 Codex 프롬프트 작성 원칙

> **새 Codex 프롬프트를 작성할 때 반드시 `## ⚠️ 프로젝트 필수 규칙` 섹션을 포함해야 합니다.**
> 규칙이 없으면 Codex가 프로젝트 컨벤션을 무시한 코드를 생성합니다.

### 모든 프롬프트 공통
```
- 커밋 메시지: `feat: [prompt-N] 작업 설명` 형식 명시
- 코드 주석: 함수·중요 로직마다 WHY를 설명하는 주석 한 줄 이상
- 화면에 표시되는 모든 텍스트: 한글 전용 (변수명·클래스명·enum·브랜드명 제외)
```

### BE 프롬프트 포함 필수 규칙
```
- 예외 처리: ResponseStatusException 금지 → BusinessException(ErrorCode.XXX) 사용
- 공통 응답: ApiResponse<T> 래퍼 필수 / 목록은 PageResponse<T>
- URL prefix: /api/v1/ 전체 적용
- application-dev.yaml 민감키 기본값 하드코딩 금지
- 도메인 구조: Controller → Service → Repository 패턴 유지
```

### FE 프롬프트 포함 필수 규칙
```
- axios: 기존 axiosInstance 사용 (src/services/axiosInstance.ts) — 새 인스턴스 생성 금지
- 환경변수: localhost URL 하드코딩 금지 — axiosInstance baseURL이 자동 처리
- Toast: 기존 Toast 컴포넌트 재사용 (src/components/Toast.tsx)
- FE → Spring Boot만: FastAPI(8000) 직접 호출 절대 금지
- 라우팅: lazy() + Suspense 패턴 유지
- data_status: READY / UPDATING / COLLECTED / JOCKEY_CHANGED
```

### ML/Python 프롬프트 포함 필수 규칙
```
- 기존 함수 구조와 동일한 패턴으로 작성
- 에러 격리: 예외 발생 시 해당 단계만 실패 — 전체 파이프라인 중단 금지
- KRA API SKIPPED 응답: 해당 job만 건너뜀, 파이프라인 계속 진행
- 로그: 기존 로그 패턴 사용, print() 직접 사용 금지
- nightly_pipeline.py 수정 시: 동일 파일 건드리는 프롬프트는 반드시 순차 실행
```

---

## 📅 전체 마일스톤

| Phase | 목표 | 완료 |
|-------|------|------|
| Phase 0 | 환경세팅 / DB / API 연동 | ✅ 2026-05-13 |
| Phase 1 | 수집파이프라인 / BE뼈대 / FE라우팅 | ✅ 2026-05-14 |
| Phase 2 | ML예측 / Monte Carlo / 시각화 대시보드 | ✅ 2026-05-15 |
| Phase 3 | AI해설 / Bayesian MC / Freemium / 편자 | ✅ 2026-05-22 |
| Phase 4 | Docker 복구 + API 완성 + FE 화면 + 운영 품질 + 자동화 | ✅ 2026-06-01 |
| **Phase 5** | **UI/UX 전면 개선 (모바일 + 시각언어 + 애니메이션 + 데이터 밀도)** | **진행 중** |
| Phase 6 | 미니게임 (다마고치 + 퀴즈 + 토너먼트 + 상점) | 예정 |
| Phase 7 | AWS 배포 + CI/CD + 부하테스트 (Terraform) | 예정 |
| Phase 8 | README + 포트폴리오 문서화 | 최종 |

---

## ✅ Phase 4 완료 요약 (2026-05-27 ~ 2026-06-01)

### Codex 프롬프트 실행 현황 (8개 전체 완료)

| # | 프롬프트 | 주요 내용 | 완료 |
|---|---------|---------|------|
| 01 | docker-fix | ML Dockerfile 오타 / BE Dockerfile 신규 / Compose asyncpg URL | ✅ |
| 02 | be-security-api | /racecourses/{meetCode} / /races/upcoming·results / /dashboard/weekly 500 수정 | ✅ |
| 03 | admin-manual-collect | POST /admin/collection/trigger/entries·results / FE 관리자 수집 현황 화면 | ✅ |
| 04 | fe-login-screens | LoginPage / RegisterPage / KakaoCallbackPage | ✅ |
| 05 | fe-race-result-commentary | RaceResultPage / CommentaryPage | ✅ |
| 06 | quality-gitignore-i18n | UI 한글화 / 날씨 API 프록시 / .gitignore / charset=utf-8 | ✅ |
| 07 | nightly-result-resync | nightly_pipeline Phase 0 — 최근 14일 누락 결과 자동 재수집 | ✅ |
| 08 | master-data-weekly-sync | sync_master_data 함수 + 월요일 조건부 실행 + collect_horse_total_info | ✅ 직접 구현 |

### Phase 4 추가 작업 (직접 구현)

| 세션 | 작업 | 결과 |
|------|------|------|
| 18차 | Phase 4 킥오프 + 이슈 감사보고서 + 버그 2건 수정 | ✅ |
| 19차 | BE API 완성 (horses/jockeys/trainers) + KRA API 8종 확장 + V14 마이그레이션 | ✅ |
| 20차 | 5/23·24 마체중 재수집 + 마스터 수집 실행 + Codex #7~8 작성 | ✅ |
| 21차 | prompt-8 직접 구현 (kra_api/data_service/admin/nightly_pipeline) | ✅ |
| 22차 | bulk_collect.py ReadTimeout 수정 + 피처 277경주 계산 + XGBoost v1.0 학습 | ✅ |

### Git 태그 이력
- `v2.0.0` — Phase 2 완료 (2026-05-15)
- `v3.0.0` — Phase 3 완료 (2026-05-22)
- `v3.0.1` — 버그픽스 (2026-05-27)
- `v4.0.0` — Phase 4 완료 (발급 필요)

---

## 🎨 Phase 5 — UI/UX 전면 개선 — 총 36개

> **목표**: "재미없고 평범하다" → "세상에 없는 경마 플랫폼"
> 기능이 완성된 상태에서 다듬어야 재작업 없음

### 5-1. 모바일 필수 🔴

| # | 작업 | 상세 |
|---|------|------|
| 1 | 하단 네비게이션 바 | `홈/경주/즐겨찾기/검색/마이` — iPhone Safe Area 대응 |
| 2 | 햄버거 메뉴 드로어 | 왼쪽 슬라이드 패널 — 전체 메뉴 + 로그인 버튼 |
| 3 | 날짜 picker 커스텀 | 브라우저 기본 input → 골드/네이비 달력 팝업 |
| 4 | ECharts 차트 모바일 반응형 | 고정 height → `ResponsiveContainer` |
| 5 | WalletHUD 모바일 배치 개선 | 헤더 → 드로어 내부 이동 |

### 5-2. 경마 시각 언어 🔴

| # | 작업 | 상세 |
|---|------|------|
| 6 | 게이트 번호 컬러 배지 | 1흰/2검/3빨/4파/5노/6초/7주/8분홍 — 실제 경마 규격 |
| 7 | 말 폼 도트 | 최근 5경주 ●●○●● — 입상/미입상 시각화 |
| 8 | 트랙 컨디션 아이콘 | ☀️양호/🌥️보통/🌧️불량 — 날씨 API 연동 |
| 9 | 경주 거리 시각화 바 | 1000m~2400m 범위 내 현재 거리 위치 |
| 10 | 경마장 컬러 코딩 | 서울 빨강/부산 파랑/제주 초록 전역 일관 적용 |

### 5-3. 라이브 & 긴장감 🟡

| # | 작업 | 상세 |
|---|------|------|
| 11 | 라이브 펄스 배지 | `animate-ping` 빨간 점 — 1시간 전부터 표시 |
| 12 | 카운트다운 색 전환 | D+골드 → 12h주황 → 1h빨강 → 30m빨강+글로우 |
| 13 | 오늘의 주목 경주 스포트라이트 | 홈 최상단 — AI 신뢰도 최고 경주 풀와이드 |
| 14 | 실시간 배당 변동 인디케이터 | OddsMovementChart 카드 연결, ▲▼ 컬러 |

### 5-4. 디자인 시스템 개편 🟡

| # | 작업 | 상세 |
|---|------|------|
| 15 | 배경 서브틀 그리드 | 40×40px 반투명 격자 — Bloomberg Terminal 느낌 |
| 16 | 골드 그라데이션 테두리 | gradient border-image — 주요 카드 |
| 17 | 카드 계층 구조 3단계 | Hero(골드글로우)/Primary(현재)/Secondary(bg만) |
| 18 | 노이즈 텍스처 레이어 | 단색 배경 → 노이즈+그라데이션 오버레이 |

### 5-5. 애니메이션 & 인터랙션 🟡

| # | 작업 | 상세 |
|---|------|------|
| 19 | 페이지 전환 fade (Framer Motion) | 0.2초 fade + 위에서 살짝 내려오는 슬라이드 |
| 20 | 숫자 카운트업 애니메이션 | 대시보드 수치 0→실제값 1.2초 카운트업 |
| 21 | 카드 hover 골드 그림자 | `shadow-gold` + 좌측 골드 강조선 슬라이드인 |
| 22 | 예측 결과 stagger 등장 | 1위→2위→3위 0.1초 간격 순차 등장 |
| 23 | 스크롤 프로그레스 바 | 상단 얇은 골드 라인 — 페이지 스크롤 진행도 |

### 5-6. 데이터 밀도 강화 🟡

| # | 작업 | 상세 |
|---|------|------|
| 24 | 히어로 "지금 이 순간" 개편 | LIVE배지 + 다음 경주 카운트다운 + 예측 진행률 |
| 25 | 경주마 카드 미니 레이더 차트 | RatingRadarChart 컴포넌트 카드에 연결 |
| 26 | 주간 성적 히트맵 | 최근 20경주 GitHub 잔디 스타일 |
| 27 | 경마장 오늘 요약 카드 | 서울/부산/제주 — 경주수/날씨/트랙 나란히 |
| 28 | 말 비교 기능 | `/horses/compare?ids=1,2,3` 최대 3마리 |

### 5-7. 모바일 심화 🟢

| # | 작업 | 상세 |
|---|------|------|
| 29 | 무한 스크롤 | 페이지네이션 → `useInfiniteQuery` 전환 |
| 30 | Pull-to-refresh | 당겨서 새로고침 — 골드 스피너 |
| 31 | 스와이프 제스처 | 카드 우스와이프→즐겨찾기 / 좌스와이프→예측 |

### 5-8. Premium 디테일 🟢

| # | 작업 | 상세 |
|---|------|------|
| 32 | 로고 SVG 교체 | `RP` 텍스트 → 경주마 실루엣 + hover 달리기 애니메이션 |
| 33 | Upset Alert | 하위 배당 말의 통계적 유리함 표시 |
| 34 | 날씨×경주 상관관계 인사이트 | "비 올 때 이 말 Top-3 +18%" 맥락 |
| 35 | PWA 설치 유도 배너 | 3회 방문 후 "홈 화면에 추가" |
| 36 | 사운드 토글 | 경주 시작 알림음 / 예측 결과 팡파레 |

---

## 🎮 Phase 6 — 미니게임 (Phase 5 완료 후)

### 게임 1: 다마고치 "나의 경주마"
- 실제 경주마 선택 → 밥주기(건초) / 훈련 / 일일 케어
- 실제 경주 결과 → 말 컨디션 자동 반영
- 연속 좋은 성적 → 레벨업 / 카드 등급 상승
- 출석 체크 + 퀴즈로 편자/건초 획득

### 게임 2: 경마 마스터 퀴즈
- 실제 DB 데이터 기반 문제 자동 생성
- 5문제 중 3개 / 시간제한 30초
- 연속 정답 → 분석가 등급 상승

### 게임 3: 편자 토너먼트
- 1위 150개 / 2위 100개 / 3위 60개 / 주간 리더보드

### 게임 4: 아이템 상점
- 사료 / 훈련 / 외형 구입 / 편자(금/은) + 건초 통화 시스템

---

## ☁️ Phase 7 — AWS 배포 + CI/CD + 부하테스트

- **Terraform 사용** (이미 설치 완료)
- EC2 3대: React Nginx / Spring Boot BE / FastAPI ML
- ALB + CloudFront CDN / RDS PostgreSQL + ElastiCache Redis
- GitHub Actions → Docker Build → ECR → EC2 배포
- 부하 테스트: 동시 사용자 100명 / p95 500ms 목표
- 도메인 + HTTPS (ACM) / 마사회 API 상업적 이용 신청 (배포 후)

---

## 📄 Phase 8 — README + 포트폴리오 문서화 (최종 마무리)

- README.md (기술스택 / 아키텍처 / 실행방법 / 스크린샷 + 실제 URL)
- 포트폴리오 문서 (기술 선택 이유 / 성과 수치 / 예측 정확도 99.85%)
- 기술 블로그 포스팅 (선택)

---

## 💬 회의록

> Phase 0~3 전체 기록 → v1·v2·v3 아카이브 참조
> Phase 4 전체 기록 → v4 아카이브 참조
> 노션 요약 → https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad

---

## 📌 새 세션 인수인계 체크리스트

새 채팅을 열 때 반드시 이 파일(`horse_racing_team_v5.md`)을 읽고 시작할 것.
(v1~v4는 필요 시 참조)

### Phase 5 시작 전 처리 필요 사항

```
🔴 즉시 처리
  1. feat/phase4-bugfix → develop PR 생성 + 머지
  2. develop → main Phase 4 PR 생성 + 머지 (Squash merge)
  3. v4.0.0 태그 생성 + push

🟡 Phase 5 Codex 프롬프트 작성 시작
  - Phase 5 작업 목록 36개 → 병렬 가능한 것끼리 묶어서 프롬프트 작성
  - 반드시 ## ⚠️ 프로젝트 필수 규칙 섹션 포함 (CLAUDE.md 참조)
  - FE 위주 작업이므로 FE 규칙 섹션 필수
```

### 현재 브랜치 상태 (2026-06-01 기준)
- `main` ← v3.0.1 태그
- `develop` ← main과 동기화 완료
- `feat/phase4-bugfix` ← Phase 4 전체 작업 완료 (PR 생성 필요)

### 현재 실행 상태
- ✅ Docker PostgreSQL (5432) + Redis (6379): healthy
- ✅ Spring Boot BE (8080): 실행 중 (수동)
- ✅ FastAPI ML (8000): 실행 중 (venv 활성화 후 수동)
- ✅ Task Scheduler 03:00 BulkCollect + 05:00 NightlyPipeline: SYSTEM 계정 (자동)
- ⚠️ PC 재부팅 시 FastAPI + Spring Boot 수동 재실행 필요

### 주요 파일 경로 참조
```
프로젝트 루트:        C:\Programmer\Work\horse racing\
BE:                   racepulse/backend/
FE:                   racepulse/frontend/
ML 서버:              racepulse/ml-server/
DB 마이그레이션:       racepulse/backend/src/main/resources/db/migration/
Docker:               racepulse/docker-compose.yml
ML Dockerfile:        racepulse/ml-server/Dockerfile
자동화 스크립트:       racepulse/ml-server/scripts/
Codex 프롬프트:       codex-prompts/ (phase4-01~08.md)
CLAUDE 규칙:          CLAUDE.md (프로젝트 루트)
회의록 v5:            horse_racing_team_v5.md (이 파일)
```
