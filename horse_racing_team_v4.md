# 🏇 RacePulse — 팀 회의 문서 v4

> **v1 아카이브**: `horse_racing_team.md` (킥오프~3차 회의 / 초기 설계 전체)
> **v2 아카이브**: `horse_racing_team_v2.md` (Phase 2 전체 기록)
> **v3 아카이브**: `horse_racing_team_v3.md` (Phase 3 전체 기록 + 17차 세션)
> **노션 워크스페이스**: https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad
> **현재 Phase**: Phase 4 준비 중 (2026-05-27 기준)

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
- **규칙**: API 변경 시 FE에 사전 공유 필수 / 공통 응답 `ApiResponse<T>` 형식 준수

### 2️⃣ FE (프론트엔드 개발자)
- **기술스택**: React 18 / TypeScript / Tailwind CSS v4 / Vite / PWA
- **담당**: 25개 라우트 UI / 동적 UI 32종 / 번들 최적화
- **우선순위**: 데이터 가독성 > UX 직관성 > 속도
- **규칙**: FE → Spring Boot 단일 창구 (FastAPI 직접 호출 금지) / 화면 문구 한글 전용

### 3️⃣ ARCH (아키텍처 & DB 담당)
- **기술스택**: PostgreSQL 16 / Redis 7 / Docker / AWS / Terraform
- **담당**: 시스템 설계 / DB 스키마 / 인프라 / 데이터 수집 파이프라인
- **우선순위**: 데이터 신뢰성 > 쿼리 성능 > 배포 안정성

### 4️⃣ ML (ML 엔지니어)
- **기술스택**: FastAPI / Python 3.13 / XGBoost / LightGBM / GPT-4.1 / APScheduler
- **담당**: 예측 모델 / Monte Carlo / AI 해설 / 데이터 수집 스케줄러
- **규칙**: 예측 생성은 조회 API와 분리 권장 / 사행성 필터 2중 적용 필수

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

### 8️⃣ NOTION (노션 담당자)
- **담당**: API 명세서 / DB 스키마 문서 / 스프린트 대시보드 / 배포 이력
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

## 🗄️ DB 현황 (Flyway V1~V13 / 총 43개 테이블)

| Flyway | 내용 |
|--------|------|
| V1 | Phase 0 — 15개 핵심 테이블 (말/기수/조교사/경주/출전/결과 등) |
| V2 | Phase 1 — 12개 서비스 테이블 (예측/AI해설/즐겨찾기/알림 등) |
| V3~V5 | Phase 1 — push_subscriptions / user_profile / Phase 3 테이블 |
| V6~V12 | Phase 2 — ML 피처스토어 / 경주출전 / 스키마 정렬 / rival+style |
| V13 | Phase 3 — trainer_changes / equipment_changes / user_wallets / AI 품질 컬럼 |

### 현재 DB 데이터 현황 (2026-05-27 기준)

| 테이블 | 건수 |
|--------|------|
| races | 12,898 |
| horses | 10,574 |
| race_entries | 132,601 |
| race_results | 132,243 |
| predictions | 426 |
| jockeys | 164 |
| trainers | 145 |

---

## 📊 ML 모델 성능 현황

| 모델 | 버전 | Top-1 | Top-3 | 피처 수 |
|------|------|-------|-------|---------|
| XGBoost | v1.0 | 83.01% | 89.07% | 23개 |
| LightGBM | v1.0 | 89.25% | 94.03% | 23개 |
| XGBoost | **v2.0** | **89.85%** | **99.85%** | 28개 |
| LightGBM | **v2.0** | **94.18%** | **99.4%** | 28개 |
| XGBoost | v3.0 | 85.31% | 98.85% | 28개 |
| LightGBM | v3.0 | 91.86% | 99.05% | 28개 |

- 피처 28개: 기본 23개 + 라이벌 직접 대결 + 주행 스타일 5개 추가
- 야간 자동 재학습: Task Scheduler 05:00 → nightly_pipeline.py

---

## 🔌 BE API 엔드포인트 (39개 확정 / `/api/v1/` 전체 적용)

| # | 분류 | 메서드 | 엔드포인트 | 권한 | 현재 상태 |
|---|------|--------|-----------|------|---------|
| 1~5 | 인증 | POST/GET | /auth/register, /login, /logout, /me, /refresh | GUEST/USER | ✅ |
| 6~7 | 카카오 | GET | /auth/kakao, /auth/kakao/callback | GUEST | ✅ |
| 8~12 | 경주 | GET | /races, /races/{id}, /races/{id}/full, /races/upcoming, /races/results | GUEST | ⚠️ upcoming·results 500 |
| 13~15 | 경주마 | GET | /horses, /horses/{id}, /horses/{id}/history | GUEST | ⚠️ {id} 500 |
| 16~17 | 기수/조교사 | GET | /jockeys/{id}, /trainers/{id} | GUEST | ❌ 403 미구현 |
| 18~20 | 예측/AI해설 | GET | /predictions/{raceId}, /commentary/{raceId}/pre, /commentary/{raceId}/post | GUEST | ✅ |
| 21~23 | 경마장/날씨 | GET | /racecourses, /racecourses/{meetCode}, /weather/{meetCode}/{date} | GUEST | ⚠️ {meetCode}·weather 500 |
| 24~25 | 검색/홈 | GET | /search, /home | GUEST | ⚠️ home 403 |
| 26~27 | 대시보드 | GET | /dashboard/accuracy, /dashboard/weekly | GUEST | ⚠️ weekly 500 |
| 28~34 | 유저 | GET/POST/DELETE/PATCH | /user/favorites, /user/history, /user/preferences, /user/notifications | USER | ✅ |
| 35~38 | 관리자 | GET/POST | /admin/collection/**, /admin/model/accuracy, /admin/commentary/regenerate | ADMIN | ✅ |
| 39 | 헬스체크 | GET | /health | GUEST | ✅ |

---

## ✅ 핵심 확정사항 (v1~v3 계승)

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

- Rate Limit: 일 3,000콜 → 2,800콜 도달 시 자동 중단
- 지수 백오프 재시도 5회

### Freemium / 편자 시스템
| 구분 | FREE | PREMIUM |
|------|------|---------|
| 예측 | 상위 4마리 / Top-3 확률만 | 전체 / Top-1 / 신뢰도 |
| 말 Stat | 속도 1개만 | 8개 전체 |
| AI 해설 | 요약 300자 | 전문 1000자 + Q&A |
| 광고 | 시청으로 잠금 해제 | 없음 |
| 체험 | 가입 후 7일 전체 무료 | — |

편자 시스템: 이벤트 편자(은색) / 구매 편자(금색) / 건초(다마고치 전용)

### Git / 배포 규칙
- 브랜치: `feat/*` → develop(PR, Merge commit) → main(Phase PR, Squash merge)
- 커밋: 프롬프트 1개 = 커밋 1개 / `feat: [prompt-N] 설명`
- feat 브랜치: 논리적으로 묶이는 3~5개 프롬프트 = 브랜치 하나
- 커밋 컨벤션: `feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`
- 배포: 화요일 02:00~06:00 정기 점검일 / 월요일 22:00 푸시 알림 + 배너 사전공지

### 외부 API
| API | 용도 | 환경변수 |
|-----|------|---------|
| 한국마사회 API | 경주 데이터 수집 | `KMA_API_KEY` |
| 기상청 API | 날씨 예보 | `WEATHER_API_KEY` |
| 카카오 OAuth 2.0 | 소셜 로그인 | `KAKAO_CLIENT_ID / SECRET` |
| OpenAI GPT API | AI 해설 | `OPENAI_API_KEY` |
| 포트원 (PortOne) | 결제 — Phase 5 도입 시 | 도입 시 추가 |

---

## 📅 전체 마일스톤

| Phase | 목표 | 완료 |
|-------|------|------|
| Phase 0 | 환경세팅 / DB / API 연동 | ✅ 2026-05-13 |
| Phase 1 | 수집파이프라인 / BE뼈대 / FE라우팅 | ✅ 2026-05-14 |
| Phase 2 | ML예측 / Monte Carlo / 시각화 대시보드 | ✅ 2026-05-15 |
| Phase 3 | AI해설 / Bayesian MC / Freemium / 편자 | ✅ 2026-05-22 |
| **Phase 4** | **Docker 복구 + API 완성 + 화면 완성 + 운영 품질** | 진행 중 |
| Phase 5 | 미니게임 (다마고치 + 퀴즈 + 토너먼트 + 상점) | 예정 |
| Phase 6 | AWS 배포 + CI/CD + 부하테스트 (Terraform) | 예정 |
| Phase 7 | README + 포트폴리오 문서화 | 최종 |

---

## 📝 완료된 작업 전체 (Phase 0~3 + 버그픽스)

### 프롬프트 실행 현황 (총 44개 완료)

| # | 프롬프트 | 담당 |
|---|---------|------|
| 01~10 | intro-video / be-basic-api / pwa / home-page / kra-api / weather-api / kakao-oauth / apscheduler-redis / web-push-vapid / fe-api-connect | FE/BE/ML |
| 11~20 | detail-pages / ml-feature-engineering / ai-commentary / dashboard / ml-model-training / prediction-page / dynamic-ui / monte-carlo / search-page / mypage | FE/ML |
| 21~28 | monte-carlo-advanced / be-race-api-fields / counterfactual-ui / dynamic-ui-phase2 / bundle-optimization / gpt-commentary / maintenance-mode / code-review-fixes | ML/FE/BE |
| 29~44 | V13-migration / bayesian-mc / sequential-race-dynamics / copula / change-detection / change-detection-api / ai-commentary-upgrade / privacy-be / freemium-be / privacy-fe / freemium-fe / horse-stat-card / dynamic-ui-phase3 / change-fe-ui / admin-panel / integration-test | DB/ML/BE/FE |

### 버그 수정 이력 (16~17차 세션)
- race_entries.win_odds → odds_win 컬럼명 수정
- SQL camelCase 별칭 큰따옴표 처리 (PostgreSQL 보존)
- Monte Carlo 기본값 70,000으로 수정
- 날씨 403 / NaN 카운트다운 / 몬테카를로 실데이터 연결
- FE preload 제거 / ECharts optimizeDeps / 스크립트 경로 수정

### Git 태그 이력
- `v2.0.0` — Phase 2 완료 (2026-05-15)
- `v3.0.0` — Phase 3 완료 (2026-05-22)
- `v3.0.1` — 버그픽스 포함 최종 (2026-05-27)

---

## 🔴 Phase 4 작업 목록 (우선순위 순)

> 작업 순서 원칙: Docker 복구 → API 구현 → 화면 구현 → 운영 품질
> (화면보다 API를 먼저 해야 화면 구현 시 뜯지 않아도 됨)

### 4-1. Docker 실행 재현성 복구 🔴 (최우선)

| # | 작업 | 현재 문제 | 파일 |
|---|------|---------|------|
| 1 | ML Dockerfile 이미지명 수정 | `python=:3.11-slim` 오타 → 빌드 실패 | `racepulse/ml-server/Dockerfile` |
| 2 | ML Compose DB URL 수정 | `postgresql://` → `postgresql+asyncpg://` | `racepulse/docker-compose.yml` |
| 3 | BE Dockerfile 작성 + Compose 실제 앱 연결 | 현재 임시 이미지(`eclipse-temurin:21-jre`) — 앱 없음 | `racepulse/docker-compose.yml` |

### 4-2. BE API 구현 🔴

| # | 작업 | 현재 상태 |
|---|------|---------|
| 4 | `GET /horses/{id}` 구현 | 500 (컨트롤러 없음) |
| 5 | `GET /jockeys/{id}` 구현 + SecurityConfig 공개 허용 | 403 (컨트롤러 없음) |
| 6 | `GET /trainers/{id}` 구현 + SecurityConfig 공개 허용 | 403 (컨트롤러 없음) |
| 7 | `GET /racecourses/{meetCode}` 구현 | 500 (컨트롤러 없음) |
| 8 | `/races/upcoming` 500 수정 | 쿼리 오류 |
| 9 | `/races/results` 500 수정 | 쿼리 오류 |
| 10 | `/dashboard/weekly` 500 수정 | 집계 쿼리 오류 |
| 11 | `/home` 403 수정 | SecurityConfig 공개 경로 누락 |
| 12 | FastAPI 스케줄러 상태 API 수정 | 별도 인스턴스 생성 → 항상 `running: false` |

### 4-3. FE Placeholder 화면 구현 🟡

| # | 화면 | 경로 | 비고 |
|---|------|------|------|
| 13 | 로그인 | `/login` | PrivateRoute가 여기로 리다이렉트 중 |
| 14 | 회원가입 | `/register` | |
| 15 | 카카오 OAuth 콜백 | `/auth/kakao/callback` | |
| 16 | 경주 결과 | `/races/:raceId/result` | API 200, 화면만 없음 |
| 17 | AI 해설 | `/races/:raceId/commentary` | API 200, 화면만 없음 |
| 18 | 경주마 목록 | `/horses` | DB 10,574마리 있음 |
| 19 | 경주마 성적 이력 | `/horses/:horseId/history` | |
| 20 | 경마장 목록 | `/racecourses` | |
| 21 | 경마장 상세 | `/racecourses/:meetCode` | |
| 22 | 관리자 대시보드 | `/admin` | |
| 23 | 수집 현황 | `/admin/collection` | |

### 4-4. 운영 품질 정리 🟡

| # | 작업 | 근거 |
|---|------|------|
| 24 | UI 영어 문구 한글화 | `AI RACE INTELLIGENCE`, `TODAY RACES`, `PREDICTION SCORE`, `WEEKLY REPORT` 등 |
| 25 | 날씨 API — FE ML 직접 호출 → Spring Boot 프록시 통일 | `raceApi.ts:26` / 아키텍처 규칙 위반 |
| 26 | `.gitignore` 로그 파일 추가 | `bulk_stdout.txt`, `bulk_stderr.txt`, `nightly_log.txt` 커밋 위험 |
| 27 | GitHub Actions 위치 정리 | 루트 `.github/workflows` vs `racepulse/.github/workflows` 중복 |
| 28 | 대시보드 데모 데이터 `isDemo: true` 플래그 추가 | Top-1/3 100% 오해 방지 |
| 29 | BE `/horses/{id}` 없는 경우 500 → 404 응답 개선 | 프론트 오류 구분 불가 |
| 30 | FastAPI charset 명시 (`application/json; charset=utf-8`) | 운영 도구 한글 깨짐 |
| 31 | 월간 마스터 수집 TODO 구현 | `scheduler.py collect_monthly` 미구현 |

---

## 🟢 Phase 5 — 미니게임 (Phase 4 완료 후)

### 게임 1: 다마고치 "나의 경주마"
- 실제 경주마 선택 → 밥주기(건초) / 훈련 / 일일 케어
- 실제 경주 결과가 말 컨디션에 자동 반영
- 연속 좋은 성적 → 레벨업 / 카드 등급 상승
- 출석 + 퀴즈로 편자/건초 획득

### 게임 2: 경마 마스터 퀴즈
- 실제 DB 데이터 기반 문제 자동 생성 (5문제 중 3개 / 시간제한 30초)
- 연속 정답 → 분석가 등급 상승

### Phase 5 이후: 토너먼트 + 상점
- 편자 토너먼트 (1위 150개 / 2위 100개 / 3위 60개)
- 아이템 상점 (사료/훈련/외형 구입)

---

## 🔵 Phase 6 — AWS 배포 (Phase 5 완료 후)

- **Terraform 사용** (이미 설치 완료)
- EC2 3서버 (React Nginx / Spring Boot BE / FastAPI ML) + ALB + CloudFront
- 배포 일정: 화요일 02:00~06:00 정기 점검일
- 부하 테스트: 동시 사용자 100명 / p95 500ms 목표

---

## 📄 Phase 7 — README + 포트폴리오 문서화 (최종 마무리)

- README.md (기술스택 / 아키텍처 / 실행방법 / 스크린샷 + 실제 URL)
- 포트폴리오 문서 (기술 선택 이유 / 성과 수치 / 예측 정확도)
- 마사회 API 상업적 이용 신청 (배포 후 진행)

---

## 💬 회의록

> Phase 0~3 전체 기록 → v1·v2·v3 아카이브 참조
> 노션 요약 → https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad

---

### [날짜: 2026-05-27] 18차 회의 — Phase 4 킥오프
- **참석**: BE, FE, ARCH, ML, PM, DESIGN, GIT, NOTION, WR, 창현님 — 전원

#### 회의 전 점검 결과 공유

**API 상태 (2026-05-27 전수 점검)**

| 상태 | API |
|------|-----|
| ✅ 200 | /health / /races / /racecourses / /search / /races/{id} / /races/{id}/entries / /races/{id}/result / /predictions/{raceId} / /commentary/{raceId}/pre / /horses(목록) / /dashboard/accuracy |
| ❌ 500 | /horses/{id} / /weather / /races/upcoming / /races/results / /dashboard/weekly |
| ❌ 403 | /home / /jockeys/{id} / /trainers/{id} |

**PROJECT_ISSUE_AUDIT_2026-05-27.md 주요 발견사항**
- ML Dockerfile 오타 → `docker compose up` 불가
- BE Docker Compose 임시 이미지 — 실제 앱 없음
- FE Placeholder 화면 11개 (로그인/결과/해설/경주마/경마장/관리자 등)
- FE가 날씨 API를 ML 서버 직접 호출 (Spring Boot 우회 — 아키텍처 규칙 위반)
- UI 영어 문구 다수 (전역 규칙 위반)
- GitHub Actions 워크플로우 중복

#### 최종 Phase 계획 (창현님 확정)

| Phase | 목표 |
|-------|------|
| Phase 4 | Docker 복구 + API 구현 + Placeholder 화면 완성 + 운영 품질 정리 |
| Phase 5 | 미니게임 (다마고치 + 퀴즈 + 토너먼트 + 상점) |
| Phase 6 | AWS 배포 + CI/CD + 부하테스트 (Terraform) |
| Phase 7 | README + 포트폴리오 문서화 (최종 마무리) |

#### 원칙 재확인 (창현님 결정)
- 최종 결정은 항상 창현님이 한다
- 팀원은 의견·근거·선택지 제시만 — 확정 선언 금지

---

## 📌 새 세션 인수인계 체크리스트

새 채팅을 열 때 반드시 이 파일(`horse_racing_team_v4.md`)을 읽고 시작할 것.
(v1·v2·v3는 필요 시 참조)

### 당장 해야 할 것 (Phase 4 우선순위 순)

```
1. 🔴 Docker 복구 3종
   - ML Dockerfile: python=:3.11-slim → python:3.11-slim
   - docker-compose.yml ML DB URL: postgresql:// → postgresql+asyncpg://
   - BE Dockerfile 작성 + Compose 실제 앱 연결

2. 🔴 BE API 구현 8종
   - /horses/{id} / /jockeys/{id} / /trainers/{id} / /racecourses/{meetCode}
   - /races/upcoming / /races/results / /dashboard/weekly 500 수정
   - /home 403 수정 (SecurityConfig 공개 경로 추가)
   - FastAPI 스케줄러 상태 API 실제 인스턴스 참조

3. 🟡 FE Placeholder 화면 구현 11개
   - 로그인 / 회원가입 / 카카오 콜백
   - 경주 결과 / AI 해설
   - 경주마 목록·상세·이력
   - 경마장 목록·상세
   - 관리자 대시보드·수집 현황

4. 🟡 운영 품질 정리 8종
   - UI 영어 문구 한글화
   - 날씨 API Spring Boot 프록시 통일
   - .gitignore 로그 파일 추가
   - GitHub Actions 중복 정리
   - 대시보드 isDemo 플래그
   - FastAPI charset 명시
   - 월간 마스터 수집 TODO 구현
```

### 현재 브랜치 상태 (2026-05-27 기준)
- `main` ← v3.0.1 태그 (버그픽스 최종) / v3.0.0 (Phase 3 완료)
- `develop` ← main과 동기화 완료
- 다음 브랜치: `feat/phase4-docker` 또는 `feat/phase4-be-api` 로 시작

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
진단 문서:            racepulse/PROJECT_ISSUE_AUDIT_2026-05-27.md
회의록 v4:            horse_racing_team_v4.md (이 파일)
```
