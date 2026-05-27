# RacePulse 프로젝트 심층 진단 문서

작성일: 2026-05-27  
작성 범위: 프론트엔드, Spring Boot 백엔드, FastAPI ML 서버, DB, Docker, CI, Windows 작업 스케줄러, 화면 완성도  
작업 원칙: 코드 수정 없이 읽기/실행 검증만 수행

---

## 1. 변경 목표

현재 프로젝트가 어떤 의도로 구성되어 있는지 다시 확인하고, 이전에 확인한 문제에 더해 실행/빌드/테스트/API/화면/자동화/운영 위험을 가능한 범위에서 더 깊게 찾아 정리한다.

---

## 2. 핵심 변경 요약

이번 점검에서 실제 수정한 코드는 없다. 새로 추가한 파일은 이 문서 하나뿐이다.

전체 결론은 다음과 같다.

- 프로젝트의 큰 방향은 명확하다. `React 화면 -> Spring Boot API -> PostgreSQL/Redis -> FastAPI ML 서버` 구조로, 경마 데이터 수집/예측/해설/사용자 기능을 하나의 로컬 개발 환경에 묶으려는 의도다.
- 하지만 현재 상태는 "완성된 자동화 서비스"가 아니다. 일부 핵심 화면은 임시 Placeholder이고, 프론트가 호출하는 API와 백엔드 구현이 맞지 않는 곳이 있다.
- Docker 기반 전체 실행은 아직 깨져 있다. 특히 ML 서버 Dockerfile은 빌드 자체가 실패하고, 백엔드는 Compose에서 실제 앱을 실행하지 않는다.
- 현재 로컬에서는 프론트/백엔드/ML 서버가 각각 수동 또는 외부 프로세스로 떠 있어 보이며, Compose만으로 재현 가능한 상태가 아니다.
- 테스트는 대체로 통과하지만, 테스트가 커버하지 못하는 화면/API 불일치와 운영 자동화 문제가 여러 개 있다.
- 전역 규칙인 "화면 UI 문구는 반드시 한글"을 위반하는 영어 UI 텍스트가 남아 있다.
- `.env`에는 실제 키가 들어 있어 보이며, 절대 문서/로그/명령 출력에 그대로 남기면 안 된다.

---

## 3. 확인한 실행 결과

### 3.1 현재 서비스 응답 상태

| 항목 | 확인 결과 | 비고 |
|---|---:|---|
| 프론트엔드 `http://localhost:3000` | 200 | Vite 개발 서버 응답 |
| 백엔드 `http://localhost:8080/api/v1/health` | 정상 | `application/json;charset=UTF-8` |
| ML 서버 `http://localhost:8000/health` | 정상 | `application/json`, charset 없음 |
| PostgreSQL 컨테이너 | healthy | Docker Compose 기준 |
| Redis 컨테이너 | healthy | Docker Compose 기준 |
| Compose 백엔드 컨테이너 | 없음 | 현재 백엔드는 Compose 밖에서 실행 중으로 보임 |
| Compose ML 컨테이너 | 없음 | 현재 ML 서버도 Compose 밖에서 실행 중으로 보임 |

### 3.2 테스트/빌드 결과

| 명령 | 결과 | 해석 |
|---|---:|---|
| `frontend npm run build` | 성공 | 단, 압축 플러그인 출력 경로 이상 징후 있음 |
| `frontend npm run test` | 성공, 1개 파일/9개 테스트 | 테스트 범위가 매우 좁음 |
| `frontend npm run lint` | 성공 | 린트 규칙으로는 현재 문제를 잡지 못함 |
| `backend gradlew test` | 성공 | JUnit 테스트 통과 |
| `ml-server venv pytest` | 성공, 56개 테스트 | ML 단위 테스트는 양호 |
| `ml-server python -m pytest` | 실패 | 전역 Python에는 pytest 없음 |
| `ml-server docker build .` | 실패 | Dockerfile 1행 이미지명 오류 |

### 3.3 DB 데이터 현황

현재 로컬 DB에는 데이터가 꽤 들어 있다.

| 테이블 | 건수 |
|---|---:|
| `races` | 12,898 |
| `horses` | 10,574 |
| `race_entries` | 132,601 |
| `race_results` | 132,243 |
| `predictions` | 426 |
| `jockeys` | 164 |
| `trainers` | 145 |

이 데이터 덕분에 일부 화면은 동작하지만, 구조적으로 API가 빠진 곳은 데이터가 있어도 화면이 정상 표시되지 않는다.

---

## 4. 치명/높음 우선순위 문제

### 4.1 ML 서버 Docker 빌드가 실패한다

- 근거: `ml-server/Dockerfile:1`
- 현재 내용: `FROM python=:3.11-slim`
- 실제 검증: `docker build .` 실패
- 오류 요약: `failed to parse stage name "python=:3.11-slim": invalid reference format`

영향:

- `docker compose up`으로 ML 서버를 띄울 수 없다.
- 로컬에서는 수동 실행으로 우회할 수 있지만, 배포/재현/신규 환경 구성은 막힌다.

권장 조치:

- `python:3.11-slim` 형태로 이미지명을 바로잡아야 한다.
- 수정 후 `docker compose build ml-server`와 `/health`, `/health/db`까지 확인해야 한다.

---

### 4.2 Docker Compose의 백엔드는 실제 Spring Boot 앱을 실행하지 않는다

- 근거: `docker-compose.yml:66`
- 현재 구성: `image: eclipse-temurin:21-jre`
- 주석에도 "임시 이미지, 실제 앱 없이 컨테이너만 기동 확인용"이라고 되어 있다.

영향:

- Compose만으로는 백엔드 API가 뜨지 않는다.
- 현재 8080 백엔드는 로컬 Java 프로세스에서 떠 있는 것으로 보이며, Docker 환경 재현성이 없다.
- Windows 작업 스케줄러/로컬 실행과 Docker 실행이 서로 다른 상태를 만든다.

권장 조치:

- 백엔드 Dockerfile을 만들거나 Gradle bootJar 산출물을 컨테이너에 넣는 방식으로 Compose 구성을 완성해야 한다.
- Compose 헬스체크가 실제 앱 컨테이너 기준으로 동작하는지 확인해야 한다.

---

### 4.3 Compose의 ML 서버 DB URL이 비동기 엔진과 맞지 않을 가능성이 크다

- 근거: `docker-compose.yml:121`, `ml-server/app/core/database.py`, `ml-server/app/core/config.py`
- Compose 설정: `DB_URL: postgresql://racepulse:racepulse_dev@postgres:5432/racepulse`
- ML 서버 코드: `create_async_engine(settings.db_url, ...)`
- 기본 로컬 설정: `postgresql+asyncpg://...`

영향:

- Dockerfile을 고쳐도, Compose 환경에서는 SQLAlchemy async engine이 동기 드라이버 URL을 받아 기동 실패할 가능성이 있다.
- 현재 로컬 venv 실행은 기본값 `postgresql+asyncpg://...`를 사용하고 있어 문제가 가려져 있다.

권장 조치:

- Compose의 `DB_URL`도 `postgresql+asyncpg://...` 형태로 맞춰야 한다.
- 환경별 설정값을 실제 기동 방식과 일치시키는 검증을 추가해야 한다.

---

### 4.4 프론트가 호출하는 API와 백엔드 구현이 맞지 않는다

실제 요청 결과:

| 프론트 기대 API | 현재 응답 | 원인 |
|---|---:|---|
| `/api/v1/horses/1` | 500 | 백엔드에 단건 조회 매핑 없음 |
| `/api/v1/racecourses/SC` | 500 | 백엔드에 단건 조회 매핑 없음 |
| `/api/v1/jockeys/1` | 403 | 백엔드 컨트롤러 없음 + Security 공개 허용 없음 |
| `/api/v1/trainers/1` | 403 | 백엔드 컨트롤러 없음 + Security 공개 허용 없음 |

근거:

- 프론트 경주마 단건 호출: `frontend/src/api/horseApi.ts:24`
- 백엔드 경주마 컨트롤러: `backend/.../HorseController.java`에는 목록 `@GetMapping`만 있음
- 프론트 기수/조교사 호출: `frontend/src/api/jockeyApi.ts:14`, `frontend/src/api/trainerApi.ts:14`
- 백엔드 전체 엔드포인트 검색 결과 `/api/v1/jockeys`, `/api/v1/trainers` 컨트롤러 없음

영향:

- 경주마 상세 화면은 데이터가 있어도 실패한다.
- 출전 명단에서 말/기수/조교사를 클릭하면 실패 화면 또는 403으로 이어질 수 있다.
- 통합 검색 결과가 상세 페이지로 연결되어도 실제 상세가 깨진다.

권장 조치:

- `GET /api/v1/horses/{horseId}` 구현
- `GET /api/v1/racecourses/{meetCode}` 구현 또는 프론트 라우트 제거
- `GET /api/v1/jockeys/{jockeyId}`, `GET /api/v1/trainers/{trainerId}` 구현
- 공개 조회가 맞다면 SecurityConfig에 `/api/v1/jockeys/**`, `/api/v1/trainers/**` 허용 추가

---

### 4.5 FastAPI 응답에 `charset=utf-8`이 없어 일부 클라이언트에서 한글이 깨진다

- 근거: `http://localhost:8000/collection/status` 응답 헤더
- 확인된 헤더: `Content-Type: application/json`
- 실제 PowerShell RawContent에서 메시지가 `ì¤ë...` 형태로 깨져 보임
- Spring Boot는 `application/json;charset=UTF-8`로 응답함

영향:

- 전역 규칙의 "한글 깨짐 방지" 요구와 충돌한다.
- 브라우저는 대부분 JSON UTF-8을 잘 해석하지만, 운영 도구/스크립트/PowerShell/로그에서는 깨질 수 있다.
- 관리자 API, 수집 상태 API 응답 메시지가 운영자가 읽기 어려워질 수 있다.

권장 조치:

- FastAPI JSON 응답의 charset 정책을 명확히 해야 한다.
- 최소한 운영/관리 스크립트에서 UTF-8 디코딩을 강제해야 한다.

---

### 4.6 FastAPI 관리자 스케줄러 상태 API가 실제 실행 중인 스케줄러를 보지 못한다

- 근거: `ml-server/app/api/admin.py:42-50`
- 코드 주석: 실제 스케줄러는 `main.py lifespan`에서 생성되지만, admin.py는 별도 인스턴스를 만들어 사용
- 실제 응답: `/admin/scheduler/status`에서 `schedulerRunning: false`
- 하지만 ML 서버가 떠 있고 `lifespan`에서는 스케줄러를 시작하도록 되어 있음

영향:

- 관리자 화면/운영자가 스케줄러가 꺼졌다고 잘못 판단할 수 있다.
- 실제 등록된 작업의 다음 실행 시각을 확인할 수 없다.
- 장애 대응 시 잘못된 판단을 유도한다.

권장 조치:

- `lifespan`에서 만든 스케줄러 인스턴스를 app state에 저장하고, admin API가 그 인스턴스를 참조해야 한다.
- `CollectionScheduler`를 새로 만드는 방식은 상태 조회용으로 부정확하다.

---

### 4.7 Windows 작업 스케줄러 자동화가 최근 실패/중단 이력이 있다

현재 등록된 작업:

| 작업 | 최근 결과 | 다음 실행 |
|---|---:|---|
| `RacePulse_BulkCollect` | 1 | 2026-05-28 03:00 |
| `RacePulse_NightlyPipeline` | 0 | 2026-05-28 05:00 |

추가 로그:

- `bulk_stderr.txt`에는 `httpx.ReadTimeout` 스택트레이스가 남아 있다.
- `nightly_log.txt` 최신 기록에는 `FastAPI 서버 미실행 — 파이프라인 중단`이 있다.
- 과거 로그에는 FE 빌드가 `[WinError 267] 디렉터리 이름이 올바르지 않습니다`로 실패한 이력이 있다.

영향:

- "완전 자동화" 상태로 보기 어렵다.
- ML 서버가 켜져 있지 않으면 야간 파이프라인은 바로 중단된다.
- 수집 작업은 타임아웃 상황에서 실패 결과를 남긴다.

권장 조치:

- 작업 스케줄러가 ML 서버 기동 상태를 보장하거나, ML 서버를 서비스로 등록해야 한다.
- 실패 시 재시도/알림/로그 로테이션 정책을 추가해야 한다.
- 대용량 수집 작업은 현재보다 더 작은 단위의 체크포인트와 재시도 단위가 필요하다.

---

### 4.8 실제 API 키/시크릿 관리 위험이 있다

- `.env` 파일은 `.gitignore`에 포함되어 있어 커밋 위험은 낮다.
- 하지만 `docker compose config`를 실행하면 `.env` 값이 콘솔에 평문으로 출력된다.
- 이 진단 문서에는 실제 키 값을 절대 적지 않았다.

영향:

- 터미널 로그, 화면 공유, CI 로그, 문서 복붙 과정에서 키가 유출될 수 있다.
- 특히 OpenAI/Kakao/KRA/Weather 키는 노출 시 즉시 폐기/재발급 대상이다.

권장 조치:

- 이미 화면/로그/대화에 노출된 키가 있다면 폐기 후 재발급해야 한다.
- `docker compose config` 출력물을 공유하지 않는 규칙을 문서화해야 한다.
- 운영 전에는 Secret Manager 또는 CI secrets로 분리해야 한다.

---

## 5. 화면 완성도 문제

### 5.1 명시적인 Placeholder 화면

근거: `frontend/src/App.tsx`

아래 라우트는 실제 화면이 아니라 `[페이지명] 페이지 준비 중...`을 보여준다.

| 경로 | 상태 |
|---|---|
| `/races/:raceId/result` | 경주 결과 화면 없음 |
| `/races/:raceId/commentary` | AI 해설 화면 없음 |
| `/horses` | 경주마 목록 화면 없음 |
| `/horses/:horseId/history` | 경주마 성적 이력 화면 없음 |
| `/racecourses` | 경마장 목록 화면 없음 |
| `/racecourses/:meetCode` | 경마장 상세 화면 없음 |
| `/login` | 로그인 화면 없음 |
| `/register` | 회원가입 화면 없음 |
| `/auth/kakao/callback` | 카카오 OAuth 콜백 화면 없음 |
| `/admin` | 관리자 대시보드 없음 |
| `/admin/collection` | 수집 현황 화면 없음 |

영향:

- 사용자가 자연스럽게 이동할 수 있는 메뉴/링크가 있어도 최종 화면은 준비 중이다.
- 인증/관리/해설/결과처럼 서비스 핵심 경험 일부가 비어 있다.

권장 조치:

- 우선순위를 나누어 실제 사용자 경로부터 완성해야 한다.
- 최소 1차 목표는 `로그인`, `경주 결과`, `AI 해설`, `경주마 목록/상세`, `관리자 수집 현황`이다.

---

### 5.2 실제 페이지 파일은 있지만 내부 기능이 미완성인 화면

| 화면 | 근거 | 미완성 내용 |
|---|---|---|
| 홈 | `HomePage.tsx:28` | 정확도 수치가 데모 |
| 대시보드 | `DashboardPage.tsx:22` | 최근 예측 목록이 정적 데모 |
| 주간 대시보드 | `WeeklyDashboardPage.tsx:17-20` | 주간 전용 API 없음, 예측 수 0 고정 |
| 경주마 상세 | `HorseDetailPage.tsx:50`, `143-148` | 경주 이력 API 없음 |
| 기수 상세 | `JockeyDetailPage.tsx:46-47`, `91-96` | 상세/이력 API 미연동 |
| 조교사 상세 | `TrainerDetailPage.tsx:45-46`, `89-94` | 상세/관리마 API 미연동 |
| 광고 보상 모달 | `AdWatchModal.tsx:189` | 실제 광고 SDK 없음 |
| 지갑 구매 | `WalletService.java:148` | 결제 연동 전 지급 껍데기 |

영향:

- 화면은 있어 보이지만 실제 운영 데이터 기반 기능은 아니다.
- 사용자 입장에서는 "되는 것처럼 보이는데 눌러보면 준비 중"인 영역이 많다.

권장 조치:

- 데모 데이터와 실제 데이터를 UI에서 명확히 구분하거나, 데모 영역은 운영 빌드에서 숨겨야 한다.
- API가 없는 화면은 먼저 API 계약서부터 정리해야 한다.

---

### 5.3 전역 규칙 위반: UI에 영어가 노출된다

전역 규칙은 "화면에 표시되는 모든 문구는 반드시 한글"이다. 현재 아래 텍스트가 화면에 표시된다.

예시:

- `AI RACE INTELLIGENCE` (`HomePage.tsx`)
- `TODAY RACES` (`HomePage.tsx`)
- `PREDICTION SCORE` (`HomePage.tsx`, `DashboardPage.tsx`)
- `WEEKLY REPORT` (`WeeklyDashboardPage.tsx`)
- `JOCKEY` (`JockeyDetailPage.tsx`)
- `TRAINER` (`TrainerDetailPage.tsx`)
- `Phase 1 동적 UI`, `Phase 2 동적 UI` (`ComponentDemoPage.tsx`)
- `Google AdSense` 문구는 주석/예정 기능이지만, 광고 모달 내부 노출 가능성을 확인해야 한다.

영향:

- 프로젝트 최상위 규칙 위반이다.
- 외부 사용자 화면으로 그대로 나가면 한글 UX 일관성이 깨진다.

권장 조치:

- 화면에 보이는 영어 레이블은 모두 한글로 바꿔야 한다.
- 코드 내부 타입/상수/주석의 영어는 괜찮지만, 렌더링되는 문자열은 별도 점검해야 한다.

---

### 5.4 프론트가 ML 서버를 직접 호출한다

- 근거: `frontend/src/api/raceApi.ts:26`
- 현재 날씨 API는 Spring Boot를 거치지 않고 `VITE_ML_SERVER_URL` 또는 `http://localhost:8000`으로 직접 호출한다.
- 반면 AI 해설은 Spring Boot가 프록시 역할을 하도록 설계되어 있다.

영향:

- CORS/보안/운영 배포 경로가 기능별로 달라진다.
- 프론트 배포 환경에서 ML 서버 도메인이 직접 노출된다.
- "프론트 -> Spring Boot -> ML"이라는 일관된 의도와 충돌한다.

권장 조치:

- 날씨도 Spring Boot 프록시로 통일할지, ML 직접 호출을 공식 정책으로 둘지 결정해야 한다.
- 공식 정책에 맞춰 CORS와 환경변수를 정리해야 한다.

---

## 6. 백엔드/API 문제

### 6.1 없는 엔드포인트가 404가 아니라 500으로 떨어진다

실제 확인:

- `/api/v1/horses/1` -> 500
- `/api/v1/racecourses/SC` -> 500

추정 원인:

- Security는 공개 허용을 통과시킨 뒤 실제 컨트롤러 매핑이 없고, Spring의 리소스 처리/예외 처리 경로에서 전역 예외 핸들러가 500으로 감싼 것으로 보인다.

영향:

- 프론트는 "없는 기능"과 "서버 오류"를 구분하지 못한다.
- 모니터링에서는 실제 장애처럼 잡힐 수 있다.

권장 조치:

- 없는 API는 404로 응답하도록 예외 처리를 보강해야 한다.
- 더 근본적으로는 프론트가 쓰는 API를 실제 구현해야 한다.

---

### 6.2 기수/조교사 데이터는 DB에 있지만 백엔드 공개 API가 없다

DB에는 `jockeys` 164건, `trainers` 145건이 있다. 검색 서비스와 출전 명단 조인은 해당 테이블을 사용한다. 하지만 상세 API 컨트롤러가 없다.

영향:

- 데이터는 있는데 화면에서 상세를 보여줄 수 없다.
- 검색 결과/출전 명단에서 상세 페이지로 이동하면 실패한다.

권장 조치:

- `JockeyController`, `TrainerController` 또는 `PersonController` 계열 API를 추가해야 한다.
- 상세, 최근 출전, 승률/연대율, 관리마/기승마 목록 범위를 정해야 한다.

---

### 6.3 대시보드 통계가 과대평가될 가능성이 있다

- 근거: `DashboardService.java`
- 현재 대시보드 응답에서 Top-1/Top-3가 100%로 나왔다.
- 예측 데이터 426건과 결과 데이터가 일부 조합된 상태에서 계산되므로, 표본 편향 가능성이 있다.
- 데이터가 없으면 데모 데이터를 반환하는 구조도 있다.

영향:

- 사용자는 실제 모델 성능으로 오해할 수 있다.
- 운영 신뢰도 지표로 쓰기 어렵다.

권장 조치:

- 통계 계산 기준을 명확히 해야 한다. 예: 평가 대상 기간, 완료 경주만, 예측 생성 시점, 누락 제외 기준.
- 데모 데이터 반환 시 응답에 `isDemo: true` 같은 플래그를 포함해야 한다.
- 화면에는 "실제 통계/데모 통계"를 구분해서 표시해야 한다.

---

### 6.4 예측 생성이 조회 API 안에서 자동 실행된다

- 근거: `PredictionService.java`
- 예측 데이터가 없으면 조회 중 `POST /ml/predict/{raceId}`를 호출한다.

영향:

- 단순 조회가 무거운 계산/쓰기 작업을 유발한다.
- 사용자가 같은 화면을 여러 명 동시에 열면 ML 서버에 부하가 몰릴 수 있다.
- 실패 원인 구분이 어렵다.

권장 조치:

- 조회와 생성은 분리하는 편이 운영상 안전하다.
- 자동 생성이 필요하면 락/큐/상태값을 두어 중복 생성을 막아야 한다.

---

## 7. ML 서버/데이터 수집 문제

### 7.1 월간 마스터 수집은 TODO 상태다

- 근거: `ml-server/app/scheduler/scheduler.py`
- `collect_monthly` 내부에 기수/조교사/마필 API 연동 TODO가 있다.

영향:

- 기수/조교사/마필 마스터 데이터가 자동으로 최신화되지 않을 수 있다.
- 상세 API를 만든 뒤에도 데이터 갱신 자동화가 부족할 수 있다.

권장 조치:

- KRAApiService에 기수/조교사/마필 전용 수집 메서드를 구현해야 한다.
- 월간 마스터 작업의 결과를 관리자 화면에서 볼 수 있게 해야 한다.

---

### 7.2 KRA API 키 변수명이 혼동을 만든다

- `KRAApiService`는 `settings.kma_api_key`를 사용한다.
- 하지만 변수명 `KMA`는 보통 기상청(Korea Meteorological Administration)으로 읽힐 수 있다.
- 실제 주석은 한국마사회 API 키라고 설명한다.

영향:

- 유지보수자가 기상청 키와 마사회 키를 혼동할 수 있다.
- `.env`에도 `KMA_API_KEY`, `WEATHER_API_KEY`가 함께 있어 더 헷갈린다.

권장 조치:

- `KRA_API_KEY`처럼 의미가 직접 드러나는 이름으로 정리하는 것이 좋다.
- 기존 `.env` 호환이 필요하면 일정 기간 alias를 둔다.

---

### 7.3 수집 로그 파일이 저장소에 잡히고 있다

현재 git 상태에 아래 파일이 untracked로 보인다.

- `racepulse/ml-server/scripts/bulk_stderr.txt`
- `racepulse/ml-server/scripts/bulk_stdout.txt`
- `racepulse/ml-server/scripts/nightly_log.txt`

영향:

- 대용량 로그, 실패 스택트레이스, API 응답 일부가 실수로 커밋될 수 있다.
- 한글 깨짐 로그가 누적되어 분석이 어려워진다.

권장 조치:

- `*.txt` 전체를 무조건 무시하기 어렵다면 `ml-server/scripts/*_stdout.txt`, `*_stderr.txt`, `nightly_log.txt`, `collect_log.txt` 등을 명시적으로 `.gitignore`에 추가해야 한다.
- 로그는 `logs/` 폴더로 모아 로테이션하는 편이 좋다.

---

### 7.4 Bulk 수집은 타임아웃 시 전체 작업 실패로 끝날 수 있다

- 근거: `bulk_stderr.txt`
- 오류: `httpx.ReadTimeout`
- `bulk_collect.py` 일부 단계는 타임아웃을 잡고 넘어가지만, 피처 계산 단계 등에서는 예외가 상위로 올라갈 수 있다.

영향:

- 장시간 수집 도중 한 요청이 느려지면 작업 스케줄러 결과가 실패로 남는다.
- 재시도 시 어느 지점부터 이어졌는지 운영자가 판단해야 한다.

권장 조치:

- 모든 외부/API 호출 단위에 재시도와 체크포인트를 통일 적용해야 한다.
- 실패한 race_id/date만 별도 목록으로 남겨 재처리 가능하게 해야 한다.

---

## 8. 프론트 빌드/자산 문제

### 8.1 Vite Brotli 압축 출력 로그가 Windows 절대경로를 포함한다

빌드 로그에서 다음과 같은 형태가 출력됐다.

```text
dist/C:/Programmer/Work/horse racing/racepulse/frontend/assets/...
```

실제 파일 시스템에는 `dist/C:` 폴더가 생성되지는 않았다. 하지만 플러그인 로그가 비정상 경로를 보여준다.

영향:

- Windows 환경에서 압축 플러그인의 경로 처리 방식이 불안정할 수 있다.
- CI/Linux와 Windows 로컬 결과가 다를 수 있다.

권장 조치:

- `vite-plugin-compression` 출력 파일 경로를 Windows에서 한 번 더 검증해야 한다.
- 커스텀 gzip 플러그인과 Brotli 플러그인이 같은 파일을 서로 다른 기준 경로로 처리하는지 확인해야 한다.

---

### 8.2 프론트 테스트 범위가 매우 좁다

- 현재 Vitest 결과: 테스트 파일 1개, 테스트 9개
- 실제로는 라우팅/API/인증/예측/대시보드/검색/상세 화면 문제가 많은데 테스트로 잡히지 않는다.

영향:

- 빌드와 린트가 성공해도 사용자 화면은 깨질 수 있다.
- API 계약 불일치를 CI에서 놓친다.

권장 조치:

- 최소한 라우트별 렌더링 테스트와 API mock 테스트를 추가해야 한다.
- 프론트 API 함수와 백엔드 OpenAPI 또는 컨트롤러 매핑을 비교하는 계약 테스트가 필요하다.

---

### 8.3 정적 자산 크기가 크다

빌드 산출물 중 큰 파일:

- `intro-video.mp4`: 약 6.7MB
- `intro-poster.jpg`: 약 6.5MB
- `intro-video.webm`: 약 3.5MB
- `bundle-analysis.html`: 약 548KB
- `vendor-echarts-charts`: 약 474KB

영향:

- 첫 방문 성능에 영향을 줄 수 있다.
- PWA precache에 큰 자산이 포함되면 서비스 워커 설치/업데이트 비용이 커진다.

권장 조치:

- 인트로 영상은 사용자가 실제로 볼 때만 지연 로드하는 정책을 확인해야 한다.
- PWA precache 목록에 대용량 영상이 꼭 필요한지 재검토해야 한다.
- `bundle-analysis.html`은 배포 산출물에 포함하지 않는 편이 안전하다.

---

## 9. CI/자동화 문제

### 9.1 GitHub Actions 설정이 두 군데 있다

- 실제 저장소 루트: `.github/workflows/test.yml`
- 하위 프로젝트 내부: `racepulse/.github/workflows/test.yml`

영향:

- GitHub Actions는 보통 저장소 루트의 `.github/workflows`만 인식한다.
- `racepulse/.github/workflows/test.yml`은 저장소가 현재 루트라면 실행되지 않는 죽은 설정일 가능성이 크다.

권장 조치:

- 루트 워크플로우만 유지하거나, 저장소 구조를 명확히 해야 한다.
- 하위 `.github`는 문서상 혼란을 줄이기 위해 정리 대상이다.

---

### 9.2 CI와 로컬 빌드 환경 버전이 다르다

- 루트 CI 프론트: Node 20
- 하위 CI 프론트: Node 22
- 로컬 package는 Vite 8, React 19, TypeScript 6 계열

영향:

- 로컬/CI/문서 간 버전 차이로 빌드 결과가 달라질 수 있다.

권장 조치:

- `.nvmrc` 또는 Volta 설정 등으로 Node 버전을 고정하는 것이 좋다.
- CI는 `npm install`보다 `npm ci`를 사용하는 편이 재현성이 높다.

---

## 10. 보안/운영 문제

### 10.1 인증 화면이 없는데 보호 라우트는 존재한다

- `PrivateRoute`는 토큰이 없으면 `/login`으로 보낸다.
- 하지만 `/login`은 Placeholder다.

영향:

- 사용자는 로그인 필요 페이지에 접근하면 준비 중 화면으로 막힌다.
- 회원가입/카카오 콜백도 화면 흐름이 완성되지 않았다.

권장 조치:

- 최소 로그인/회원가입/카카오 콜백 화면을 먼저 완성해야 한다.
- 백엔드 인증 API와 프론트 토큰 저장 흐름을 실제로 연결해야 한다.

---

### 10.2 결제/지갑 일부는 껍데기 상태다

- 근거: `WalletService.earnPurchasePlaceholder`
- 주석상 Phase 4 포트원 결제 검증 전까지 구매 편자 지급 API 형태만 준비되어 있다.

영향:

- 운영에서 노출되면 실제 결제 없이 지급 로직이 오해되거나 악용될 수 있다.

권장 조치:

- 운영 빌드에서는 구매 관련 임시 API를 숨기거나 관리자/개발 전용으로 제한해야 한다.
- 결제 검증 완료 전에는 실제 재화 지급과 연결하지 않아야 한다.

---

### 10.3 관리자성 API 인증/권한 정책이 불명확하다

- FastAPI `/admin/**`는 현재 별도 인증 없이 접근 가능한 구조로 보인다.
- Spring Boot 관리자 페이지는 Placeholder다.

영향:

- 수동 수집, rate limit reset 같은 기능이 외부에 노출되면 위험하다.
- 로컬 개발에서는 괜찮아도 운영 배포 전 반드시 막아야 한다.

권장 조치:

- FastAPI admin 라우터에 관리자 인증 또는 내부망 제한을 적용해야 한다.
- Spring Boot를 단일 게이트웨이로 둘 경우 ML admin API 직접 노출을 막아야 한다.

---

## 11. 한글/인코딩 문제

### 11.1 소스 파일은 UTF-8로 보이지만 도구 출력은 깨질 수 있다

`Get-Content -Encoding UTF8`로 읽으면 한글 주석/문구는 대부분 정상이다. 하지만 기본 PowerShell 출력이나 FastAPI 응답은 깨져 보이는 경우가 있었다.

영향:

- 운영자가 로그를 볼 때 한글 메시지를 읽지 못할 수 있다.
- 사용자 보고/문서 복사 과정에서 깨진 문자열이 섞일 수 있다.

권장 조치:

- FastAPI 응답 charset 명시
- PowerShell 스크립트 시작부에 UTF-8 출력 인코딩 설정
- 로그 파일 저장/읽기 모두 UTF-8 명시

---

## 12. 우선순위별 처리 제안

### 12.1 1순위: 실행 재현성 복구

1. ML Dockerfile 이미지명 수정
2. Compose ML DB URL을 asyncpg 형식으로 수정
3. 백엔드 Dockerfile/Compose 실제 실행 구성 추가
4. `docker compose up --build`만으로 프론트 제외 핵심 API가 뜨는지 확인

### 12.2 2순위: 깨지는 사용자 경로 복구

1. `/api/v1/horses/{id}` 구현
2. `/api/v1/jockeys/{id}`, `/api/v1/trainers/{id}` 구현
3. `/api/v1/racecourses/{meetCode}` 구현
4. `/horses`, `/races/:id/result`, `/races/:id/commentary` 실제 화면 추가

### 12.3 3순위: 자동화 신뢰도 확보

1. FastAPI 스케줄러 상태 API가 실제 스케줄러를 보게 수정
2. Windows 작업 스케줄러 실패 시 알림/로그 로테이션 추가
3. Bulk 수집 타임아웃과 재처리 체크포인트 강화
4. 야간 파이프라인이 ML 서버 미실행 시 서버 기동 또는 명확한 실패 알림 처리

### 12.4 4순위: 운영 품질 정리

1. FastAPI charset 문제 해결
2. UI 영어 문구 한글화
3. 데모 데이터와 실제 데이터 구분 플래그 추가
4. 관리자/결제/광고 임시 기능 운영 노출 차단
5. 프론트 라우트/API 계약 테스트 추가

---

## 13. 검증에 사용한 주요 명령

```powershell
npm run build
npm run test
npm run lint
.\gradlew.bat test --no-daemon
.\venv\Scripts\python.exe -m pytest
docker build .
docker compose ps
docker exec racepulse-postgres psql -U racepulse -d racepulse -c "..."
Invoke-WebRequest http://localhost:8080/api/v1/health
Invoke-WebRequest http://localhost:8000/health
Invoke-WebRequest http://localhost:8080/api/v1/horses/1
Invoke-WebRequest http://localhost:8000/admin/scheduler/status
schtasks /query /fo CSV /v
rg -n "TODO|준비 중|데모|Placeholder|Phase" ...
```

---

## 14. 최종 판단

RacePulse는 "경마 데이터 기반 예측 플랫폼"이라는 방향과 레이어 분리는 잘 잡혀 있다. 다만 현재는 개발 중간 단계의 흔적이 많이 남아 있고, 특히 Docker 실행, 화면 완성도, 프론트-백엔드 API 계약, 관리자 자동화 상태 조회, 한글 인코딩/화면 문구 규칙에서 운영 전 필수 정리가 필요하다.

현 상태를 한 문장으로 요약하면 다음과 같다.

> 데이터와 핵심 계산 로직은 상당 부분 들어와 있지만, 사용자가 끊김 없이 쓰는 제품 상태와 운영자가 믿고 자동화에 맡길 수 있는 상태 사이에는 아직 여러 단계의 마감 작업이 남아 있다.
