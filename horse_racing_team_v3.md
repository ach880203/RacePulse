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

### [날짜: 2026-05-15] 13차 작업 세션 (Phase 3 착수)
- **참석**: 창현님

#### 완료 작업

| 구분 | 작업 | 결과 |
|------|------|------|
| ML | XGBoost v3.0 재학습 | Top-1 85.31% / Top-3 **98.85%** |
| ML | LightGBM v3.0 재학습 | Top-1 91.86% / Top-3 **99.05%** |
| WR | horse_racing_team_v3.md 생성 | v1·v2 규칙 전체 계승 |
| NOTION | 노션 워크스페이스 전면 업데이트 | 메인/회의록/스프린트/디자인 4페이지 |

#### 특이사항
- v3.0 Top-1이 v2.0 대비 소폭 하락 — 데이터셋 재분할 영향 추정, Top-3는 유지
- Bayesian 피처 적용 후 v3.1 재학습 검토 예정

#### 커밋 내역
```
docs: Phase 3 시작 — horse_racing_team_v3.md 생성 (v1·v2 규칙 계승 + Phase 2 완료 선언)
docs: v3.0 재학습 결과 기록 (XGBoost Top-3 98.85% / LightGBM Top-3 99.05%)
```

---

### [날짜: 2026-05-15] 12차 작업 세션 (Phase 2 완료 선언)
- **참석**: 창현님

#### 완료 작업

| 구분 | 작업 | 결과 |
|------|------|------|
| DESIGN | Figma 디자인 토큰 동기화 | RacePulse Design System 파일 생성 |
| DESIGN | Variables 33개 업로드 | Color×16 / Spacing×8 / Radius×5 / Duration×4 |
| DESIGN | Text Styles 11개 업로드 | Text×8 (Inter) / Mono×3 (JetBrains Mono) |
| GIT | v2.0.0 태그 push | origin에 push 완료 |
| GIT | develop 최신화 | PR #7·#8 반영 확인 |

#### Phase 2 완료 조건 충족

| 조건 | 상태 |
|------|------|
| ML Top-3 80% 이상 | ✅ XGBoost 99.85% / LightGBM 99.4% |
| Figma 디자인 토큰 동기화 | ✅ 2026-05-15 완료 |
| develop → main Phase PR | ✅ PR #8 Squash merge |
| v2.0.0 태그 | ✅ push 완료 |

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

---

### [날짜: 2026-05-15] 14차 회의 — Phase 3 킥오프
- **참석**: BE, FE, ARCH, ML, PM, DESIGN, GIT, NOTION, WR, 창현님 — 전원

#### ✅ Q1 — 사행성 팝업 확정

| 항목 | 확정 내용 |
|------|----------|
| GPT 프레이밍 | "스포츠 중계 해설위원" 관점 + Few-shot 예시 + Chain-of-Thought 4단계 |
| 금지어 추가 | "다크호스" 추가 / "이변 가능성이 큽니다" 허용 |
| 승률 UI | 골드 유지 / 크기 아닌 투명도로 차별화 |
| 팝업 방식 | 별도 팝업 / 스크롤 완료 → 확인함 버튼 → 동의하기 / localStorage 저장 |
| 재방문 | 팝업 항상 표시 / 동의한 유저는 "동의하였음 + 날짜" + 닫기만 |
| 면책 | 해설 하단 고정 + 첫 접속 팝업 별도 분리 |
| 사행성 필터 | GPT 시스템 프롬프트 1차 + BE 키워드 스캔 2차 / retry 2회 / fallback 템플릿 |
| 기수변경 재생성 | 기수변경 감지 시 해설 캐시 무효화 + 자동 재생성 트리거 |
| 품질 점수 | 0~100점 / HIGH(80+)/MED(50~79)/LOW(-50) / 연속 LOW 3회 시 관리자 알림 |

#### ✅ Q2 — 변경사항 감지 체계 전체 확정

**감지 5종 전부 구현:**

| 변경 종류 | 뱃지 | 영향도 | 구현 |
|-----------|------|--------|------|
| 기수변경 | 🔴 빨강 | 매우 큼 | ✅ 기존 |
| 출전 취소 | ⚫ 회색 | 매우 큼 | 신규 |
| 조교사 변경 | 🟠 주황 | 중간 | 신규 |
| 장비변경 (블링커 등) | 🟡 노랑 | 중간 | 신규 |
| 트랙 상태 급변 | 🔵 파랑 | 중간 | 신규 |

**DB 신설 (V13 포함):** `trainer_changes` + `equipment_changes` + `previous_change_id` FK (A→B→A 체인 처리)

**ML 피처 추가:** `blinker_first_time` / `blinker_removed` / `trainer_changed_days` / `new_jockey_horse_combination` / `new_jockey_first_ride_winrate` / `trainer_change_recovery_race` / 날씨+트랙 복합 영향도

**전체 아이디어 확정 (A~Y + 추가):**
- Bayesian prior 자동 조정 / 신뢰도 자동 하향 / 이변 확률 상향 / MC 자동 재시뮬레이션
- Redis 캐시 + Pub/Sub 병렬 처리 / 주기 단축 (30분 간격)
- UI 별표(★) + 오늘의 변동사항 카드 + 타임라인 + 비교 툴팁 + 알림 센터 벨 아이콘
- 즐겨찾기 연동 푸시 / 알림 구독 설정 UI / 카카오 공유 / SSE 실시간 업데이트
- 홈 경보 배너 / 경주 목록 필터 / 히트맵 / 정렬 옵션
- GET /races/{id}/changes 엔드포인트 / Webhook / 수동 트리거 / 이메일 fallback
- 변경 빈도 ↔ 예측 정확도 상관 분석 / 케이스 스터디 / 경마장별 패턴
- E2E 테스트 + Feature Flag + 플러그인 구조 모듈화

#### ✅ Q3 — AI 해설 모델 확정

| 해설 종류 | 모델 | Temperature |
|---------|------|------------|
| 사전 해설 (금요일) | GPT-4.1 | 0.7 |
| 결과 해설 (월요일) | GPT-4.1-mini | 0.3 |
| 실운영 수익 후 | GPT-5 전체 전환 검토 | — |

추가 품질 향상: Structured Output (JSON 섹션 강제) + Chain-of-Thought + Few-shot

#### ✅ 안건 4-1 — 동적 UI Phase 3 확정

| # | UI 요소 | 비고 |
|---|---------|------|
| 27 | Bayesian 확률 업데이트 애니메이션 | 사전→사후 카운트업 |
| 28 | Sequential Race 실시간 컨디션 갱신 바 | 앞 경주 결과 반영 |
| 29 | AI 해설 품질 뱃지 | HIGH/MED/LOW + 모델명 |
| 30 | 사행성 팝업 스크롤 진행 바 | 골드 프로그레스 바 |
| 31 | 변경사항 복합 신뢰도 게이지 | 변경 건수별 실시간 하락 |
| 32 | **말 Stat 카드** | **Option 1+3 합체 (FIFA 카드 + 수치 게이지)** |

추가: 물결 컨디션 히스토리 / 말 카드 플립 / 배당률 라이브 차트 / 게이트 열림 전환 / 말 1:1 비교 / 드래그&드롭 순위 예측 / 소셜 예측 분포 / SHAP 피처 중요도 / 컨디션 최적조건 매칭 / 등급 오라 효과 / AI 해설 문장 단위 타이핑

#### ✅ 안건 4-2 — Freemium 확정

| 구분 | FREE | PREMIUM |
|------|------|---------|
| 예측 | 상위 4마리 / Top-3 확률만 | 전체 / Top-1 / 신뢰도 |
| 말 Stat | 속도 1개만 | 8개 전체 |
| 변경사항 | "변경됨" 알림만 | 상세 전체 |
| Counterfactual | 하루 3회 | 무제한 |
| AI 해설 | 요약 300자 | 전문 1000자 + Q&A |
| 광고 | 시청으로 잠금 해제 | 광고 없음 |
| 체험 | **가입 후 7일 전체 무료** | — |

**광고 유혹 강화:** 일일 무료 열람권 3회 / blur(4px) 흐릿 미리보기 / 친구 초대 3일 연장 / 주간 예측 챌린지 PREMIUM 1주일 / 히스토리 무제한 / SHAP 설명 / 앙상블 불일치 공개 / AI Q&A / 역대 대결 풀 데이터

#### ✅ 미니게임 — 방향 확정

**게임 1: 다마고치 "나의 경주마"**
- 실제 경주마 선택 → 밥주기 / 훈련 / 일일 케어
- 실제 경주 결과가 말 컨디션에 자동 반영
- 연속 좋은 성적 → 레벨업 / 카드 등급 상승
- 출석 체크 + 퀴즈로 코인 획득 → 아이템 상점에서 사료/훈련/외형 구입

**게임 2: 무한 퀴즈 "경마 마스터"**
- 실제 DB 데이터 기반 문제 자동 생성
- 연속 정답 → 분석가 등급 상승

**보상 체계:**
| 보상 | 조건 | 수량 |
|------|------|------|
| 광고 스킵권 | 토너먼트 1위 | +5장 |
| 광고 스킵권 | 토너먼트 2~3위 | +3장 |
| 광고 스킵권 | 연속 출석 7일 | +3장 |
| 광고 스킵권 | 퀴즈 10연속 정답 | +2장 |
| 광고 스킵권 | 일일 출석 | +1장 |
| **최대 보유** | **상한선** | **15장** |

- 법적 안전: 광고 스킵권 = 현금 가치 없는 앱 내 편의 아이템
- 개발 시점: Phase 4 (다마고치 + 퀴즈 기본) / Phase 5 (토너먼트 + 상점)

---

## 📌 새 세션 인수인계 체크리스트

새 채팅을 열 때 반드시 이 파일(`horse_racing_team_v3.md`)을 읽고 시작할 것.
(v1·v2는 필요 시 참조)

### 당장 해야 할 것 (우선순위 순)
1. ~~**v3.0 재학습**~~ ✅ 2026-05-15 완료 (XGBoost Top-3 98.85% / LightGBM Top-3 99.05%)
2. **Bayesian MC 고도화**: Bayesian → Sequential → Copula 순 (Phase 3 핵심)
3. **AI 해설 고도화**: GPT-4.1 전환 + 사행성 이중 필터 + 품질 점수
4. **개인정보보호법**: `/privacy` + `/terms` + 회원가입 동의 + V13 마이그레이션
5. **변경사항 감지 5종**: DB 신설 + 피처 추가 + UI + 푸시 알림
6. **동적 UI Phase 3**: 27~32번 + 추가 아이디어
7. **Freemium 뼈대**: PREMIUM 게이트 Spring Security 구현 (결제는 Phase 4)
8. **미니게임**: Phase 4 착수 전 설계 문서 작성

### 현재 브랜치 상태
- `main` ← PR #8 Squash merge 완료 / 태그 `v2.0.0`
- `develop` ← 최신화 완료
- Phase 3 브랜치: `feat/phase3-ml-bayesian` / `feat/phase3-be-privacy` / `feat/phase3-fe-dynamic-ui`

### 실행 중인 자동화
- Task Scheduler 03:00: 데이터 수집 (`RacePulse_BulkCollect`)
- Task Scheduler 05:00: ML 파이프라인 (`RacePulse_NightlyPipeline`)
- 로그: `racepulse/ml-server/scripts/nightly_log.txt`
