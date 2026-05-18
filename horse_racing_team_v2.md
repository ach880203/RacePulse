# 🏇 RacePulse — 팀 회의 문서 v2

> **v1 아카이브**: `horse_racing_team.md` (1~3차 회의 전체 기록 + 상세 설계 논의)
> **노션 워크스페이스**: https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad
> **현재 Phase**: Phase 2 (2026-05-14 ~ 06-10)

---

## 🎯 프로젝트 개요

- **목표**: 경마 데이터 기반 순수 분석/예측 플랫폼 — 사행성 없음, 베팅 기능 없음
- **핵심 가치**: 예측 정확도 극대화 (Top-3 정확도 60% 미만 → 피처 재검토 / 70% → Phase 2 / **80% → 실운영 전환**)
- **설계 기준**: 포트폴리오가 아닌 **실운영 품질** — "세상에 없는 앱"

---

## 👥 역할 요약

| 역할 | 담당 | 기술스택 |
|------|------|---------|
| BE | 인증/유저/API 서버 | Spring Boot / Java 21 / JPA / PostgreSQL |
| FE | UI/시각화 | React 18 / TypeScript / Tailwind / Vite |
| ARCH | 아키텍처/DB/인프라 | PostgreSQL / Redis / Docker / AWS |
| ML | 예측모델/AI해설 | FastAPI / XGBoost / LightGBM / GPT-4o-mini |
| PM | 일정/우선순위 | — |
| DESIGN | UI/UX 디자인 | Figma |
| GIT | 브랜치/CI/CD | GitHub Actions |
| NOTION | 문서화 | Notion |
| WR | 회의 전사/기록 | — |

---

## 🏗️ 시스템 아키텍처 (✅ 확정)

```
[사용자 브라우저]
      ↕
[CloudFront CDN]
      ↕
[ALB]
      ↕
[React (Nginx)] ←→ [Spring Boot BE] ←→ [PostgreSQL]
                         ↕                    ↕
                   [FastAPI ML]          [Redis]
                         ↕
              [XGBoost/LightGBM / GPT-4o-mini]
                         ↕
              [한국마사회 API / 기상청 API]
```

- FE → Spring Boot 단일 창구 (FastAPI 직접 호출 없음)
- 데이터 수집 / 예측 / AI해설: FastAPI 전담
- 인증 / 유저 / 경주데이터: Spring Boot 전담

---

## 📅 마일스톤

| Phase | 목표 | 기간 | 완료 |
|-------|------|------|------|
| Phase 0 | 환경세팅 / DB / API 연동 | 1주 | ✅ 2026-05-13 |
| Phase 1 | 수집파이프라인 / BE뼈대 / FE라우팅 / 테스트 CI | 2주 | ✅ 2026-05-14 |
| **Phase 2** | **ML예측 / Monte Carlo / 시각화 대시보드** | **2주** | **2026-06-10** |
| Phase 3 | AI해설 고도화 / 정확도 개선 / Bayesian MC | 2주 | 2026-06-24 |
| Phase 4 | 문서화 / 부하테스트 / 배포 / 모니터링 | 1주 | 2026-07-01 |

---

## 📝 프롬프트 실행 현황 (총 20개 / 전체 완료 ✅)

| # | 프롬프트 | 담당 | 상태 |
|---|---------|------|------|
| 01 | intro-video | FE | ✅ 완료 |
| 02 | be-basic-api | BE | ✅ 완료 |
| 03 | pwa | FE | ✅ 완료 |
| 04 | home-page | FE | ✅ 완료 |
| 05 | kra-api | ML/ARCH | ✅ 완료 |
| 06 | weather-api | ML/ARCH | ✅ 완료 |
| 07 | kakao-oauth | BE | ✅ 완료 |
| 08 | apscheduler-redis | ML/ARCH | ✅ 완료 |
| 09 | web-push-vapid | BE | ✅ 완료 |
| 10 | fe-api-connect | FE | ✅ 완료 |
| 11 | detail-pages | FE | ✅ 완료 |
| 12 | ml-feature-engineering | ML | ✅ 완료 |
| 13 | ai-commentary | ML/BE | ✅ 완료 |
| 14 | dashboard | FE | ✅ 완료 |
| 15 | ml-model-training | ML | ✅ 완료 |
| 16 | prediction-page | FE | ✅ 완료 |
| 17 | dynamic-ui | FE | ✅ 완료 |
| 18 | monte-carlo | ML | ✅ 완료 |
| 19 | search-page | FE | ✅ 완료 |
| 20 | mypage | FE | ✅ 완료 |

---

## ✅ 핵심 확정사항 요약

### 기술 스택
- **DB**: PostgreSQL (Flyway V1~V6 / Phase 0~2 완료)
- **캐싱**: Redis (피처 스토어 당일 경주 100% 캐싱 + MC 결과)
- **ML 모델**: XGBoost + LightGBM / 피처 23개
- **AI 해설**: GPT-4o-mini / 금요일 사전 + 월요일 결과 / Redis 캐싱
- **배당률**: 마사회 API / `odds_history` 테이블

### 인증 / 보안
- JWT (Access 1h / Refresh 24h~3d) + Rotation + Family 감지
- 카카오 OAuth 2.0 병행 / BCrypt / Rate Limiting

### API
- 39개 엔드포인트 / `/api/v1/` 전체 적용
- 공통 응답: `ApiResponse<T>` / `PageResponse<T>`
- 에러: HTTP 상태코드 분리 (A방식) + 에러 페이지 3종 (404/401·403/500) + 토스트

### Monte Carlo (Phase 2)
- 기법: QMC(Sobol) + Antithetic Variates + Gaussian 상관행렬
- 횟수: Adaptive (10k~100k, CI ±0.5% 수렴 시 중단)
- 병렬처리: multiprocessing 4코어
- 추가: 게이트 브레이크 / 날씨 불확실성 / 스마트 머니 탐지 / 신뢰도 점수
- Counterfactual 인터랙티브 UI (Web Worker 필수)
- Phase 3: Bayesian 업데이트 / Sequential Race Dynamics / Copula / 앙상블

### 디자인
- 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 컬러: #07091A(배경) / #D4A843(골드) / 골드 글로우
- 폰트: Playfair Display(브랜드) + Inter(데이터) + JetBrains Mono(수치/CI)
- 애니메이션: duration-fast(150ms) ~ duration-hero(1200ms)
- 동적 UI: Phase 2 10종 / Phase 3 5종

### Git / 배포
- 브랜치: `feat/*` → develop(PR) → main(Phase PR + 버전태그)
- 커밋: 프롬프트 1개 = 커밋 1개 / `feat: [prompt-N] 설명`
- feat 브랜치: 논리적으로 묶이는 3~5개 프롬프트 = 브랜치 하나
- 배포: **매주 화요일 02:00~06:00 정기 점검일** (Blue-Green 폐기)
- 사전공지: 월요일 22:00 푸시 알림 + 오후 배너

### 실운영 대비
- 마사회 API 상업적 이용: 80% 달성 + 운영 결정 후 진행 (리스크 수용)
- OpenAI 비용: Freemium + 광고 수익화 (Phase 3~4 안건)
- 개인정보보호법 준수: Phase 2~3 (약관/처리방침/동의)

---

## 📋 액션 아이템

### ✅ 완료
- [x] **창현님**: ml-server Dockerfile 작성 ✅ 2026-05-15
- [x] **창현님**: ml-server requirements.txt / .dockerignore 작성 ✅ 2026-05-15
- [x] **창현님**: docker-compose.yml ml-server build 연결 ✅ 2026-05-15
- [x] **BE**: `ErrorCode.java` + `BusinessException.java` + `GlobalExceptionHandler.java` 구현 ✅ 2026-05-15
- [x] **BE**: 에러 페이지 3종 (404 / 401·403 / 500) + 토스트 구현 ✅ 2026-05-15
- [x] **ARCH**: `V6__phase2_ml_race_entries.sql` 생성 (11개 테이블) ✅ 2026-05-15
- [x] **ML**: Monte Carlo 고도화 (QMC/Sobol + Antithetic + Adaptive CI + 게이트편향 + Cholesky 상관행렬 + 날씨불확실성 + 스마트머니 + 신뢰도점수) ✅ 2026-05-18
- [x] **BE**: API 응답 `lastUpdated / dataStatus / nextUpdate` 필드 추가 (RaceResponse.java) ✅ 2026-05-18

### ✅ Phase 2 완료
- [x] ML: Monte Carlo 고도화 (QMC + Adaptive + 게이트편향 + 날씨 + 스마트머니 + 신뢰도) ✅ 2026-05-18
- [x] BE: API 응답 lastUpdated / dataStatus / nextUpdate 필드 추가 ✅ 2026-05-18
- [x] ARCH: 마사회 API 실데이터 테스트 (품질점수 97.6 GOOD / 전국 1년치 수집) ✅ 2026-05-18
- [x] ML: XGBoost v1.0 학습 (Top-1 83% / Top-3 89%) ✅ 2026-05-18
- [x] ML: LightGBM v1.0 학습 (Top-1 89% / Top-3 94%) ✅ 2026-05-18
- [x] ML: XGBoost + LightGBM 앙상블 예측 구현 ✅ 2026-05-18
- [x] ML: 라이벌 직접 대결 피처 (rival_records 396,937쌍 → 538,717쌍) ✅ 2026-05-18~19
- [x] ML: 주행 스타일 피처 (horse_running_style 6,892마리 → 8,726마리) ✅ 2026-05-18~19
- [x] ML: FEATURE_COLUMNS 23개 → 28개 확장 ✅ 2026-05-18
- [x] ML: **XGBoost v2.0 학습 (Top-1 89.85% / Top-3 99.85%)** ✅ 2026-05-19 (야간 자동 실행)
- [x] ML: **LightGBM v2.0 학습 (Top-1 94.18% / Top-3 99.4%)** ✅ 2026-05-19 (야간 자동 실행)
- [x] FE: Counterfactual 인터랙티브 UI (Web Worker 기반) ✅ 2026-05-18
- [x] FE: 동적 UI Phase 2 10종 (라이벌/스타일/MC 시각화) ✅ 2026-05-18
- [x] FE: 번들 최적화 14단계 (Brotli/ECharts/Lazy/SW캐싱 등) ✅ 2026-05-18
- [x] ARCH: 야간 자동화 파이프라인 구축 (Task Scheduler 03:00 수집 + 05:00 재학습) ✅ 2026-05-18

---

## 🗂️ 전체 남은 작업 우선순위 (Phase 2 ~ Phase 4)

### 🔴 P1 — 즉시 (ML 정확도 핵심 / 임팩트 큼 / 빠름)

| # | 작업 | 담당 | 근거 |
|---|------|------|------|
| 1 | **2024년 데이터 추가 수집** (bulk_collect.py START_MONTH=2024-01) | ML/ARCH | 2년치 재학습 시 2·3위 정확도 개선 직결 |
| 2 | **LightGBM 학습 + XGBoost 앙상블** (두 모델 평균 예측) | ML | POST /ml/train?model_type=lgbm → 앙상블 코드 추가 |
| 3 | **라이벌 직접 대결 피처** (rival_records 테이블 — 4차 회의 확정) | ML | A vs B 직접 전적 → feature_engineering.py 추가 |
| 4 | **주행 스타일 피처** (horse_running_style 테이블 — 4차 회의 확정) | ML | 선행/추입/중간 스타일 → feature_engineering.py 추가 |

### 🟡 P2 — Phase 2 완성 (FE 핵심 / 4차 회의 확정)

| # | 작업 | 담당 | 근거 |
|---|------|------|------|
| 5 | **Counterfactual 인터랙티브 UI** (Web Worker 필수 — 4차 회의 확정) | FE | Monte Carlo 고도화의 FE 연동 |
| 6 | **동적 UI Phase 2 10종** (4차 회의: Phase 2 추가 10종) | FE | 경주 시뮬레이션 미니 애니메이션 등 |
| 7 | **번들 최적화 14단계** (4차 회의 확정 — Brotli/WebM/ECharts/폰트서브셋/Lazy/WebWorker/가상화/SW캐싱/CI모니터링) | FE | 실운영 성능 기준 |

### 🟠 P3 — Phase 2~3 경계 (BE/DESIGN)

| # | 작업 | 담당 | 근거 |
|---|------|------|------|
| 8 | **GPT-4o-mini 프롬프트 초안** (금요일 사전 / 월요일 결과 — 1차 회의 확정) | BE | AI 해설 실제 생성에 필요 |
| 9 | **Figma 컬러 팔레트 + 디자인 토큰 초안** (2차 회의 확정) | DESIGN | FE 동적 UI 구현 선행 조건 |
| 10 | **개인정보보호법 준수 체계 설계** (약관/처리방침/동의 — Phase 2~3 안건) | BE | 실운영 전환 법적 요건 |
| 11 | **점검 모드 페이지 + 월요일 배너 + 푸시 알림** (화요일 정기 점검일 대비) | FE | 배포 운영 기반 |

### 🟢 P4 — Phase 3 (AI 해설 고도화 / Monte Carlo 심화)

| # | 작업 | 담당 | 근거 |
|---|------|------|------|
| 12 | **Bayesian MC 업데이트** (Sequential Race Dynamics / Copula / 앙상블 — 4차 회의 확정) | ML | Monte Carlo Phase 3 심화 |
| 13 | **AI 해설 고도화** (GPT 품질 검증 / 사행성 필터 강화) | ML/BE | 실운영 해설 품질 |
| 14 | **동적 UI Phase 3 5종** (4차 회의 확정) | FE | 완성도 향상 |
| 15 | **Freemium 수익화 모델 설계** (Phase 3~4 안건 — 4차 회의 이관) | PM | 실운영 전환 전 결정 |

### ⚪ P5 — Phase 4 (배포 / 문서화)

| # | 작업 | 담당 | 근거 |
|---|------|------|------|
| 16 | **AWS 배포** (EC2 3서버 + ALB + CloudFront — 4차 회의 확정) | ARCH | 화요일 02:00~06:00 정기 점검일 |
| 17 | **부하 테스트** (동시 사용자 100명, p95 500ms 목표) | ARCH | 실운영 품질 기준 |
| 18 | **README + 포트폴리오 문서화** | NOTION | Phase 4 산출물 |
| 19 | **마사회 API 상업적 이용 신청** (80% 달성 확인 후 진행 — 4차 회의 리스크 수용) | PM | 실운영 전환 법적 요건 |

### 🟢 낮음 (기존)
- [ ] **DESIGN**: Figma 컬러 팔레트 + 디자인 토큰 초안 업로드

---

## 💬 회의록

> 1~3차 회의 전체 기록 → `horse_racing_team.md` (v1 아카이브) 참조
> 1~3차 회의 요약 → 노션 워크스페이스 참조

---

### [날짜: 2026-05-14] 4차 회의 (Phase 2 킥오프)
- **참석**: BE, FE, ARCH, PM, DESIGN, GIT, NOTION, ML, WR, 창현님

#### 주요 결정 요약

| 안건 | 확정 내용 |
|------|----------|
| 프로젝트 방향 | 실운영 품질 기준 / "세상에 없는 앱" |
| Dockerfile | Phase 2 첫 태스크로 이관 |
| BE 예외처리 | HTTP A방식 + 에러 페이지 3종 + 토스트 |
| ml_feature_store | JSONB + 핵심 컬럼 + model_version_id + computation_status + error_message + GIN index |
| Phase 2 DB 10개 | avg_finish_position / top3_rate / avg_odds / meet_code 일관성 / shap_mean_abs / gate_break / rival 양방향 중복 방지 등 전면 보강 |
| Monte Carlo | QMC + Adaptive + 12가지 고도화 기법 / Phase별 배분 |
| 디자인 시스템 | Bloomberg × Premium / JetBrains Mono 추가 / 애니메이션 토큰 확정 |
| 동적 UI | Phase 2 10종 / Phase 3 5종 |
| 인트로 영상 | 영상2.mp4 = Veo 3.1 제작 최종 확정 |
| AWS 배포 | 3서버 + ALB + CloudFront / 화요일 정기 점검일 배포 |
| GIT | feat/* → develop PR → main Phase PR / 프롬프트 단위 커밋 |
| 번들 최적화 | 14단계 레이어드 전략 확정 |
| Freemium | Phase 3~4 안건으로 이관 |

---

### [날짜: 2026-05-15] 5차 작업 세션 (Phase 2 첫 번째 작업일)
- **참석**: 창현님

#### 완료 작업 목록

| 구분 | 작업 | 파일 경로 |
|------|------|---------|
| ML | ml-server Dockerfile A to Z 직접 작성 | `racepulse/ml-server/Dockerfile` |
| ML | requirements.txt 작성 (26개 패키지) | `racepulse/ml-server/requirements.txt` |
| ML | .dockerignore 작성 | `racepulse/ml-server/.dockerignore` |
| ARCH | docker-compose.yml ml-server build 연결 | `racepulse/docker-compose.yml` |
| BE | ErrorCode.java 직접 작성 (10개 에러 코드) | `global/exception/ErrorCode.java` |
| BE | BusinessException.java 직접 작성 | `global/exception/BusinessException.java` |
| BE | GlobalExceptionHandler.java 직접 작성 | `global/exception/GlobalExceptionHandler.java` |
| BE | ApiResponse.java error() 메서드 추가 | `global/response/ApiResponse.java` |
| FE | NotFoundPage.tsx (404) | `src/pages/error/NotFoundPage.tsx` |
| FE | UnauthorizedPage.tsx (401/403) | `src/pages/error/UnauthorizedPage.tsx` |
| FE | ServerErrorPage.tsx (500) | `src/pages/error/ServerErrorPage.tsx` |
| FE | Toast.tsx 컴포넌트 | `src/components/Toast.tsx` |
| FE | App.tsx 에러 라우트 등록 | `src/App.tsx` |
| ARCH | V6__phase2_ml_race_entries.sql (11개 테이블) | `db/migration/V6__phase2_ml_race_entries.sql` |

#### 특이사항
- 프롬프트 01~20 전체 실행 완료 확인
- Dockerfile은 창현님이 직접 A to Z 작성 (학습 목적)
- BE 예외처리 3종도 창현님이 직접 작성
- V6 명명 이유: V3가 이미 `create_push_tables`로 사용 중이었음

#### 커밋 내역
```
dockerfile, dockerignore, requirements 생성 및 추가작성
feat: BE 전역 예외처리 구현 (ErrorCode / BusinessException / GlobalExceptionHandler)
feat: FE 에러 페이지 3종 및 Toast 컴포넌트 추가
feat: V6 Phase 2 DB 마이그레이션 — ML 피처스토어 및 경주 출전 테이블 11개 추가
chore: docs 폴더 gitignore 추가
```

---

### [날짜: 2026-05-18] 6차 작업 세션 (Phase 2 두 번째 작업일)
- **참석**: 창현님

#### 완료 작업 목록

| 구분 | 작업 | 파일 경로 |
|------|------|---------|
| ML | Monte Carlo 고도화 — QMC(Sobol) + Antithetic Variates | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — Adaptive 수렴 (CI ±0.5%, 10k~100k) | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — Cholesky 게이트 상관행렬 | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — 게이트 브레이크 편향 | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — 날씨 불확실성 | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — 스마트머니 탐지 | `ml-server/app/services/monte_carlo.py` |
| ML | Monte Carlo 고도화 — 신뢰도 점수(0~100) | `ml-server/app/services/monte_carlo.py` |
| ML | 신규 테스트 5개 추가 | `ml-server/tests/test_monte_carlo.py` |
| BE | RaceResponse.java — lastUpdated / dataStatus / nextUpdate 필드 추가 | `domain/race/dto/RaceResponse.java` |

#### 특이사항
- Monte Carlo 테스트: 기존 16개 + 신규 5개 = **21개 통과** (4.04s)
  - 프롬프트 예상치(23개)와 다른 이유: 기존 파일에 테스트가 16개였음 (18개 아님)
- BE 컴파일: `./gradlew compileJava` → **BUILD SUCCESSFUL**
- ML 브랜치: `feat/phase2-ml-monte-carlo`
- BE 브랜치: `feat/phase2-be-api-fields`
- scipy fallback 구현: scipy 미설치 시 numpy로 자동 전환 (graceful degradation)
- odds_history 테이블 없을 때도 안전하게 동작 (`to_regclass`로 존재 여부 확인)

#### 커밋 내역
```
feat: [prompt-21] Monte Carlo 고도화 (QMC + Adaptive + 병렬처리 + 8종)
feat: [prompt-22] BE 경주 API 응답에 lastUpdated/dataStatus/nextUpdate 필드 추가
```

---

## 🔜 다음 회의 안건 (6차 회의)

| 우선순위 | 안건 | 담당 |
|----------|------|------|
| 🔴 | ARCH: 마사회 API 실데이터 테스트 결과 공유 | ARCH |
| 🔴 | ML 모델 정확도 측정 결과 공유 (60%/70% 기준 판단) | ML |
| 🟡 | Phase 2 동적 UI 10종 진행 현황 | FE |
| 🟡 | Monte Carlo 고도화 진행 현황 | ML |
| 🟡 | 번들 최적화 착수 여부 | FE |
| 🟡 | 개인정보보호법 준수 체계 설계 | BE + DESIGN |
| 🟢 | Freemium 수익화 모델 세부 설계 | PM |

---

### [날짜: 2026-05-19] 10차 작업 세션 (Phase 2 미착수 항목 + 코드 리뷰)
- **참석**: 창현님

#### 야간 자동화 결과 (2026-05-18 → 05-19 새벽)

| 모델 | v1.0 | v2.0 | 향상 |
|------|------|------|------|
| XGBoost Top-1 | 83.01% | **89.85%** | +6.84%p |
| XGBoost Top-3 | 89.07% | **99.85%** | +10.78%p |
| LightGBM Top-1 | 89.25% | **94.18%** | +4.93%p |
| LightGBM Top-3 | 94.03% | **99.4%** | +5.37%p |

→ 라이벌 직접 대결 피처 + 주행 스타일 피처 효과로 정확도 대폭 향상

#### 완료 작업

| 구분 | 작업 | 결과 |
|------|------|------|
| GIT | PR #6 develop 머지 | feat/phase2-fe-prompts-23-25 |
| FE | npm install + build 검증 | ✅ 빌드 성공 |
| DESIGN | design-tokens.css 생성 | Figma 동기화용 전체 토큰 코드화 |
| BE | Codex 프롬프트 26 작성 | GPT-4o-mini AI 해설 시스템 |
| FE | Codex 프롬프트 27 작성 | 점검 모드 + 월요일 배너 + 푸시 알림 |
| GIT | feat/phase2-remaining 브랜치 push | 오늘 작업 일괄 커밋 |

#### Codex 코드 리뷰 결과 (2026-05-19) — 수정 필요 항목

| 우선순위 | 구분 | 이슈 | 영향 |
|---------|------|------|------|
| 🔴 높음 | BE | `/races/{id}`, `/races/{id}/entries`, `/races/{id}/result` 엔드포인트 없음 | 경주 상세/출전/결과 화면 404 오류 |
| 🔴 높음 | BE/FE | `RaceResponse` DTO에 `trackType`, `prize`, `weather`, `raceClass` 필드 누락 | 상세 화면 데이터 오표시 |
| 🔴 높음 | FE | 401 refresh 인터셉터 무한 대기 버그 (`axiosInstance.ts:116`) | 로그인 후 화면 무한 로딩 가능 |
| 🟡 중간 | FE | 번들 796KB 초과 (`App.tsx` 정적 import 문제) | 초기 로딩 느림 |
| 🟡 중간 | FE | `localhost:8080`, `localhost:8000` 하드코딩 | 배포 환경 깨짐 |
| 🟡 중간 | BE | `DashboardService.java:71` null 언박싱 NPE | `/dashboard/accuracy` 500 에러 가능 |
| 🟡 중간 | DB | V10 마이그레이션 중복 constraint 위험 | 마이그레이션 실패 가능 |
| 🟡 중간 | BE | `application-dev.yaml` 민감 키 기본값 노출 | 보안 위험 |
| 🟢 낮음 | ML | pytest-asyncio 경고 | 향후 버전 호환성 |

→ **prompt-28** 으로 묶어서 Codex 수정 예정

#### 빌드/테스트 현황

| 서버 | 결과 |
|------|------|
| BE `./gradlew test` | ✅ 성공 |
| FE `npm run build` | ✅ 성공 (번들 경고 있음 — 796KB) |
| FE `npm test` | ✅ 9개 통과 |
| ML `pytest` | ✅ 46개 통과 (asyncio 경고 1건) |

#### 데이터 수집 현황 (2026-05-19 기준)

- 결과 수집 완료: **1,491 날짜** (2021-04-10 ~ 2026-05-17)
- 고유 말 수: **10,560마리**
- v3.0 재학습 준비 완료

#### 특이사항
- Phase 2 핵심 기술 목표 **전부 완료**
- Phase 2 공식 완료 선언 조건: DESIGN Figma 업로드 + Codex 프롬프트 26·27 완료
- v2.md → v3.md 전환은 Phase 2 완료 공식 선언 후 진행
- 채팅창 용량 초과로 새 세션에서 이어서 진행

---

## 📌 새 세션 인수인계 체크리스트

새 채팅을 열 때 반드시 이 파일(`horse_racing_team_v2.md`)과 `horse_racing_team.md`를 읽고 시작할 것.

### 당장 해야 할 것 (우선순위 순)
1. **Codex 실행**: prompt-26 (AI 해설) + prompt-27 (점검 모드) 동시 실행
2. **Codex 프롬프트 28 작성 + 실행**: 코드 리뷰 높음/중간 이슈 수정
3. **Figma**: 창현님이 파일 URL 주시면 MCP로 디자인 토큰 생성
4. **v3.0 재학습**: `POST /ml/train?start_date=2021-04-10&version=v3.0` × 2

### 현재 브랜치 상태
- `develop` ← PR #4·#5·#6 머지 완료
- `feat/phase2-remaining` — prompt 26·27 + 디자인 토큰 (PR 미생성)

### 실행 중인 자동화
- Task Scheduler 03:00: 데이터 수집 (`RacePulse_BulkCollect`)
- Task Scheduler 05:00: ML 파이프라인 (`RacePulse_NightlyPipeline`)
- 로그: `racepulse/ml-server/scripts/nightly_log.txt`
