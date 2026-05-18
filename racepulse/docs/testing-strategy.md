# RacePulse 테스트 전략 완전 가이드

> 이 문서는 RacePulse 프로젝트에서 **왜** 테스트가 필요한지, **어떤** 테스트를 **언제** 해야 하는지를 설명합니다.

---

## 📌 테스트가 왜 필요한가?

RacePulse는 세 가지 이유로 테스트가 일반 프로젝트보다 더 중요합니다.

1. **돈과 직결됨** — 예측 결과가 틀리면 사용자 신뢰를 잃습니다. 버그가 잘못된 예측을 만들면 치명적입니다.
2. **복잡한 데이터 파이프라인** — 마사회 API → FastAPI → PostgreSQL → ML 모델 → Spring Boot → React 까지 여러 시스템이 연결됩니다. 어디 하나 어긋나면 전체가 무너집니다.
3. **실운영 목표** — 포트폴리오가 아닌 실제 서비스를 목표로 하므로, 배포 전 품질 보증이 필수입니다.

---

## 🗺️ 테스트 종류 전체 지도

```
┌─────────────────────────────────────────────────────┐
│  Layer 5: E2E 테스트 (사용자 시나리오 전체 흐름)          │
├─────────────────────────────────────────────────────┤
│  Layer 4: 시스템 테스트 (성능 / 부하 / 보안)              │
├─────────────────────────────────────────────────────┤
│  Layer 3: 통합 테스트 (서버 간 통신 / DB 연동)            │
├─────────────────────────────────────────────────────┤
│  Layer 2: ML 검증 테스트 (예측 정확도 / 데이터 품질)       │
├─────────────────────────────────────────────────────┤
│  Layer 1: 단위 테스트 (함수 하나하나의 동작)               │
└─────────────────────────────────────────────────────┘
```

아래로 갈수록 빠르고 저렴하고 자주 실행합니다.
위로 갈수록 느리고 비싸지만 실제 운영 품질을 보장합니다.

---

## Layer 1 — 단위 테스트 (Unit Test)

> **목적**: 함수/메서드 하나가 올바르게 동작하는지 확인합니다.
> **실행 주기**: 코드 수정할 때마다 (CI에서 자동)
> **소요 시간**: 수 초

---

### 1-1. BE 단위 테스트 — `JwtTokenProviderTest.java`

**왜 필요한가?**
JWT는 모든 인증의 핵심입니다. 토큰이 잘못 만들어지거나, 위조된 토큰을 통과시키거나, 만료된 토큰을 허용하면 전체 보안이 무너집니다.

**현재 구현 상태**: ✅ 완료 (10개 통과)

| 테스트 케이스 | 검증 내용 | 왜 중요한가 |
|-------------|---------|-----------|
| Access Token 생성 후 userId 추출 | 토큰에서 사용자 ID를 정확히 읽어오는가 | 로그인된 사용자 식별의 기반 |
| Access Token 생성 후 role 추출 | 권한 정보가 정확히 담기는가 | 관리자/일반 사용자 구분 |
| 유효한 토큰 → validateToken = true | 정상 토큰을 통과시키는가 | 정상 사용자 접근 허용 |
| 만료된 토큰 → validateToken = false | 만료 토큰을 막는가 | 보안 핵심 |
| 위변조된 토큰 → validateToken = false | 조작된 토큰을 막는가 | 해킹 방어 |
| 빈 문자열/null → validateToken = false | 엣지케이스 처리 | **실제 버그 발견됨** (500 에러 방지) |
| rememberMe=false → 24시간 만료 | Refresh 토큰 만료 시간 | 보안 정책 준수 |
| rememberMe=true → 3일 만료 | 로그인 유지 옵션 | 사용자 경험 |

**추가로 필요한 테스트**:
```java
// TODO: [Phase 3] 추가 필요
- 동시에 여러 Refresh Token 발급 시 Family 감지 테스트
- Redis 블랙리스트 등록 후 토큰 거부 테스트
- 카카오 OAuth 토큰으로 JWT 발급 테스트
```

---

### 1-2. BE 단위 테스트 — `BusinessException`, `GlobalExceptionHandler`

**왜 필요한가?**
에러코드가 잘못된 HTTP 상태코드로 응답하거나, 에러 메시지가 누락되면 FE가 사용자에게 올바른 안내를 못 합니다.

**현재 구현 상태**: ⏳ 미작성 (Phase 2 필요)

```java
// 작성 필요
@Test void tokenExpired_returns401()
@Test void horseNotFound_returns404()
@Test void duplicateEmail_returns409()
@Test void serverError_returns500_withoutStackTrace()
@Test void errorResponse_format_matches_ApiResponse()
```

---

### 1-3. ML 단위 테스트 — `test_feature_engineering.py`

**왜 필요한가?**
피처(Feature)가 잘못 계산되면 ML 모델이 쓰레기 입력을 받아서 쓰레기 예측을 냅니다. 승률 0.25를 0.025로 계산하면 모델 전체가 망가집니다.

**현재 구현 상태**: ✅ 완료 (22개 통과)

| 테스트 섹션 | 검증 내용 |
|-----------|---------|
| `TestSafeRate` | 승률 계산 정확성 + 0÷0 방지 |
| `TestEncodingDicts` | UP/SAME/DOWN → 1/0/-1 인코딩 |
| `TestJockeyFeaturesNone` | 기수 없을 때 None 반환 |
| `TestTrainerFeaturesNone` | 조교사 없을 때 None 반환 |
| `TestRaceFeaturesEntryNone` | 출전표 없을 때 None 반환 |
| `TestHorseFeaturesDebut` | 신마 데뷔 — ZeroDivision 없음 |
| `TestHorseFeaturesVeteran` | 경력마 승률/평균착순 수치 정확성 |

**추가로 필요한 테스트**:
```python
# TODO: [Phase 2] 추가 필요
def test_feature_count_equals_23()         # 항상 23개 피처 반환
def test_feature_values_numeric_or_none()  # 모든 값이 float 또는 None
def test_no_future_data_leakage()          # 현재 경주보다 미래 데이터 미포함
def test_gate_no_within_valid_range()      # 게이트 번호 1~16
```

---

### 1-4. ML 단위 테스트 — `test_monte_carlo.py`

**왜 필요한가?**
Monte Carlo는 확률론에 기반합니다. 수학적 불변량(예: 모든 말의 1위 확률 합 = 100%)이 깨지면 FE에 이상한 숫자가 표시됩니다.

**현재 구현 상태**: ✅ 완료 (21개 통과 — 기존 16개 + 신규 5개)

| 불변량 | 설명 |
|-------|------|
| 전체 1위 확률 합 = 100% | 반드시 누군가 1위 |
| 각 말 순위 분포 합 = 100% | 1위+2위+3위+4위이하 = 100 |
| 말 1마리 → 1위 확률 100% | 엣지케이스 |
| upset_probability ∈ [0, 100] | 이변 확률 범위 |
| expected_rank ∈ [1, N] | 예상 순위 범위 |
| 같은 시드 → 같은 결과 | 재현성 보장 |
| converged 필드는 bool | 고도화 후 추가 |
| confidence_score ∈ [0, 100] | 신뢰도 점수 범위 |
| n_simulations ∈ [10000, 100000] | Adaptive 범위 |

---

### 1-5. FE 컴포넌트 테스트 — `DataStatusBadge.test.tsx`

**왜 필요한가?**
데이터 상태 뱃지는 사용자가 "지금 데이터가 준비 중인지, 수집 중인지"를 아는 핵심 UI입니다. 틀린 상태가 표시되면 사용자 혼란을 줍니다.

**현재 구현 상태**: ✅ 완료 (9개 통과)

**추가로 필요한 테스트**:
```tsx
// TODO: [Phase 2] 추가 필요
- PredictionCard 컴포넌트: 승률 표시 정확성
- RaceCountdown 컴포넌트: 카운트다운 종료 처리
- MonteCarloChart 컴포넌트: 데이터 없을 때 빈 상태 표시
- Toast 컴포넌트: 에러/성공 메시지 자동 사라짐
```

---

## Layer 2 — ML 검증 테스트 (Data & Model Validation)

> **목적**: 데이터 품질과 ML 모델의 예측 능력을 수치로 검증합니다.
> **실행 주기**: 데이터 수집 후, 모델 학습 후
> **소요 시간**: 수 분 ~ 수십 분

---

### 2-1. 데이터 품질 테스트 (현재 진행 중!)

**왜 필요한가?**
마사회 API 데이터는 결측값, 구버전 포맷, 이상값이 있을 수 있습니다. 나쁜 데이터가 모델에 들어가면 나쁜 예측이 나옵니다 ("Garbage In, Garbage Out").

**검증 지표**:

| 지표 | 기준 | 현재 결과 |
|-----|------|---------|
| `qualityScore` | ≥ 85 = GOOD | **97.6점 (GOOD)** ✅ |
| `nullCount` | 최소화 | 6건 (153건 중) ✅ |
| `anomalyCount` | 0 목표 | 0건 ✅ |
| 결측값 비율 | < 5% | 약 3.9% ✅ |

**자동화 필요 (Phase 3)**:
```python
# 매일 수집 후 자동 실행
def test_quality_score_above_threshold():
    assert quality_score >= 85, "데이터 품질 저하 — 알람 발송"

def test_null_rate_below_5_percent():
    null_rate = null_count / records_collected
    assert null_rate < 0.05

def test_no_future_race_in_results():
    assert all(rc_date <= today for rc_date in result_dates)
```

---

### 2-2. ML 모델 정확도 테스트

**왜 필요한가?**
이 프로젝트의 존재 이유입니다. 예측이 맞지 않으면 서비스 의미가 없습니다.

**기준 (4차 회의 확정)**:

| Top-3 정확도 | 판단 | 조치 |
|------------|------|------|
| 60% 미만 | ❌ 심각 | 피처 재검토, 데이터 추가 수집 |
| 60~69% | ⚠️ 미달 | 피처 엔지니어링 개선 후 재학습 |
| 70~79% | 🟡 보통 | Phase 2 진행, 지속 개선 |
| **80% 이상** | ✅ 목표 | **실운영 전환 가능** |

**검증 방법**:
```
POST /ml/train → 학습
GET  /ml/accuracy → Top-1 / Top-3 정확도 확인
```

**백테스팅 (Phase 2)**:
```
학습 데이터: 2025-01 ~ 2025-12 (과거 1년)
테스트 데이터: 2026-01 ~ 현재 (한 번도 본 적 없는 데이터)
→ 시간 순서를 반드시 지켜야 함 (미래 데이터로 과거를 학습하면 안 됨)
```

---

### 2-3. 피처 중요도 검증 테스트

**왜 필요한가?**
어떤 피처가 예측에 기여하는지 알아야 모델을 개선할 수 있습니다. 또한 "왜 이 말을 1위로 예측했는가"를 설명할 수 있어야 합니다.

**현재 구현 상태**: ⏳ Phase 2 필요

```python
# SHAP value 기반 피처 중요도 검증
def test_top3_features_make_sense():
    # 상위 피처가 horse_win_rate, jockey_win_rate 등
    # 상식적으로 중요한 피처여야 함
    assert "horse_win_rate_total" in top5_features
    assert "jockey_win_rate_total" in top5_features

def test_no_feature_dominates_100_percent():
    # 하나의 피처가 모든 예측을 결정하면 과적합
    assert max(importances) < 0.5
```

---

### 2-4. Monte Carlo 통계 검증 테스트

**왜 필요한가?**
QMC + Adaptive 고도화 후, 시뮬레이션 결과가 이론적으로 올바른지 검증해야 합니다.

**현재 구현 상태**: ✅ 수학적 불변량 테스트 완료

**추가 필요 (Phase 3)**:
```python
def test_qmc_lower_variance_than_random():
    # Sobol 수열이 순수 랜덤보다 분산이 낮아야 함
    qmc_variance = run_qmc_simulation().variance
    random_variance = run_random_simulation().variance
    assert qmc_variance < random_variance

def test_adaptive_convergence_reached():
    result = run_simulation(race_id=1)
    if result["converged"]:
        # CI 폭이 실제로 1% 이하인지 확인
        assert result["ci_width"] <= 0.01
```

---

## Layer 3 — 통합 테스트 (Integration Test)

> **목적**: 여러 시스템이 함께 동작할 때 올바로 작동하는지 확인합니다.
> **실행 주기**: PR 생성 시, 배포 전
> **소요 시간**: 수 분

---

### 3-1. BE API 컨트롤러 테스트 — `AuthControllerTest.java`

**왜 필요한가?**
API 엔드포인트가 올바른 HTTP 상태코드, 응답 형식, 쿠키 설정을 하는지 검증합니다. DB나 외부 서비스 없이도 API 계층만 테스트할 수 있습니다.

**현재 구현 상태**: ✅ 완료 (11개 통과, MockMvc 방식)

**추가로 필요한 테스트**:
```java
// TODO: [Phase 2] 추가 필요
@Test void getRaces_returns_lastUpdated_dataStatus_nextUpdate()
@Test void getPrediction_returns_monteCarloResults()
@Test void favoriteHorse_requires_authentication()
@Test void adminEndpoint_requires_admin_role()
@Test void rateLimiting_blocks_after_5_failed_logins()
```

---

### 3-2. ML-DB 통합 테스트

**왜 필요한가?**
피처를 계산하고 DB에 저장하는 파이프라인이 실제 DB와 올바르게 연동되는지 확인합니다.

**현재 구현 상태**: ⏳ 미작성 (Phase 2 필요)

```python
# 실제 DB 연결 후 테스트 (테스트 DB 별도 사용 권장)
async def test_feature_store_roundtrip():
    """계산 → 저장 → 조회가 일관성 있게 동작하는가"""
    features = await svc.build_feature_vector(entry_id=1)
    record = await svc.save_to_feature_store(1, 1, features)
    loaded = await db.get(MLFeatureStore, record.id)
    assert loaded.features == features

async def test_prediction_saves_and_loads():
    """예측 결과가 저장 후 조회 시 동일한가"""
    results = await predictor.predict_race(race_id=1)
    loaded = await predictor.get_prediction_result(race_id=1)
    assert len(loaded) == len(results)
```

---

### 3-3. KRA API 연동 테스트

**왜 필요한가?**
마사회 API가 예상과 다른 형식으로 응답해도 우리 시스템이 안전하게 처리하는지 확인합니다.

**현재 구현 상태**: ✅ `kra_api.py` `_normalize_items` 수정 완료

```python
# 다양한 API 응답 포맷 테스트
def test_normalize_empty_string_items():
    """items가 빈 문자열일 때 빈 리스트 반환"""
    payload = {"response": {"body": {"items": ""}}}
    assert KRAApiService._normalize_items(payload) == []

def test_normalize_single_item_dict():
    """단건 응답(dict)을 리스트로 감싸는가"""
    payload = {"response": {"body": {"items": {"item": {"rcNo": 1}}}}}
    result = KRAApiService._normalize_items(payload)
    assert len(result) == 1

def test_rate_limit_stops_at_threshold():
    """일일 한도 도달 시 KRARateLimitExceededError 발생"""
    # Redis 카운터를 2800으로 설정 후 호출
    with pytest.raises(KRARateLimitExceededError):
        await svc.fetch_race_schedule(...)
```

---

## Layer 4 — 시스템 테스트 (System Test)

> **목적**: 실제 운영 환경과 유사한 조건에서 성능, 보안, 안정성을 검증합니다.
> **실행 주기**: Phase 4 (배포 전)
> **소요 시간**: 수십 분 ~ 수 시간

---

### 4-1. 성능 테스트 (Performance Test)

**왜 필요한가?**
경마 당일 많은 사용자가 동시에 접속할 때 서비스가 버텨야 합니다.

| 측정 항목 | 목표 기준 | 도구 |
|---------|---------|------|
| API 응답시간 (일반) | p95 < 500ms | k6, Locust |
| API 응답시간 (예측 조회) | p95 < 2초 | k6 |
| 동시 사용자 100명 | 에러율 < 1% | Locust |
| DB 쿼리 시간 | < 100ms | pgBadger |
| Monte Carlo 계산 | < 30초/경주 | 직접 측정 |

```python
# k6 스크립트 예시
# POST /api/v1/auth/login → GET /api/v1/races → GET /api/v1/predictions/1
# 가상 사용자 100명, 5분 유지
```

---

### 4-2. 부하 테스트 (Load Test)

**왜 필요한가?**
경주 당일 오전(출전표 확정 시간) 동시 접속 급증을 시뮬레이션합니다.

```
시나리오: 토요일 오전 8시, 출전표 확정 직후
- 사용자 500명이 30분 안에 접속
- /api/v1/races/{id}/prediction 집중 호출
→ 시스템이 무너지지 않는가?
```

---

### 4-3. 보안 테스트 (Security Test)

**왜 필요한가?**
개인정보와 사용자 데이터를 보호해야 합니다.

| 테스트 | 검증 내용 |
|-------|---------|
| SQL Injection | `'; DROP TABLE users; --` 입력 시 에러 없이 거부 |
| XSS | 스크립트 태그 입력 시 이스케이프 처리 |
| CSRF | 쿠키 SameSite=Strict 동작 확인 |
| Rate Limiting | 로그인 5회 실패 후 15분 잠금 동작 |
| JWT 위조 | 서명 변조된 토큰 거부 확인 |
| 민감정보 노출 | API 응답에 password, secret 등 미포함 확인 |

---

### 4-4. 인프라 헬스체크 테스트

**왜 필요한가?**
Docker 컨테이너, DB, Redis, 외부 API 연결 상태를 배포 전 자동으로 확인합니다.

**현재 구현 상태**: ✅ `/health` 엔드포인트 구현 완료

```bash
# 배포 파이프라인에서 자동 실행
curl http://localhost:8080/api/v1/health  → {"status": "UP"}
curl http://localhost:8000/health         → {"status": "UP"}
docker exec racepulse-postgres pg_isready -U racepulse
docker exec racepulse-redis redis-cli ping
```

---

## Layer 5 — E2E 테스트 (End-to-End Test)

> **목적**: 실제 사용자 시나리오 전체를 자동화하여 브라우저 레벨에서 검증합니다.
> **실행 주기**: 주 1회, 배포 전
> **도구**: Playwright 또는 Cypress
> **현재 구현 상태**: ⏳ Phase 4 예정

---

### 5-1. 핵심 사용자 시나리오

```
시나리오 1: 신규 가입 → 예측 조회
  1. 회원가입 (이메일/비밀번호)
  2. 로그인
  3. 경주 목록 페이지 진입
  4. 이번 주 토요일 1경주 클릭
  5. ML 예측 결과 + Monte Carlo 차트 확인
  6. 즐겨찾기 추가
  7. 마이페이지에서 즐겨찾기 확인

시나리오 2: 카카오 로그인
  1. 카카오 로그인 버튼 클릭
  2. 카카오 OAuth 페이지 (모킹)
  3. 콜백 처리 후 메인 화면 진입
  4. JWT 토큰 발급 확인

시나리오 3: AI 해설 렌더링
  1. 경주 상세 페이지 진입
  2. AI 해설 타이핑 애니메이션 시작
  3. 600자 이상 해설 완성 확인
  4. 사행성 금지 문구 하단 포함 확인

시나리오 4: 데이터 없는 경주
  1. 미래 예정 경주 클릭
  2. "준비중" 뱃지 표시 확인
  3. next_update 카운트다운 표시 확인
```

---

## CI/CD 파이프라인 — 현재 구현 현황

**파일 위치**: `.github/workflows/test.yml`

```
develop 브랜치 push 또는 main PR 시 자동 실행

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Backend (JUnit) │  │  ML (pytest)     │  │  Frontend (Vitest)│
│                  │  │                  │  │                  │
│  JwtTokenProvider│  │  test_feature_   │  │  DataStatusBadge │
│  Test (10개)     │  │  engineering.py  │  │  .test.tsx (9개) │
│                  │  │  (22개)          │  │                  │
│  AuthController  │  │  test_monte_     │  │  TypeScript 타입  │
│  Test (11개)     │  │  carlo.py (21개) │  │  체크             │
└────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘
         └───────────────┬─────┘──────────────────────┘
                         ↓
              ✅ 전체 통과 시 main 머지 허용
```

**해결된 CI 문제들**:
- `gradlew` 실행권한: `git update-index --chmod=+x gradlew`
- `npm ci` → `npm install` 변경
- BE 테스트용 PostgreSQL/Redis 서비스 추가
- ML `PYTHONPATH=.` 환경변수 설정
- Tailwind v4 + jsdom 충돌: `css: false` 설정

---

## Phase별 테스트 로드맵

| Phase | 추가할 테스트 | 이유 |
|-------|------------|------|
| **Phase 2 (현재)** | 데이터 품질 자동 알람, ML 정확도 측정, 피처 중요도 검증 | ML 파이프라인 완성 |
| **Phase 3** | Monte Carlo 통계 검증, Bayesian 업데이트 검증 | 고도화 품질 보증 |
| **Phase 4** | 성능 테스트(k6), 보안 테스트, E2E(Playwright) | 실운영 전 최종 검증 |

---

## 오늘 진행한 테스트 (2026-05-18)

오늘은 코드 단위 테스트가 아닌 **실데이터 통합 테스트**를 진행했습니다.

| 테스트 | 결과 | 의미 |
|-------|------|------|
| 마사회 API 연결 | ✅ | API 키 유효, 네트워크 정상 |
| 경주 일정 수집 (schedule) | ✅ 품질 97.6점 | 마사회 API 데이터 품질 GOOD |
| 출전표 수집 (entry) | ✅ 103건 | 기수/조교사/말 데이터 정상 |
| 경주 결과 수집 (results) | ✅ 103건 | 착순/구간기록 정상 |
| 피처 계산 | 🔧 디버깅 중 | DB 스키마 정렬 중 |
| 모델 학습 (trainSamples=8) | ⚠️ 데이터 부족 | 과거 데이터 수집 중 |
| 과거 데이터 일괄 수집 | 🔄 실행 중 | 2025-01 ~ 2026-04 수집 |

---

*최초 작성: 2026-05-18*
*다음 업데이트: Phase 3 시작 시*
