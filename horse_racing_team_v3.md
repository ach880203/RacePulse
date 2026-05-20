# 🏇 RacePulse — 팀 회의 문서 v3

> **v1 아카이브**: `horse_racing_team.md` (킥오프~3차 회의 전체 기록)
> **v2 아카이브**: `horse_racing_team_v2.md` (Phase 2 전체 기록)
> **노션 워크스페이스**: https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad
> **현재 Phase**: Phase 3 (2026-06-10 ~ 06-24)

---

## 🎯 프로젝트 개요

- **목표**: 경마 데이터 기반 순수 분석/예측 플랫폼 — 사행성 없음, 베팅 기능 없음
- **핵심 가치**: 예측 정확도 극대화
- **설계 기준**: 포트폴리오가 아닌 **실운영 품질** — "세상에 없는 앱"
- **정확도 기준**: Top-3 60% 미만 → 피처 재검토 / 70% → Phase 2 진행 / **80% → 실운영 전환**
  - ✅ Phase 2 달성: XGBoost v2.0 Top-3 **99.85%** / LightGBM v2.0 Top-3 **99.4%**

### 절대 하지 않는 것
- ❌ 베팅 기능 (직접 / 시뮬레이션 모두 없음)
- ❌ 포인트, 가상화폐, 랭킹 경쟁
- ❌ "이 말에 걸어라" 식의 직접적 투자 조언 뉘앙스

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
| Phase 2 | ML예측 / Monte Carlo / 시각화 대시보드 | 2주 | ✅ 2026-05-19 |
| **Phase 3** | **AI해설 고도화 / 정확도 개선 / Bayesian MC** | **2주** | **2026-06-24** |
| Phase 4 | 문서화 / 부하테스트 / 배포 / 모니터링 | 1주 | 2026-07-01 |

---

## 📝 프롬프트 실행 현황 (총 28개 완료 / Phase 2 종료)

| # | 프롬프트 | 담당 | 상태 |
|---|---------|------|------|
| 01 | intro-video | FE | ✅ |
| 02 | be-basic-api | BE | ✅ |
| 03 | pwa | FE | ✅ |
| 04 | home-page | FE | ✅ |
| 05 | kra-api | ML/ARCH | ✅ |
| 06 | weather-api | ML/ARCH | ✅ |
| 07 | kakao-oauth | BE | ✅ |
| 08 | apscheduler-redis | ML/ARCH | ✅ |
| 09 | web-push-vapid | BE | ✅ |
| 10 | fe-api-connect | FE | ✅ |
| 11 | detail-pages | FE | ✅ |
| 12 | ml-feature-engineering | ML | ✅ |
| 13 | ai-commentary | ML/BE | ✅ |
| 14 | dashboard | FE | ✅ |
| 15 | ml-model-training | ML | ✅ |
| 16 | prediction-page | FE | ✅ |
| 17 | dynamic-ui | FE | ✅ |
| 18 | monte-carlo | ML | ✅ |
| 19 | search-page | FE | ✅ |
| 20 | mypage | FE | ✅ |
| 21 | monte-carlo-advanced | ML | ✅ |
| 22 | be-race-api-fields | BE | ✅ |
| 23 | counterfactual-ui | FE | ✅ |
| 24 | dynamic-ui-phase2 | FE | ✅ |
| 25 | bundle-optimization | FE | ✅ |
| 26 | gpt-commentary | BE/ML | ✅ |
| 27 | maintenance-mode | FE/BE | ✅ |
| 28 | code-review-fixes | 전체 | ✅ |

---

## ✅ 핵심 확정사항 (v1·v2 계승)

### 기술 스택
- **DB**: PostgreSQL (Flyway V1~V12 / Phase 0~2 완료 / 43개 테이블)
- **캐싱**: Redis (피처 스토어 당일 경주 100% 캐싱 + MC 결과 + AI 해설)
- **ML 모델**: XGBoost + LightGBM 앙상블 / 피처 28개
- **AI 해설**: GPT-4o-mini / 금요일 사전 + 월요일 결과 / Redis 캐싱
- **배당률**: 마사회 API / `odds_history` 테이블

### 인증 / 보안
- JWT (Access 1h / Refresh 24h~3d) + Rotation + Family 감지
- 카카오 OAuth 2.0 병행 / BCrypt(strength 10) / Rate Limiting (5회 실패 → 15분 잠금)
- Cookie: HttpOnly + Secure + SameSite=Strict
- dev 프로파일: Secure=false / prod 프로파일: Secure=true

### API
- 39개 엔드포인트 / `/api/v1/` 전체 적용
- 공통 응답: `ApiResponse<T>` / `PageResponse<T>`
- 에러: HTTP 상태코드 분리 (A방식) + 에러 페이지 3종 (404/401·403/500) + 토스트
- 경주 API 공통 필드: `lastUpdated` / `dataStatus` / `nextUpdate`

### Monte Carlo (Phase 2 완료 / Phase 3 고도화 예정)
- Phase 2: QMC(Sobol) + Antithetic Variates + Gaussian 상관행렬
- Phase 2: Adaptive (10k~100k, CI ±0.5% 수렴 시 중단) / 병렬처리 4코어
- Phase 2: 게이트 브레이크 / 날씨 불확실성 / 스마트 머니 탐지 / 신뢰도 점수
- **Phase 3 예정**: Bayesian 업데이트 / Sequential Race Dynamics / Copula / 앙상블

### 디자인 시스템 (✅ Figma 동기화 완료)
- 철학: "Bloomberg Terminal × Premium Sports Analytics"
- 컬러: `#07091A`(배경) / `#D4A843`(골드) / 골드 글로우
- 폰트: Playfair Display(브랜드) + Inter(데이터) + JetBrains Mono(수치/CI)
- Figma 파일: https://www.figma.com/design/CmPgsCrp7e5uWrucHtilue (RacePulse Design System)
- Variables: 컬러×16 / 스페이싱×8 / 반경×5 / Duration×4
- Text Styles: Text×8 / Mono×3
- 애니메이션: duration-fast(150ms) ~ duration-hero(1200ms)
- 동적 UI: Phase 1 6종 + Phase 2 10종 완료 / Phase 3 5종 예정

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
- 지수 백오프 재시도 5회 (5분→15분→30분→1시간→3시간)
- **야간 자동화**: Task Scheduler 03:00 수집 + 05:00 ML 파이프라인

### Git / 배포 규칙
- **브랜치**: `feat/*` → develop(PR, Create a merge commit) → main(Phase PR + 버전태그, Squash merge)
- **커밋**: 프롬프트 1개 = 커밋 1개 / `feat: [prompt-N] 설명`
- **feat 브랜치**: 논리적으로 묶이는 3~5개 프롬프트 = 브랜치 하나
- **커밋 컨벤션**: `feat` / `fix` / `docs` / `style` / `refactor` / `test` / `chore`
- **배포**: 매주 화요일 02:00~06:00 정기 점검일
- **사전공지**: 월요일 22:00 푸시 알림 + 오후 배너 (MaintenanceBanner / MaintenancePushScheduler 구현 완료)

### AI 해설 규칙 (사행성 방지)
- 절대 금지: "베팅 추천", "이 말에 투자", "확실한 1위"
- 필수 포함: "데이터 기준", "통계적으로", "참고용 분석"
- 하단 고정 면책 문구: "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."
- 사전 해설: 금요일 08:00 자동 생성 (600~1000자)
- 결과 해설: 월요일 14:00 자동 생성 (800~1200자)

### 외부 API
| API | 용도 | 키 |
|-----|------|----|
| 한국마사회 API | 경주 데이터 수집 | `KMA_API_KEY` |
| 기상청 API | 날씨 예보 | `WEATHER_API_KEY` |
| 카카오 OAuth 2.0 | 소셜 로그인 | `KAKAO_CLIENT_ID / SECRET` |
| OpenAI GPT API | AI 해설 (GPT-4o-mini) | `OPENAI_API_KEY` |
| 포트원 (PortOne) | 결제 — Freemium 도입 시 연동 | 도입 시 추가 |

### 실운영 대비
- 마사회 API 상업적 이용: 80% 달성 + 운영 결정 후 진행 (리스크 수용)
- OpenAI 비용: Freemium + 광고 수익화 (Phase 3~4 안건)
- 개인정보보호법 준수: Phase 2~3 (약관/처리방침/동의) — **Phase 3 필수**
- 결제: 포트원 (KakaoPay → 포트원 확정)

---

## 🗄️ DB 현황 (Flyway V1~V12 / 총 43개 테이블)

| Flyway | Phase | 내용 |
|--------|-------|------|
| V1 | Phase 0 | 15개 핵심 테이블 (말/기수/조교사/경주/출전/결과 등) |
| V2 | Phase 1 | 12개 서비스 테이블 (예측/AI해설/즐겨찾기/알림 등) |
| V3 | Phase 1 | push_subscriptions 관련 |
| V4 | Phase 1 | Phase 3 테이블 5개 |
| V5 | Phase 1 | user_profile 테이블 |
| V6 | Phase 2 | ML 피처스토어 및 경주 출전 테이블 11개 |
| V7 | Phase 2 | FastAPI 모델 정렬 스키마 수정 |
| V8 | Phase 2 | 마스터 테이블 컬럼 수정 |
| V9 | Phase 2 | ML 테이블 스키마 전면 정렬 |
| V10 | Phase 2 | race_results margin 타입 수정 |
| V11 | Phase 2 | races ENUM 컬럼 복원 |
| V12 | Phase 2 | rival_records + horse_running_style 테이블 추가 |

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

- v2.0 향상 원인: 라이벌 직접 대결 피처(rival_records 538,717쌍) + 주행 스타일 피처(8,726마리)
- v3.0 학습 데이터: 훈련 103,725건 / 테스트 25,931건 (2021-04-10 기준)
- v3.0 특이사항: Top-1 소폭 하락, Top-3 유지 — 데이터셋 재분할 영향으로 추정
- **Phase 3 예정**: Bayesian MC 고도화 후 v3.1 재학습 검토

---

## 🔜 Phase 3 작업 목록

### 🔴 P1 — 즉시 (ML 핵심)

| # | 작업 | 담당 |
|---|------|------|
| 1 | **v3.0 재학습** `POST /ml/train?start_date=2021-04-10&version=v3.0` × 2 | ML |
| 2 | **Bayesian MC 업데이트** (Sequential Race Dynamics / Copula / 앙상블) | ML |
| 3 | **AI 해설 고도화** (GPT 품질 검증 / 사행성 필터 강화) | ML/BE |

### 🟡 P2 — Phase 3 완성 (법적/운영)

| # | 작업 | 담당 |
|---|------|------|
| 4 | **개인정보보호법 준수 체계 설계** (약관/처리방침/동의) | BE |
| 5 | **동적 UI Phase 3 5종** | FE |
| 6 | **Freemium 수익화 모델 세부 설계** | PM |

### 🟠 P3 — Phase 4 준비

| # | 작업 | 담당 |
|---|------|------|
| 7 | **AWS 배포** (EC2 3서버 + ALB + CloudFront) | ARCH |
| 8 | **부하 테스트** (동시 사용자 100명, p95 500ms 목표) | ARCH |
| 9 | **README + 포트폴리오 문서화** | NOTION |
| 10 | **마사회 API 상업적 이용 신청** | PM |

---

## 🔌 BE API 엔드포인트 (39개 확정)

| # | 분류 | 메서드 | 엔드포인트 | 권한 |
|---|------|--------|-----------|------|
| 1~5 | 인증 | POST/GET | /auth/register, /login, /logout, /me, /refresh | GUEST/USER |
| 6~7 | 카카오 | GET | /auth/kakao, /auth/kakao/callback | GUEST |
| 8~12 | 경주 | GET | /races, /races/{id}, /races/{id}/full, /races/upcoming, /races/results | GUEST |
| 13~15 | 경주마 | GET | /horses, /horses/{id}, /horses/{id}/history | GUEST |
| 16~17 | 기수/조교사 | GET | /jockeys/{id}, /trainers/{id} | GUEST |
| 18~20 | 예측/AI해설 | GET | /predictions/{raceId}, /commentary/{raceId}/pre, /commentary/{raceId}/post | GUEST |
| 21~23 | 경마장/날씨 | GET | /racecourses, /racecourses/{meetCode}, /weather/{meetCode}/{date} | GUEST |
| 24~25 | 검색/홈 | GET | /search, /home | GUEST |
| 26~27 | 대시보드 | GET | /dashboard/accuracy, /dashboard/weekly | GUEST |
| 28~34 | 유저 | GET/POST/DELETE/PATCH | /user/favorites, /user/history, /user/preferences, /user/notifications | USER |
| 35~38 | 관리자 | GET/POST | /admin/collection/**, /admin/model/accuracy, /admin/commentary/regenerate | ADMIN |
| 39 | 헬스체크 | GET | /health | GUEST |

---

## 💬 회의록

> 킥오프~3차 회의 전체 기록 → `horse_racing_team.md` (v1 아카이브)
> Phase 2 전체 기록 → `horse_racing_team_v2.md` (v2 아카이브)
> 요약 → 노션 워크스페이스 참조

---

### [날짜: 2026-05-15] Phase 2 완료 선언

#### 완료 조건 충족 내역
| 조건 | 상태 |
|------|------|
| ML Top-3 정확도 80% 이상 | ✅ XGBoost 99.85% / LightGBM 99.4% |
| Monte Carlo QMC 고도화 | ✅ 12종 기법 적용 |
| FE 동적 UI Phase 2 10종 | ✅ 완료 |
| FE Counterfactual 인터랙티브 UI | ✅ Web Worker 기반 |
| 번들 최적화 14단계 | ✅ 완료 |
| Figma 디자인 토큰 동기화 | ✅ 2026-05-15 완료 |
| develop → main Phase PR | ✅ PR #8 Squash merge |
| v2.0.0 태그 | ✅ 2026-05-15 push |

---

## 📌 새 세션 인수인계 체크리스트

새 채팅을 열 때 반드시 이 파일(`horse_racing_team_v3.md`)을 읽고 시작할 것.
(v1·v2는 필요 시 참조)

### 당장 해야 할 것 (우선순위 순)
1. ~~**v3.0 재학습**~~ ✅ 2026-05-15 완료 (XGBoost Top-3 98.85% / LightGBM Top-3 99.05%)
2. **Bayesian MC 고도화**: Sequential Race Dynamics / Copula / 앙상블 (Phase 3 핵심)
3. **AI 해설 고도화**: GPT 품질 검증 / 사행성 필터 강화
4. **개인정보보호법 준수**: 약관/처리방침/동의 체계 (실운영 법적 필수)
5. **동적 UI Phase 3 5종**: FE 완성도
6. **Freemium 모델 결정**: Phase 3~4 안건

### 현재 브랜치 상태
- `main` ← PR #8 Squash merge 완료 / 태그 `v2.0.0`
- `develop` ← main과 동기화 완료
- Phase 3 작업 시작 시 `feat/phase3-*` 브랜치 생성할 것

### 실행 중인 자동화
- Task Scheduler 03:00: 데이터 수집 (`RacePulse_BulkCollect`)
- Task Scheduler 05:00: ML 파이프라인 (`RacePulse_NightlyPipeline`)
- 로그: `racepulse/ml-server/scripts/nightly_log.txt`
