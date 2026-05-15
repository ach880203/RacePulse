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

## ✅ 핵심 확정사항 요약

### 기술 스택
- **DB**: PostgreSQL 43개 테이블 (Phase 0~3 / Flyway V1~V4)
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

## 📋 미완료 액션 아이템

### 🔴 즉시 처리
- [ ] **창현님**: ml-server Dockerfile 작성 (Phase 2 첫 번째 태스크 / 마사회 실테스트 전제)
- [ ] **BE**: `ErrorCode.java` + `BusinessException.java` + `GlobalExceptionHandler.java` 구현
- [ ] **BE**: 에러 페이지 3종 (404 / 401·403 / 500) + 토스트 구현

### 🟡 Phase 2 진행 중
- [ ] **ARCH**: `V3__phase2.sql` 생성 (11개 테이블 전면 재설계 구조 반영)
- [ ] **ARCH**: 마사회 API 실데이터 테스트 (Dockerfile 완료 후 / 결측값·구버전 포맷)
- [ ] **ML**: 모델 정확도 측정 (실데이터 수집 후 / Top-3 기준 판단)
- [ ] **ML**: Monte Carlo 고도화 (QMC + Adaptive + 병렬처리 + 상관행렬 + 게이트브레이크 + 날씨불확실성 + 스마트머니 + 신뢰도점수)
- [ ] **FE**: Counterfactual 인터랙티브 UI (Web Worker 기반)
- [ ] **FE**: 동적 UI Phase 2 10종 구현
- [ ] **FE**: 번들 최적화 14단계 (Brotli / WebM / ECharts / 폰트서브셋 / Lazy / WebWorker / 가상화 / SW캐싱 / CI모니터링 등)
- [ ] **BE**: API 응답 `last_updated / data_status / next_update` 필드 추가

### 🟢 낮음
- [ ] **BE**: GPT-4o-mini 프롬프트 초안 (금요일용 / 월요일용)
- [ ] **DESIGN**: Figma 컬러 팔레트 + 디자인 토큰 초안 업로드
- [ ] **BE**: 개인정보보호법 준수 체계 설계 (약관 / 처리방침 / 동의)
- [ ] **FE**: 점검 모드 페이지 + 월요일 배너 + 푸시 알림

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

## 🔜 다음 회의 안건 (5차 회의)

| 우선순위 | 안건 | 담당 |
|----------|------|------|
| 🔴 | Dockerfile 완료 확인 → 실데이터 수집 시작 | 창현님 + ARCH |
| 🔴 | ML 모델 정확도 측정 결과 공유 (60%/70% 기준 판단) | ML |
| 🔴 | BE 예외처리 구현 완료 확인 | BE |
| 🟡 | V3__phase2.sql 생성 완료 확인 | ARCH |
| 🟡 | Phase 2 프롬프트 진행 현황 점검 | 팀 전체 |
| 🟡 | 개인정보보호법 준수 체계 설계 | BE + DESIGN |
| 🟢 | Freemium 수익화 모델 세부 설계 | PM |
