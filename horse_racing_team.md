# 🏇 RacePulse — 경마 데이터 분석 & 예측 플랫폼

## 🎯 프로젝트 개요

- **목표**: 경마 데이터를 기반으로 한 순수 분석/예측 정보 제공 플랫폼
- **핵심 방향**: 사행성 없는 학습 및 탐구 목적. 베팅/포인트/가상화폐 기능 없음
- **타겟 유저**: 경마에 순수한 호기심을 가진 사람, 데이터 분석에 관심 있는 사람
- **핵심 가치**: 예측 **정확도** 극대화. 이게 이 프로젝트의 존재 이유다.

### 핵심 기능
- [ ] 한국마사회 API 기반 실시간 경주 데이터 수집
- [ ] 통계 기반 승률 예측 알고리즘
- [ ] AI 해설 (GPT 기반, 레이스 흥미 요소 설명)
- [ ] 경주마 / 기수 / 조교사 데이터 시각화 대시보드
- [ ] 과거 데이터 기반 백테스팅 결과 제공

### 절대 하지 않는 것
- ❌ 베팅 기능 (직접 / 시뮬레이션 모두 없음)
- ❌ 포인트, 가상화폐, 랭킹 경쟁
- ❌ "이 말에 걸어라" 식의 직접적 투자 조언 뉘앙스

---

## 👥 역할 정의

### 1️⃣ 백엔드 개발자 (BE)
- **담당**: 사용자 인증/인가, API 서버, 데이터 흐름 조율
- **기술스택**: Spring Boot (Java), Spring Security, JPA/QueryDSL, MySQL/PostgreSQL
- **책임 범위**:
  - REST API 설계 및 제공
  - 한국마사회 API 데이터 수신 → 저장 파이프라인
  - FastAPI(Python) 예측 서버와 통신
  - 유저 관련 기능 (로그인, 즐겨찾기, 조회 히스토리)
- **우선순위**: 데이터 정합성 > API 응답 속도 > 확장성
- **현재 우려사항**: Spring Boot와 FastAPI 역할 경계 모호함 → 첫 회의 안건

---

### 2️⃣ 프론트엔드 개발자 (FE)
- **담당**: 사용자 인터페이스, 데이터 시각화
- **기술스택**: React 18, TypeScript, React Router, Axios, Chart.js or Recharts, Tailwind CSS, Vite PWA Plugin
- **책임 범위**:
  - 경주 목록 / 경주마 상세 / 예측 결과 UI
  - 대시보드: 통계 차트, 예측 신뢰도 시각화
  - AI 해설 렌더링 (타이핑 애니메이션 방식)
  - 반응형 디자인 Mobile First (sm/md/lg/xl 브레이크포인트)
  - PWA: manifest.json + Service Worker + 홈 화면 설치 지원
  - 인트로 영상 (영상2 확정 / MP4 6.4MB / 6초 / 시네마틱 실사 / 다크 네이비+골드 엔딩 슬레이트)
  - 16종 동적 UI 요소 구현
- **우선순위**: 데이터 가독성 > UX 직관성 > 속도
- **확정사항**: 데이터 상태 표시 (준비중/업데이트 예정/데이터 수집 중/기수변경 뱃지)
- **디자인 방향**: 다크 네이비 + 골드 프리미엄 톤 / Mobile First

---

### 3️⃣ 아키텍처 & DB 담당 (ARCH)
- **담당**: 전체 시스템 설계, 데이터베이스 스키마, 인프라
- **기술스택**: PostgreSQL (메인), Redis (캐싱), Docker, AWS EC2/RDS, 마사회 API
- **책임 범위**:
  - 3서버 구조 설계 (React / Spring Boot / FastAPI) 확정 및 통신 방식
  - DB 스키마 설계: 말, 기수, 조교사, 레이스, 예측결과, 유저
  - 캐싱 전략: Redis 적용 범위 결정
  - 데이터 수집 파이프라인 설계 (Batch? 실시간?)
  - 한국마사회 API 분석 및 추가 데이터 소스 탐색
- **우선순위**: 데이터 신뢰성 > 쿼리 성능 > 배포 안정성
- **현재 우려사항**: 마사회 API rate limit 및 갱신 주기 파악 필요

---

### 4️⃣ 프로젝트 매니저 (PM)
- **담당**: 일정 관리, 우선순위 조율, 리스크 식별
- **책임 범위**:
  - 마일스톤 및 스프린트 계획 수립
  - 역할 간 의존성 관리 (BE가 API 안 나오면 FE 블로킹되는 상황 방지)
  - MVP 기준 유지 (범위 확장 방지)
  - 포트폴리오 관점에서의 문서화 기준 관리
- **우선순위**: MVP 빠른 완성 > 완성도 > 기능 수
- **현재 우려사항**: 예측 알고리즘 정확도 높이는 게 시간이 얼마나 걸릴지 예측 불가

---

---

### 5️⃣ 서기 (WR)
- **담당**: 회의 내용 전사, 회의 내용 요약, 회의내용 보고서 작성
- **책임 범위**:
  - 회의의 모든 내용을 기록
  - 회의 마무리에 회의 내용 요약하여 다음 회의를 위해 정리
  - 다음 회의 때 아무런 지장없이 이어서 진행 하도록 md파일에 저장 
- **우선순위**: 다음 회의에 이어질 수 있는 문서 > 회의 내용 요약 보고 > 회의 내용 전사
- **필수 규칙** ⚠️: **md 파일 작성이 끝나면 무조건 저장** — 저장하지 않으면 회의 내용이 소실됨. 예외 없음.

---

### 6️⃣ 웹디자이너 (DESIGN)

- **담당**: UI/UX 디자인, 비주얼 아이덴티티, 디자인 시스템
- **기술스택**: Figma, Adobe Illustrator (또는 동급 툴)
- **책임 범위**:
  - 전체 컬러 팔레트 / 타이포그래피 / 톤앤매너 확정
  - 컴포넌트 디자인 시스템 구축 (FE와 협업)
  - 각 페이지 와이어프레임 + 하이파이 목업
  - 16종 동적 UI 요소 시각 가이드 제공
  - 인트로 영상 비주얼 방향 가이드
  - 반응형 디자인 가이드 (모바일 대응)
- **우선순위**: 브랜드 일관성 > 사용성 > 시각적 완성도
- **확정 디자인 방향**:
  - 컬러: 다크 네이비 + 골드 프리미엄 톤
  - 톤앤매너: 시네마틱, 고급스러움, 진지한 분석 플랫폼
  - "분석 플랫폼" 성격 유지 — 사행성 느낌 금지
  - FE TypeScript/Tailwind 구조에 맞는 디자인 토큰 제공

---

### 7️⃣ 노션 담당자 (NOTION)
- **담당**: 프로젝트 문서화, 노션 페이지 관리, 포트폴리오 정리
- **책임 범위**:

  **회의록 주간 요약**
  - WR이 md에 전사한 내용을 보기 좋게 가공해 노션에 주간 요약 정리
  - 다음 회의 안건 노션에도 미리 공유

  **API 명세서 관리**
  - 39개 엔드포인트 요청 예시 / 응답 예시 / 에러코드 목록 정리
  - 권한별 접근 가능 여부 (GUEST/USER/ADMIN) 명시
  - API 변경 이력 추적 (언제 어떤 API가 추가/수정됐는지)

  **DB 스키마 문서화**
  - 43개 테이블 Phase별 정리
  - 테이블 간 관계도 (ERD 다이어그램) 노션 삽입
  - 컬럼 설명, 인덱스, ENUM 값 목록 정리

  **컴포넌트 라이브러리 문서화**
  - 동적 UI 16종 설명 및 사용법 정리
  - 공통 컴포넌트 목록 및 props 정리
  - 어떤 페이지에서 어떤 컴포넌트 쓰는지 매핑

  **디자인 시스템 문서화**
  - Figma 링크 연동
  - 컬러 팔레트, 타이포그래피, 브랜드 토큰 노션 정리
  - 비개발자도 이해할 수 있도록 시각적으로 정리

  **버그/이슈 트래킹**
  - 노션 데이터베이스로 버그 관리 (발견일/담당자/상태/해결일)
  - Phase별 이슈 분류

  **스프린트 현황 대시보드**
  - Phase별 진행률 시각화
  - 완료/진행중/대기 상태 관리

  **배포 이력 관리**
  - 버전/날짜/주요 변경사항 기록
  - 포트폴리오 타임라인으로 활용 가능하게 정리

  **포트폴리오 문서**
  - 프로젝트 소개 페이지
  - 기술 선택 이유 (왜 PostgreSQL인지, 왜 XGBoost인지 등)
  - 성과 및 수치 (예측 정확도, API 응답속도 등)

- **WR과의 역할 구분**:
  - WR → 회의 내용 실시간 전사 (md 파일)
  - NOTION → WR 내용을 가공해 노션에 보기 좋게 정리
- **우선순위**: 포트폴리오 품질 > 문서 최신화 속도 > 문서 완성도

---

### 8️⃣ Git 관리자 (GIT)
- **담당**: 코드 버전 관리, 브랜치 전략 실행, 코드 품질 게이트 관리
- **책임 범위**:

  **브랜치 관리**
  - `main` — 배포 가능한 안정 코드만. 직접 push 금지, PR + 승인 후 머지만 허용
  - `develop` — 개발 통합 브랜치. feature 브랜치의 머지 대상
  - `feature/*` — 기능 단위 작업 브랜치. 완료 후 develop으로 PR
  - `hotfix/*` — 긴급 버그 수정. main에서 분기 후 main + develop 동시 머지
  - 브랜치 네이밍 기준 수립 (예: `feature/be-auth-login`, `feature/이슈번호-설명`)

  **PR 관리**
  - PR 템플릿 작성 및 관리
  - PR 승인 기준 정의 (최소 승인자 수, 체크리스트)
  - 머지 방식 결정 (Squash / Rebase / Merge commit)
  - 충돌 발생 시 해결 주도 또는 가이드

  **커밋 컨벤션 관리**
  ```
  feat: 새 기능
  fix: 버그 수정
  docs: 문서
  style: 포맷 변경
  refactor: 리팩토링
  test: 테스트
  chore: 빌드/설정
  ```

  **CI/CD 파이프라인**
  - GitHub Actions 설정 및 관리
  - PR 시 자동 빌드/테스트 확인
  - main 머지 시 자동 배포 트리거

  **Repository 보호 설정**
  - main / develop Branch Protection Rule 설정 (직접 push 물리적 차단)
  - 리뷰어 지정, 상태 체크 통과 필수 조건 관리

  **이슈 트래킹 연동**
  - GitHub Issues와 브랜치 연결 컨벤션 수립 및 유지

  **버전 및 릴리즈 관리**
  - Git 태그로 버전 관리 (v0.1.0, v1.0.0 등)
  - Phase별 코드 프리징 + 릴리즈 노트 작성
  - main 머지 = 배포 기준점 관리

  **보안 관리**
  - 민감 파일(.env 등) 커밋 방지 모니터링
  - 실수로 커밋된 시크릿 이력 제거 주도

  **Git 사용 가이드 문서화**
  - 팀원 대상 Git 사용 가이드 작성 (자주 쓰는 명령어, 실수 복구 방법 등)

- **우선순위**: 코드 안정성 > 브랜치 일관성 > 배포 속도
- **보류**: Terraform/AWS 인프라 관리 → 배포 단계(Phase 4) 시점에 역할 재논의

---

## 🏗️ 시스템 아키텍처 (✅ 확정)

```
[사용자 브라우저]
        ↕
[React 프론트엔드]
        ↕ REST API (단일 창구)
[Spring Boot 백엔드]  ←→  [PostgreSQL]
        ↕ HTTP/REST          ↕
[FastAPI Python 서버]   [Redis - 캐시 + 수집 카운터/체크포인트]
        ↕
[예측 모델 (XGBoost/LightGBM) / AI 해설 (GPT API)]

[한국마사회 API] → FastAPI (APScheduler 스케줄 수집 전담)
```

- FE는 Spring Boot만 바라봄 (FastAPI 직접 호출 없음)
- 데이터 수집 / 예측 / AI해설 전담: FastAPI
- 인증 / 유저 / 경주데이터 저장·조회: Spring Boot

---

## 📊 데이터 소스

### 한국마사회 공공데이터 API
- **출처**: [공공데이터포털 data.go.kr](https://www.data.go.kr) → "한국마사회" 검색
- **제공 데이터**: 경주 일정, 출전마 정보, 기수 정보, 레이스 결과, 배당률
- **특이사항**: API 키 발급 필요, rate limit 확인 필요

### 추가 데이터 소스 (탐색 필요)
- KRA 공식 사이트 (race.kra.co.kr) 스크래핑 가능 여부 검토
- 과거 레이스 데이터 (백테스팅용) 확보 방법 논의 필요

---

## 📋 회의 아이젠다

### 🔴 안건 1: Spring Boot vs FastAPI 역할 분리 (최우선)

**문제**: 두 서버의 역할 경계가 불명확하면 중복 개발 + 통신 오버헤드 발생

**선택지 A: Spring Boot = 게이트웨이 + 유저관리, FastAPI = 데이터 + 예측**
```
BE: 인증, 유저, 즐겨찾기 → Spring Boot
데이터 수집, 예측, AI해설 → FastAPI
```
- 장점: 역할 명확
- 단점: Spring Boot가 단순 게이트웨이면 오버스펙

**선택지 B: Spring Boot = 메인 비즈니스 로직, FastAPI = 예측 전용 마이크로서비스**
```
BE: 인증 + 유저 + 경주데이터 저장/조회 → Spring Boot
예측 연산 + AI해설 생성만 → FastAPI
```
- 장점: Spring Boot가 포트폴리오에서 활용도 높음
- 단점: 데이터 수집을 Spring Boot가 해야 하면 배치 스케줄러 구현 필요

**→ 팀 논의 필요**

---

### 🔴 안건 2: 예측 알고리즘 기반 방향

**문제**: 정확도를 높이는 게 최우선인데, 어떤 방식으로 갈 것인가

**선택지 A: 통계/수학 기반**
- 승률 계산: 과거 성적, 출주 횟수, 기수 성적, 마체중 변화, 경주 거리 궁합
- 장점: 설명 가능 (포트폴리오에서 "왜 이렇게 예측했는지" 설명 가능)
- 단점: 정확도 한계 존재

**선택지 B: ML 기반 (scikit-learn, XGBoost 등)**
- 피처 엔지니어링 → 모델 학습 → 예측
- 장점: 더 높은 정확도 가능성
- 단점: 데이터 충분해야 의미있는 학습 가능, 개발 시간 김

**선택지 C: 통계 + ML 하이브리드**
- 통계 기반으로 먼저 MVP, 이후 ML 레이어 추가
- PM 관점에서 제일 현실적

**→ 팀 논의 필요**

---

### 🟡 안건 3: 데이터 수집 파이프라인 방식

- **실시간 방식**: 경주 시작 전 API 호출 → 즉시 처리
- **배치 방식**: 정해진 시간에 마사회 API 전체 수집 (Spring Batch or APScheduler)
- **하이브리드**: 배치로 기본 수집 + 경주 당일 실시간 업데이트

---

### 🟡 안건 4: AI 해설 방식

- GPT API 사용 시 비용 이슈 → 유저당 호출 횟수 제한 필요?
- 해설 생성 시점: 레이스 결과 나온 후? 출전 명단 발표 후?
- 스트리밍 방식으로 FE에서 실시간 렌더링할 것인가?

---

## 📅 마일스톤 (✅ 확정)

**개발 시작일: 2026-05-06**

| 단계 | 목표 | 기간 | 예상 완료 |
|------|------|------|---------|
| **Phase 0** | 개발 환경 세팅, DB 스키마, API 연동 테스트, 카카오 앱 등록 | 1주 | 2026-05-13 |
| **Phase 1** | 데이터 수집 파이프라인 + BE API 뼈대 + FE 라우팅 구조 | 2주 | 2026-05-27 |
| **Phase 2** | ML 예측 알고리즘 + Monte Carlo + 시각화 대시보드 | 2주 | 2026-06-10 |
| **Phase 3** | AI 해설 연동 + 정확도 개선 + 디버깅 | 2주 | 2026-06-24 |
| **Phase 4** | 포트폴리오용 문서화, README, 배포 | 1주 | 2026-07-01 |

---

## 📝 액션 아이템

- [x] **ARCH**: 마사회 API 키 발급 완료 (총 21개 확인, 15개 즉시 사용)
- [x] **ARCH**: 데이터 품질 체크리스트 확인 완료 → ML 기반 직행 결정
- [x] **ARCH**: DB 테이블 목록 확정 → ✅ 총 43개 / Phase별 분리 (Phase0 15개 / Phase1 12개 / Phase2 11개 / Phase3 5개)
- [x] **ARCH**: DB 스키마 상세 작성 완료 → V1__phase0.sql (컬럼/인덱스/ENUM/트리거 포함)
- [x] **ARCH**: FastAPI APScheduler + Redis 수집 파이프라인 설계 → ✅ 16개 스케줄 + Rate Limit + 체크포인트 + 결측값 추적 구현 완료
- [ ] **창현님**: ml-server Dockerfile 직접 작성 → Phase 2 첫 번째 태스크
- [ ] **ARCH**: 실제 마사회 API 호출 테스트 → 결측값 비율 + 2019년 구버전 포맷 확인 (Dockerfile 완료 후 진행)
- [x] **BE**: Spring Boot API 엔드포인트 확정 → ✅ 39개 / /api/v1/ 버전 포함 (34→36 카카오 추가 → 38 알림설정 추가 → 39 refresh 추가)
- [x] **BE**: 인증 보안 구조 확정 → ✅ JWT + Rotation + Family 감지 + BCrypt + Rate Limiting
- [x] **BE**: 환경별 설정 분리 확정 → ✅ dev(HTTP) / prod(HTTPS) 프로파일
- [x] **BE**: Spring Boot 프로젝트 세팅 + Security 설정 구현 완료
- [x] **BE**: 카카오 OAuth 2.0 연동 완료 → 07-kakao-oauth-prompt.md 기반 Codex 생성
- [x] **창현님**: 카카오 개발자 센터 앱 등록 + REST API 키 발급 완료
- [ ] **BE**: API 응답에 last_updated / data_status / next_update 필드 포함 설계
- [x] **FE**: 페이지 구조 (라우팅) 초안 작성 완료 → 25개 라우트
- [x] **FE**: 데이터 상태 UI 컴포넌트 설계 (준비중 / 업데이트 예정 / 데이터 수집 중 / 기수변경 뱃지) → DataStatusBadge 구현 + 테스트 완료
- [x] **PM**: Phase 0 상세 일정 수립 완료
- [x] **팀 전체**: 안건 1 확정 → ✅ 선택지 B (Spring Boot 메인, FastAPI 마이크로서비스)
- [x] **팀 전체**: 안건 2 확정 → ✅ ML 기반 직행 (XGBoost/LightGBM, 2019년~데이터 활용)
- [x] **팀 전체**: 안건 3 확정 → ✅ APScheduler 스케줄 수집 (아래 상세 일정 참조)
- [x] **팀 전체**: 안건 4 확정 → ✅ GPT-4o-mini 캐싱, 금/월 해설, 동적 UI 16종, 인트로 영상
- [x] **팀 전체**: 프로젝트명 확정 → ✅ RacePulse
- [x] **팀 전체**: 인트로 영상 방향 변경 → ✅ 시네마틱 실사 / 다크 네이비 + 골드
- [x] **팀 전체**: DB 선택 → ✅ PostgreSQL (윈도우 함수/JSONB/ML 분석 쿼리 이점)
- [x] **팀 전체**: DB 테이블 목록 → ✅ 즉시 25개 확정 (24→25, notification_settings 분리 추가 / Phase 2 이후 4개 별도)
- [x] **FE**: 인트로 영상 제작 → ✅ Veo 3.1 제작 완료 (영상2.mp4 최종 확정)
- [x] **FE**: TypeScript 기반 라우팅 구조 확정 → ✅ 25개 라우트 (목록 확정, /intro는 별도 라우트 아닌 홈의 조건부 렌더링으로 처리)
- [ ] **BE**: GPT-4o-mini 프롬프트 초안 작성 (금요일용 / 월요일용)
- [ ] **BE**: ErrorCode.java + BusinessException.java + GlobalExceptionHandler.java 구현 (API 명세서 작성 선행 조건)
- [x] **팀 전체**: API 공통 응답 포맷 확정 → ✅ ApiResponse<T> (success/data/message) + PageResponse<T>
- [ ] **ARCH**: 마사회 API 실데이터 테스트 결과 공유 (질 점수 / 결측값 비율 / 구버전 포맷 이슈)
- [ ] **ARCH**: Monte Carlo 시뮬레이션 Phase 2 설계 문서 작성
- [x] **PM**: Phase 0 일정 확정 → ✅ 7일 일정
- [x] **창현님**: 카카오 개발자 센터 앱 등록 완료 ✅
- [x] **팀 전체**: Figma 사용 확정 ✅ (DESIGN 주도)
- [x] **팀 전체**: Swagger/OpenAPI 추가 확정 ✅
- [x] **팀 전체**: Git 브랜치 전략 확정 ✅ (main/develop/feature/*)
- [x] **팀 전체**: 로깅 확정 ✅ (SLF4J+Logback 기본 / FastAPI logging)
- [x] **ARCH**: V1__phase0.sql 생성 완료 → `racepulse/backend/src/main/resources/db/migration/V1__phase0.sql` (15개 테이블 + ENUM + 인덱스 + 트리거 + 기본 경마장 데이터)
- [x] **ARCH**: PostgreSQL + Redis Docker 컨테이너 실행 완료 (healthy)
- [x] **ARCH**: FastAPI 프로젝트 생성 완료 (Python 3.13 / FastAPI 0.115.12)
- [x] **ARCH**: /health 정상 응답 확인 → {"status":"UP","service":"RacePulse ML Server"}
- [x] **ARCH**: Swagger 문서 정상 확인 → http://localhost:8000/docs
- [x] **ARCH**: FastAPI DB 연동 확인 완료 → PostgreSQL 16.13 연결 성공
- [x] **ARCH**: 마사회 API 연동 완료 → 05-kra-api-prompt.md 기반 Codex 생성
- [x] **ARCH**: 기상청 API 연동 완료 → 06-weather-api-prompt.md 기반 Codex 생성
- [x] **ARCH**: APScheduler + Redis 파이프라인 완료 → 08-apscheduler-redis-prompt.md 기반 Codex 생성
- [x] **BE**: Spring Boot 프로젝트 생성 완료 (Java 21 / Spring Boot 3.5.14)
- [x] **BE**: SecurityConfig + HealthController 구현 완료
- [x] **BE**: application.yaml / application-dev.yaml / application-prod.yaml 설정 완료
- [x] **BE**: /api/v1/health 정상 응답 확인 → {"status":"UP","service":"RacePulse Backend"}
- [x] **BE**: Swagger UI 정상 확인 → http://localhost:8080/swagger-ui.html
- [x] **BE**: Flyway 베이스라인 설정 완료
- [x] **BE**: 카카오 OAuth 연동 완료 → 07-kakao-oauth-prompt.md 기반 Codex 생성
- [x] **BE**: Web Push 알림 로직 + VAPID 키 설정 완료 → 09-web-push-vapid-prompt.md 기반 Codex 생성
- [x] **FE**: FE-BE API 연동 완료 → 10-fe-api-connect-prompt.md 기반 Codex 생성
- [x] **BE**: 기본 API 엔드포인트 완성 → 02-be-basic-api-prompt.md 기반 Codex 생성 (/api/v1/racecourses, /api/v1/races, /api/v1/horses)
- [x] **FE**: React+TypeScript 프로젝트 생성 완료 (React 18 / Vite / TypeScript)
- [x] **FE**: Tailwind CSS v4 설정 완료 (brand-navy, brand-gold 토큰 포함)
- [x] **FE**: 라우팅 뼈대 25개 완료 → http://localhost:3000 정상 확인
- [x] **FE**: PWA 설정 완료 → 03-pwa-prompt.md 기반 Codex 생성
- [x] **FE**: 홈/경주목록 페이지 뼈대 완료 → 04-home-page-prompt.md 기반 Codex 생성
- [x] **FE**: 인트로 영상 연동 완료 → 01-intro-video-prompt.md 기반 Codex 생성
- [ ] **DESIGN**: Figma 컬러 팔레트 + 디자인 토큰 초안 (Day 5)
- [x] **팀 전체**: 2차 회의 확정 → ✅ DB 스키마 25개 / 폰트(Playfair Display+Inter) / Tailwind brand 토큰 / 프로젝트 세팅 프롬프트 4개
- [x] **FE**: 상세 페이지 구현 완료 → 11-detail-pages-prompt.md 기반 Codex 생성
- [x] **ML**: ML 피처 엔지니어링 완료 → 12-ml-feature-engineering-prompt.md 기반 Codex 생성 (23개 피처)
- [x] **ML**: AI 해설 서비스 완료 → 13-ai-commentary-prompt.md 기반 Codex 생성
- [x] **FE**: 대시보드 페이지 완료 → 14-dashboard-prompt.md 기반 Codex 생성
- [x] **ML**: ML 모델 학습 서비스 완료 → 15-ml-model-training-prompt.md 기반 Codex 생성 (XGBoost/LightGBM)
- [x] **FE**: 예측 결과 페이지 완료 → 16-prediction-page-prompt.md 기반 Codex 생성
- [x] **FE**: 동적 UI 16종 구현 완료 → 17-dynamic-ui-prompt.md 기반 Codex 생성
- [x] **ML**: Monte Carlo 시뮬레이션 완료 → 18-monte-carlo-prompt.md 기반 Codex 생성 (10,000회)
- [x] **FE**: 검색 페이지 완료 → 19-search-page-prompt.md 기반 Codex 생성
- [x] **BE/FE**: 마이페이지 완료 → 20-mypage-prompt.md 기반 Codex 생성 (즐겨찾기/알림/설정)
- [x] **BE**: PredictionController + PredictionService 구현 완료
- [x] **BE**: UserController + UserPageService 구현 완료 (즐겨찾기/설정/알림)
- [x] **BE**: V5__create_user_profile_tables.sql 생성 완료
- [x] **ML**: monte_carlo.py 구현 완료

---

## 💬 회의록

### [날짜: 2026-05-04~05] 킥오프 회의
- **참석**: BE, FE, ARCH, PM, 창현, WR(서기)

---

#### ✅ 안건 1: Spring Boot vs FastAPI 역할 분리 → 선택지 B 확정

- Spring Boot: 인증/인가, 유저 관리, 경주 데이터 저장/조회, REST API 단일 창구
- FastAPI: 마사회 API 데이터 수집 (APScheduler), 예측 연산, AI 해설 생성
- FE는 Spring Boot 단일 창구만 사용 — FastAPI 직접 호출 없음
- ML 전환 시 API 응답 스펙 변경 사전 공유 원칙 합의

---

#### ✅ 안건 2: 예측 알고리즘 기반 방향 → ML 기반 직행 확정

- 마사회 API 데이터 2019년부터 존재 확인 (추정 85,000건 이상)
- 데이터 양/질 모두 ML에 충분 → 통계 MVP 단계 없이 ML 직행
- 채택 모델: XGBoost / LightGBM (트리 기반)
- 예측 결과 화면에 근거 데이터 함께 표시 (예: "최근 3경주 연속 2위")

---

#### ✅ 안건 3: 데이터 수집 파이프라인 → APScheduler 스케줄 수집 확정

**수집 스케줄**

| 시점 | 수집 내용 |
|------|-----------|
| 월요일 오후 14:00 | 주말 경기 결과 |
| 화요일 오전 09:00 | 월요일 경기 결과 (있는 경우) |
| 목요일 오전 10:00 | 주말 출전표 초안 |
| 목요일 오후 17:30 | 출전표 업데이트 확인 |
| 금요일 오전 08:00 | 출전표 확정본 |
| 토요일 오전 09:05 | 마체중+증감, 기수변경, 트랙 상태 |
| 일요일 오전 09:05 | 마체중+증감, 기수변경, 트랙 상태 |
| 월요일 오전 09:05 | 마체중+증감, 기수변경, 트랙 상태 (있는 경우) |
| 주 1회 | 경주마명단, 경주마 레이팅 |
| 월 1회 | 기수/조교사/마필/진료 정보 |

**안전장치**
- APScheduler + Redis 카운터/체크포인트 관리
- 지수 백오프 재시도 5회 (5분→15분→30분→1시간→3시간)
- 일 3,000콜 → 2,800콜 도달 시 자동 중단, 다음 스케줄 이어서 수집
- Rate Limit 카운터 자정(00:00) 리셋

**유저 화면 데이터 상태 표시**

| 상태 | 화면 표시 |
|------|-----------|
| 수집 전 (스케줄 대기) | 준비중 |
| 다음 수집까지 대기 | 업데이트 예정 |
| 실제 수집 진행 중 | 데이터 수집 중 |
| 기수 교체 발생 | 기수변경 뱃지 표시 |

**API 응답 공통 필드**: `last_updated` / `data_status` / `next_update`

---

#### ✅ 안건 4: AI 해설 방식 → 전체 확정

**GPT 모델 및 비용 관리**
- 모델: GPT-4o-mini 시작 → 품질 부족 시 GPT-4o 업그레이드
- 비용 관리: 사전 생성 + Redis 캐싱 (경주당 최대 2회 호출로 고정)
- 캐시 키: `pre_race:{meet}:{rc_date}:{race_no}` / `post_race:{meet}:{rc_date}:{race_no}`

**렌더링 방식**
- 스트리밍 제거 → FE 타이핑 애니메이션으로 대체 (모든 유저 동일 경험)
- 실제 수집은 APScheduler가 자동 처리 — 유저 요청과 GPT 호출 완전 분리

**해설 생성 시점 (2종)**

| 시점 | 생성 시각 | 내용 |
|------|-----------|------|
| 사전 해설 | 금요일 08:00 (출전표 확정 후 자동) | 출전마 심층 분석 + 관전 포인트 |
| 결과 해설 | 월요일 14:00 (경기 결과 수집 후 자동) | 경기 드라마 + 예측 복기 + 다음 주 예고 |

**금요일 사전 해설 구성 (600~1000자)**
- 오늘의 핵심 변수 (트랙/날씨/거리)
- 말별 심층 프로필: 강점/약점/기수 콤비 히스토리/컨디션 등급(최하~최상)/예상 기록 범위/"이길 수 있는 시나리오"
- 5대 궁금증 해소: 트랙 적합성 / 기수-말 궁합 / 최근 폼 / 역사적 패턴 / 다크호스 분석
- 이번 경주 관전 포인트 + 이변 가능성

**월요일 결과 해설 구성 (800~1200자)**
- 이변 지수 (Upset Meter) — 배당률 기반 이변 정도 수치화
- 경기 하이라이트 + 결정적 구간 분석
- ML 예측 vs 실제 결과 복기 (틀렸다면 이유 솔직하게)
- 역대 기록과 비교 (이 트랙/거리 역대 몇 위)
- 카운터팩추얼 분석 ("만약 기수 변경이 없었다면?")
- 라이벌 구도 업데이트 (상대 전적 갱신)
- 다음 주 예고 + 복수전 예고

**사행성 방지 (시스템 프롬프트 고정)**
- 절대 금지: "베팅 추천", "이 말에 투자", "확실한 1위"
- 필수 포함: "데이터 기준", "통계적으로", "참고용 분석"
- 하단 고정 면책 문구: "본 해설은 순수 데이터 분석 목적이며, 베팅 등 사행 행위와 무관합니다."

**FE 동적 UI (16종)**
1. 컨디션 게이지 애니메이션 (최하~최상 차오르는 효과)
2. 예측 승률 바 차트 스윕 애니메이션
3. 말 카드 호버 시 상세 스탯 팝업 + 미니 성적 차트
4. 컨디션 등급 색상 코딩 (빨강→주황→노랑→연두→초록)
5. 레이팅 레이더 차트 (5각형, 호버 시 회전)
6. 말 카드 게이트 열리듯 순서대로 슬라이드 인
7. 경주 시뮬레이션 미니 애니메이션 (Monte Carlo 연동, Phase 2)
8. 성적 추이 스파크라인 (최근 5경주, 상승/하락 색상)
9. 착순 역순 공개 애니메이션 (5위→1위)
10. 구간별 기록 라인 차트 (페이스 곡선 비교)
11. 예측 vs 실제 비교 게이지
12. 예측 정확도 대시보드 원형 게이지 + 카운트업
13. 다음 수집까지 카운트다운
14. 경기 시작까지 카운트다운
15. AI 해설 타이핑 애니메이션
16. 로딩 화면: 말 달리기 → 결승선 통과 → 트로피 등장

**인트로 영상 (최초 접속 1회) ✅ 확정**
- 영상: 영상2 확정 (6초, MP4, 6.4MB 원본 사용)
- 포맷: MP4 (압축 없이 원본 그대로)
- 스타일: 시네마틱 실사 — 정면 돌진 오프닝 → 황금빛 질주 → 모션블러 전환 → 엔딩 슬레이트
- 엔딩 슬레이트: 다크 네이비 + 골드 말 로고 + "RacePulse" + "Made by Changhyun Ahn"
- 재방문: localStorage → 자동 스킵
- 이전 방향 폐기: ~~귀여운 소형 말 타원 트랙 애니메이션~~

**인트로 영상 끊김 방지 구현 (처음부터 적용)**
- `poster` 속성: 영상 1/197 프레임 정지 이미지 → 검은 화면 없음
- `canplaythrough` 이벤트: 완전 버퍼링 완료 후에만 재생 시작
- `preload="auto"`: 페이지 진입 즉시 백그라운드 로딩
- 골드 프로그레스 바: 로딩 진행률 시각화
- 10초 타임아웃: 느린 환경에서 자동 스킵 → 메인 전환
- `onEnded`: 재생 완료 시 메인 페이지 자연스럽게 전환

**예측 정확도 검증**
- 개발 단계: 2019~2024 학습 / 2025 백테스팅
- 운영 단계: 매 경기 후 예측 vs 실제 자동 비교 + 누적 정확도 DB 저장
- 기준: Top-3 정확도 60% 미만 → 피처 재검토 / 70% 이상 → Phase 2 진행
- 대시보드에 누적 적중률 공개 표시

**Monte Carlo — Phase 2 적용 계획**
- ML 예측값을 확률 분포로 변환 → 10,000회 시뮬레이션
- 각 말의 순위별 확률 산출 (예: 1위 34%, 2위 28%)
- 컨디션 등급 범위 수치화 + 이변 확률 계산
- FE 레이스 시뮬레이션 애니메이션 데이터 소스로 활용

---

## 🗄️ DB 설계 확정

### DB 선택: PostgreSQL
- MariaDB/MySQL 대비 윈도우 함수, JSONB, 복잡한 분석 쿼리에 유리
- ML 피처 계산 (이동평균, 순위 계산 등) 에 실질적 이점
- Spring Boot JPA dialect만 변경, 코드는 MariaDB와 동일
- 포트폴리오 임팩트 높음 (선택 이유가 프로젝트 목적과 연결)

### 전체 테이블 — 43개 (창현님 확정 / Phase별 분리)

> 최초 25개 → 논의 끝에 55개 제안 → 통합/제거 후 43개 확정
> Flyway 마이그레이션 도구 사용: V1~V4 파일로 Phase별 관리

---

#### 🟢 Phase 0 — 즉시 생성 (15개) `V1__phase0.sql`

| # | 테이블 | 비고 |
|---|--------|------|
| 1 | `horses` | 말 마스터 + coat_color, photo_url, thumbnail_url 컬럼 포함 |
| 2 | `jockeys` | 기수 마스터 |
| 3 | `trainers` | 조교사 마스터 |
| 4 | `racecourses` | 경마장 마스터 |
| 5 | `races` | 경주 + race_class, race_grade, pace 컬럼 포함 |
| 6 | `race_entries` | 출전명단 + is_debut, is_comeback, rest_days, class_change, distance_change 컬럼 포함 |
| 7 | `race_results` | 경주 결과 |
| 8 | `track_conditions` | 트랙 상태 |
| 9 | `horse_weight_history` | 마체중 이력 |
| 10 | `jockey_changes` | 기수변경 이력 |
| 11 | `weather_forecasts` | 날씨 예보 |
| 12 | `collection_logs` | 수집 로그 + null_count, anomaly_count, quality_score, quality_status 컬럼 포함 |
| 13 | `users` | 유저 |
| 14 | `user_preferences` | 설정 + theme DEFAULT 'dark' 포함 |
| 15 | `refresh_tokens` | JWT Refresh Token 보안 관리 |

---

#### 🟡 Phase 1 — 서비스 오픈 전 (12개) `V2__phase1.sql`

| # | 테이블 | 비고 |
|---|--------|------|
| 16 | `predictions` | ML 예측 결과 |
| 17 | `prediction_accuracy_logs` | 예측 정확도 추적 |
| 18 | `model_versions` | ML 모델 버전 관리 |
| 19 | `ai_commentary` | AI 해설 (PRE/POST) |
| 20 | `odds_history` | 배당률 이력 + opening/intermediate/final/movement_rate 컬럼 포함 |
| 21 | `favorites` | 즐겨찾기 |
| 22 | `user_views` | 조회 이력 |
| 23 | `notification_settings` | 알림 설정 (유형별) |
| 24 | `push_subscriptions` | Web Push VAPID 구독 정보 |
| 25 | `entry_cancellations` | 출전 취소 이력 |
| 26 | `race_payouts` | 경주 후 실제 환수금 |
| 27 | `system_event_log` | 시스템 이벤트 통합 로그 |

---

#### 🔵 Phase 2 — ML 고도화 (11개) `V3__phase2.sql`

| # | 테이블 | 비고 |
|---|--------|------|
| 28 | `horse_breakdown_stats` | 거리/조건/코스/중량별 말 성적 통합 (stat_type 구분) |
| 29 | `combination_stats` | 기수-말 / 조교사-말 조합 성적 통합 |
| 30 | `participant_form_stats` | 기수/조교사 최근 30/60/90일 폼 통합 |
| 31 | `horse_form_index` | 말 최근 폼 점수 (가중 계산) |
| 32 | `horse_running_style` | 말별 주행 스타일 (선두/중간/추입) |
| 33 | `gate_bias_stats` | 경마장별 게이트 편향 통계 |
| 34 | `ml_feature_store` | 예측용 피처 사전 계산 저장 (JSONB) |
| 35 | `feature_importance_log` | ML 피처 중요도 기록 |
| 36 | `equipment_changes` | 블링커 등 장비 변경 이력 |
| 37 | `rival_records` | 말간 직접 대결 이력 |
| 38 | `horse_pedigree` | 혈통 정보 (sire_id/dam_id FK) |

---

#### 🟣 Phase 3 — 완성도 (5개) `V4__phase3.sql`

| # | 테이블 | 비고 |
|---|--------|------|
| 39 | `horse_clinic` | 말 진료/부상 이력 |
| 40 | `horse_ratings_history` | 레이팅 변동 이력 |
| 41 | `race_highlight_moments` | 이변/기록/DQ 등 하이라이트 이벤트 |
| 42 | `search_keywords` | 인기 검색어 집계 |
| 43 | `api_rate_limit_log` | API 일별 사용량 이력 |

---

### 통합/제거 처리 내역

| 처리 | 원래 테이블 | 결과 |
|------|------------|------|
| 통합 | horse_stat_by_distance + horse_stat_by_condition + horse_course_stats + weight_performance_stats | → `horse_breakdown_stats` |
| 통합 | jockey_horse_stats + trainer_horse_stats | → `combination_stats` |
| 통합 | jockey_form_stats + trainer_form_stats | → `participant_form_stats` |
| 컬럼 흡수 | odds_movement_log | → `odds_history`에 포함 |
| 컬럼 흡수 | pace_scenario | → `races`에 포함 |
| 컬럼 흡수 | race_entry_flags | → `race_entries`에 포함 |
| 컬럼 흡수 | horse_visual_profile | → `horses`에 포함 |
| 컬럼 흡수 | data_collection_health | → `collection_logs`에 포함 |
| 제거 | schema_change_log | Flyway가 대체 |
| 제거 | race_class_movement_history | race_entries + races로 도출 가능 |

### 날씨 데이터
- 기상청 단기예보 + 중기예보 API (data.go.kr, 이미 신청 완료)
- API허브/기상자료개방포털 추가 신청 불필요

---

## 🔌 BE API 엔드포인트 확정 (39개)

> 2차 회의 재점검으로 34→36(카카오 2개 추가) → 38(알림설정 2개 추가) → 39(refresh 1개 추가)

### 버전: /api/v1/ 전체 적용

| # | 분류 | 메서드 | 엔드포인트 | 권한 |
|---|------|--------|-----------|------|
| 1 | **인증** | POST | /auth/register | GUEST |
| 2 | | POST | /auth/login | GUEST |
| 3 | | POST | /auth/logout | USER |
| 4 | | GET  | /auth/me | USER |
| 5 | | POST | /auth/refresh | GUEST |
| 6 | | GET  | /auth/kakao | GUEST |
| 7 | | GET  | /auth/kakao/callback | GUEST |
| 8 | **경주** | GET | /races | GUEST |
| 9 | | GET | /races/{id} | GUEST |
| 10 | | GET | /races/{id}/full | GUEST |
| 11 | | GET | /races/upcoming | GUEST |
| 12 | | GET | /races/results | GUEST |
| 13 | **경주마** | GET | /horses | GUEST |
| 14 | | GET | /horses/{id} | GUEST |
| 15 | | GET | /horses/{id}/history | GUEST |
| 16 | **기수/조교사** | GET | /jockeys/{id} | GUEST |
| 17 | | GET | /trainers/{id} | GUEST |
| 18 | **예측/AI해설** | GET | /predictions/{raceId} | GUEST |
| 19 | | GET | /commentary/{raceId}/pre | GUEST |
| 20 | | GET | /commentary/{raceId}/post | GUEST |
| 21 | **경마장/날씨** | GET | /racecourses | GUEST |
| 22 | | GET | /racecourses/{meetCode} | GUEST |
| 23 | | GET | /weather/{meetCode}/{date} | GUEST |
| 24 | **검색/홈** | GET | /search | GUEST |
| 25 | | GET | /home | GUEST |
| 26 | **대시보드** | GET | /dashboard/accuracy | GUEST |
| 27 | | GET | /dashboard/weekly | GUEST |
| 28 | **유저** | GET | /user/favorites | USER |
| 29 | | POST | /user/favorites | USER |
| 30 | | DELETE | /user/favorites/{id} | USER |
| 31 | | GET | /user/history | USER |
| 32 | | PATCH | /user/preferences | USER |
| 33 | **알림설정** | GET | /user/notifications | USER |
| 34 | | PATCH | /user/notifications/{type} | USER |
| 35 | **관리자** | GET | /admin/collection/** | ADMIN |
| 36 | | POST | /admin/collection/** | ADMIN |
| 37 | | GET | /admin/model/accuracy | ADMIN |
| 38 | | POST | /admin/commentary/regenerate | ADMIN |
| 39 | **헬스체크** | GET | /health | GUEST |

### 인증 보안 구조

```
JWT 설정
─────────────────────────────────────────────────
Access Token   1시간
Refresh Token  24시간 기본 / 로그인 유지 선택 시 3일

보안 3종 조합
─────────────────────────────────────────────────
✅ Refresh Token Rotation (1회용, 사용 시 즉시 폐기)
✅ Token Family 탈취 감지 (재사용 시 전체 세션 폐기)
✅ Redis 블랙리스트 + 유효 토큰 관리

추가 보안
─────────────────────────────────────────────────
✅ 로그인 5회 실패 → 15분 잠금 (Rate Limiting)
✅ BCrypt strength 10 비밀번호 해싱
✅ Cookie: HttpOnly + Secure + SameSite=Strict
✅ JWT 페이로드 최소화 (userId + role만)
✅ CORS 허용 도메인 제한
⚠️ IP 변경 감지 → 알림만 (강제 차단 아님)
```

### 환경별 설정 분리

```
dev 프로파일 (개발 중)
─────────────────────────────────────────────────
Secure=false / SameSite=Lax / CORS: localhost:3000

prod 프로파일 (배포 후)
─────────────────────────────────────────────────
Secure=true / SameSite=Strict / CORS: racepulse.com

전환: spring.profiles.active=dev|prod 한 줄 변경
```

### 카카오 연동

```
인증: 이메일 로그인 + 카카오 OAuth 2.0 병행
결제: 포트원 (PortOne) — Freemium 도입 시 연동 (KakaoPay 대신 포트원으로 확정)

카카오 로그인 엔드포인트 추가
─────────────────────────────────────────────────
GET /api/v1/auth/kakao           카카오 로그인 시작
GET /api/v1/auth/kakao/callback  카카오 OAuth 콜백

users 테이블 변경
─────────────────────────────────────────────────
kakao_id      VARCHAR  (nullable, 카카오 유저 식별자)
auth_provider ENUM('LOCAL','KAKAO')
password      nullable (카카오 유저는 없음)
tier          VARCHAR DEFAULT 'FREE' (Freemium 여지)

JWT 페이로드
─────────────────────────────────────────────────
userId / role / tier / exp
```

```
준비 필요
─────────────────────────────────────────────────
[ ] 카카오 개발자 센터 (developers.kakao.com) 앱 등록
[ ] REST API 키 발급
[ ] Redirect URI 등록
```

---

---

## 🔜 다음 회의 안건 (3차 회의)

| 우선순위 | 안건 | 담당 |
|----------|------|------|
| 🔴 | 노션 담당자 온보딩 (역할 설명 + 노션 워크스페이스 구조 설계) | NOTION + 팀 전체 | ✅ 완료 |
| 🔴 | 마사회 API 실제 데이터 수집 현황 점검 (결측값/포맷 체크) | ARCH | ✅ 완료 (실테스트는 프롬프트 20번 후) |
| 🔴 | ML 모델 정확도 결과 공유 → Phase 2 진행 여부 결정 (60%/70% 기준) | ARCH | ⏸️ 저녁 후 재개 |
| 🔴 | GitHub Repository 브랜치 전략 실제 운영 시작 (develop/feature/* 적용) | GIT | ✅ 완료 |
| 🟡 | Figma 컬러 팔레트 + 와이어프레임 초안 공유 | DESIGN | ⏸️ 대기 |
| 🟡 | 동적 UI 16종 우선순위 분류 (Phase 2 필수 vs 나중) | FE | ⏸️ 대기 |
| 🟡 | 인트로 영상 최종 확정 (영상2.mp4 확정 or Veo 3.1 재시도) | FE | ⏸️ 대기 |
| 🟡 | AWS 배포 환경 사전 논의 (EC2/RDS 구조, 도메인, SSL) | ARCH | ⏸️ 대기 |
| 🟢 | 코드 리뷰 프로세스 + PR 기준 확정 | GIT + 팀 | ⏸️ 대기 |
| 🟢 | Freemium / 포트원 결제 도입 시점 논의 | PM | ⏸️ 대기 |

---

## 🔑 외부 API 사용 목록 (✅ 창현님 확정)

| # | API | 용도 | .env 키 | 상태 |
|---|-----|------|---------|------|
| 1 | **한국마사회 API** | 경주 데이터 수집 (15개 즉시 사용) | `KMA_API_KEY` | ✅ 기입 완료 |
| 2 | **기상청 API** | 단기/중기 날씨 예보 | `WEATHER_API_KEY` | ✅ 기입 완료 |
| 3 | **카카오 OAuth 2.0** | 소셜 로그인 + 회원가입 | `KAKAO_CLIENT_ID` / `KAKAO_CLIENT_SECRET` | ✅ 기입 완료 |
| 4 | **OpenAI GPT API** | AI 해설 생성 (GPT-4o-mini) | `OPENAI_API_KEY` | ✅ 기입 완료 |
| 5 | **포트원 (PortOne)** | 결제 — Freemium 도입 시 연동 | `PORTONE_API_KEY` / `PORTONE_SECRET` | ⏳ 도입 시 추가 |

> KakaoPay → 포트원으로 변경 확정 (창현님 결정)

---

## 📡 마사회 API 활용 목록 (총 21개 검토)

### ✅ 즉시 사용 — 15개

**🔴 핵심 수집**

| API | 수집 주기 | 주요 피처 |
|-----|-----------|-----------|
| 출전표 상세정보 | 목/금 | 부담중량, 기수, 조교사, 성적 통계 |
| 경주성적 정보 | 월/화 (결과) | 구간기록, 착순, 마체중 |
| 경주마 성적 정보 | 월 1회 | 통산/최근 1년 승률 |
| 경주마명단 | 주 1회 | 마스터 데이터, 레이팅1~4, 출전여부 |
| 경주마 레이팅 정보 | 주 1회 | 레이팅 최신값 보장 (명단과 병행) |
| 출전마 체중 정보 | 토/일/월 09:05 | 마체중, 증감 |
| 기수변경 정보 | 토/일/월 09:05 | 당일 기수 교체 감지 |
| 경주로 정보 | 토/일/월 09:05 | 트랙 함수율 (건조/습윤/다습/포화) |

**🟡 보조 수집**

| API | 수집 주기 | 주요 피처 |
|-----|-----------|-----------|
| 기수 성적 정보 | 월 1회 | 기수 통산/최근 승률 |
| 기수 상세정보 | 월 1회 | 기능가능 소속조/타조 중량 |
| 조교사 상세정보 | 월 1회 | 조교사 통산/최근 승률 |
| 환수배당률 통합정보 | 목/금 | 단승/복승/연승/삼복승 배당률 |
| 마필종합 상세정보 | 월 1회 | 혈통, 부마/모마 정보 |
| 경주계획표 | 월 1회 | 경주 일정 관리 |
| 마필진료 정보 | 월 1회 | 부상 이력 |

### ⏳ Phase 2 이후 검토 — 3개

| API | 이유 |
|-----|------|
| 일별훈련 상세정보 | 매일 수집 필요 — Rate Limit 부담 |
| 경주 구간별 성적 정보 | RaceDetailResult_1로 MVP 먼저 |
| 주행심사 상세결과 | 데뷔/복귀마 한정 — MVP 범위 밖 |

### ❌ 제거 — 3개

| API | 이유 |
|-----|------|
| 경주기록 정보 | 경주성적 정보와 중복 |
| 경주마 상세정보 | 경주마명단 + 마필종합으로 커버 |
| 경마경주정보 | 경주계획표와 역할 중복 |

---

---

### [날짜: 2026-05-08] 2차 회의
- **참석**: BE, FE, ARCH, PM, DESIGN(신규), 창현님, WR

#### ✅ 안건 1: DESIGN 온보딩 + 디자인 방향 확정

- **폰트**: Playfair Display (heading/title) + Inter (body) — Google Fonts 적용
- **Tailwind 토큰 네임스페이스**: `colors.brand.*`
  - `brand-navy-950 / brand-navy-900 / brand-navy-800` (배경 계열)
  - `brand-gold-400 / brand-gold-500 / brand-gold-600` (골드 계열)
  - `brand-white / brand-gray-*` (텍스트/보조)
- DESIGN → Figma 컬러 팔레트 + 토큰 초안 Day 5까지 업로드

---

#### ✅ 안건: 사이트 기본 톤 + 주야간 모드 확정

**인트로 영상 흐름 확인** (영상2.mp4 캡처 검토)
- 1/197: 정면 돌진 오프닝 — 밝은 황금빛, 경마장 관중석
- 25~60/197: 황금빛 질주 → 클로즈업 모션블러
- 138/197: 강한 모션블러 전환
- 155/197: 엔딩 슬레이트 — 다크 네이비 + 골드 → 이 화면에서 메인 페이지로 전환

**✅ 창현님 확정**

| 항목 | 결정 |
|------|------|
| 기본 사이트 톤 | **다크 모드** 기본 |
| 라이트(주간) 모드 | **토글 옵션 포함** — 유저가 선택 전환 가능 |
| 자동 주/야간 전환 | **없음** |
| poster 이미지 | `intro-poster.jpg` (1/197 프레임, 정면 돌진 장면) — 파일 존재 확인 완료 |
| DB 대응 | `user_preferences.theme VARCHAR DEFAULT 'dark'` 컬럼 포함 |

---

#### ✅ 안건 2: DB 스키마 확정 — 25개 테이블

**테이블 수 변경**: 24개 → 25개 (`notification_settings` 독립 테이블로 분리)

**마스터 (4개)**
- `horses`: id, name, eng_name, birth_year, sex, color, origin, father_name, mother_name, owner, meet_code(VARCHAR2+CHECK), rating_1~4, is_active, created_at, updated_at
- `jockeys`: id, name, eng_name, meet_code, license_no, win_rate_total, win_rate_recent, place_rate_total, is_active, created_at, updated_at
- `trainers`: id, name, eng_name, meet_code, license_no, win_rate_total, win_rate_recent, is_active, created_at, updated_at
- `racecourses`: id, meet_code(SC/BU/JJ), name, location, track_types(JSONB), created_at

**경주 (3개)**
- `races`: id, meet_code, rc_date, race_no, race_name, distance, track_type, track_condition, prize_money, weather, start_time, status(ENUM: SCHEDULED/COMPLETED/CANCELLED), created_at, updated_at
- `race_entries`: id, race_id(FK), horse_id(FK), jockey_id(FK), trainer_id(FK), gate_no, burden_weight, horse_weight, horse_weight_diff, rating, odds_win, odds_place, data_status(ENUM: READY/UPDATING/COLLECTED/JOCKEY_CHANGED), created_at, updated_at
- `race_results`: id, race_id(FK), horse_id(FK), race_entry_id(FK), rank, record_time, margin, section_1~6(VARCHAR), created_at

**이력 (7개)**
- `track_conditions`: id, race_id(FK), meet_code, rc_date, moisture_rate, condition(ENUM: DRY/WET/HUMID/SATURATED), recorded_at
- `horse_weight_history`: id, horse_id(FK), race_id(FK), rc_date, weight, weight_diff, recorded_at
- `jockey_changes`: id, race_entry_id(FK), race_id(FK), horse_id(FK), prev_jockey_id(FK), new_jockey_id(FK), changed_at, reason
- `entry_cancellations`: id, race_id(FK), horse_id(FK), race_entry_id(FK), reason, cancelled_at
- `horse_clinic`: id, horse_id(FK), diagnosis, treatment, clinic_date, return_expected_date, created_at
- `horse_ratings_history`: id, horse_id(FK), rating_1~4, recorded_date, created_at
- `odds_history`: id, race_entry_id(FK), race_id(FK), odds_win, odds_place, odds_quinella, recorded_at

**날씨 (1개)**
- `weather_forecasts`: id, meet_code, forecast_date, temp_min, temp_max, precipitation_prob, wind_speed, condition, source, created_at, updated_at

**ML/AI (4개)**
- `predictions`: id, race_id(FK), horse_id(FK), race_entry_id(FK), model_version_id(FK), predicted_rank, win_probability, place_probability, feature_snapshot(JSONB), created_at
- `prediction_accuracy_logs`: id, race_id(FK), model_version_id(FK), top1_correct(BOOL), top3_correct(BOOL), predicted_rank, actual_rank, created_at
- `model_versions`: id, version_name, algorithm(XGBoost/LightGBM), features_used(JSONB), hyperparams(JSONB), train_period_start, train_period_end, accuracy_top1, accuracy_top3, is_active(BOOL), created_at
- `ai_commentary`: id, race_id(FK), type(ENUM: PRE/POST), content(TEXT), model_used, cache_key, generated_at, created_at

**수집 (1개)**
- `collection_logs`: id, api_name, meet_code, rc_date, status(ENUM: SUCCESS/FAILED/PARTIAL/SKIPPED), records_collected, error_message, daily_call_count, collected_at

**유저 (5개)**
- `users`: id(UUID), email, password(nullable), kakao_id(nullable), auth_provider(ENUM: LOCAL/KAKAO), nickname, role(ENUM: USER/ADMIN), tier(ENUM: FREE/PRO DEFAULT FREE), is_active, last_login_at, created_at, updated_at
- `favorites`: id, user_id(FK), target_type(ENUM: HORSE/JOCKEY/RACE), target_id, created_at — UNIQUE(user_id, target_type, target_id)
- `user_views`: id, user_id(FK), target_type, target_id, viewed_at
- `user_preferences`: id, user_id(FK UNIQUE), default_meet_code, notification_enabled, preferred_language(DEFAULT 'ko'), theme(DEFAULT 'dark'), updated_at
- `notification_settings`: id, user_id(FK), type(ENUM: RACE_START/JOCKEY_CHANGE/RESULT), is_enabled, created_at, updated_at

---

---

---

### [날짜: 2026-05-11] 3차 회의
- **참석**: BE, FE, ARCH, PM, DESIGN, GIT, NOTION, WR, 창현님

#### ✅ 안건 0: NOTION 온보딩 + 노션 자동 동기화 루틴 설정

- 노션 워크스페이스 확정: https://www.notion.so/Racepulse-35de61ba917a80bfa329dc8acb7466ad
- NOTION 첫 작업: API 명세서 우선 진행
- 노션 자동 동기화 루틴 생성 완료 (매일 오전 2:00 KST / `trig_01GazhAkKvfekaPcVEUw22qF`)
  - `horse_racing_team.md` 기반 자동 정리
  - 대상: 회의록 / API 명세서 / DB 스키마 / 스프린트 대시보드
- 노션 페이지 구조 확정:
  ```
  RacePulse/
  ├── 📋 회의록/
  ├── 🔌 API 명세서/
  ├── 🗄️ DB 스키마/
  ├── 🎨 디자인 시스템/
  ├── 🧩 컴포넌트 라이브러리/
  ├── 🐛 버그/이슈 트래킹/
  ├── 📊 스프린트 대시보드/
  ├── 🚀 배포 이력/
  └── 📁 포트폴리오/
  ```

#### ✅ API 공통 응답 포맷 + 에러코드 체계 확정

**공통 응답 포맷** (`ApiResponse<T>` — 이미 구현됨)
```json
{ "success": true, "data": { ... }, "message": "..." }
```
**페이징 응답** (`PageResponse<T>` — 이미 구현됨)
```json
{ "content": [...], "page": 0, "size": 20, "totalElements": 100, "totalPages": 5, "last": false }
```

**에러코드 목록 확정**
```
// 인증
TOKEN_EXPIRED, TOKEN_INVALID, LOGIN_FAILED, ACCOUNT_LOCKED

// 경주/말
RACE_NOT_FOUND, HORSE_NOT_FOUND, JOCKEY_NOT_FOUND

// 유저
USER_NOT_FOUND, DUPLICATE_EMAIL, UNAUTHORIZED

// 데이터
DATA_NOT_READY, COLLECTION_IN_PROGRESS
```

**BE 구현 필요 파일**
- `ErrorCode.java` — 에러코드 enum
- `BusinessException.java` — 커스텀 예외 베이스 클래스
- `GlobalExceptionHandler.java` — `@RestControllerAdvice` 전역 예외처리

**data_status ENUM 확정**: `READY / UPDATING / COLLECTED / JOCKEY_CHANGED` → NOTION 명세서 반영

#### ✅ 안건 3: ML 모델 정확도 → Phase 2 진행 여부

- 프롬프트 11~20 모두 완료 확인 (ML 피처 23개 / XGBoost+LightGBM / Monte Carlo 10,000회)
- ml-server Dockerfile 미생성 → Docker 기동 불가 → 실제 학습/정확도 측정 불가
- **결정**: 창현님이 회의 후 Dockerfile 직접 작성 → Docker 기동 → 실데이터 수집 → 모델 학습 순서로 진행
- Phase 2 진행 기준 유지: Top-3 정확도 60% 미만 → 피처 재검토 / 70% 이상 → Phase 2 진행

#### ✅ 안건 4: GitHub 브랜치 전략 실제 운영 시작

- **현황**: main 브랜치만 존재, develop/feature/* 없음
- **솔로 개발 맞춤 조정 확정**:
  - 브랜치 구조: `main / develop / feature/* / hotfix/*` 유지
  - main 직접 push: **금지** (포트폴리오용 PR 이력 유지)
  - develop 직접 push: **허용** (혼자 작업)
  - PR 승인자: **생략** (셀프 머지)
  - 머지 방식: **Squash merge** (main 이력 깔끔하게)
- **GIT 액션**: develop 브랜치 생성 + GitHub Branch Protection Rule 설정 + PR 템플릿 생성

---

#### ✅ 안건 2: 마사회 API 실데이터 수집 현황 점검

**파이프라인 구현 상태 확인**
- 마사회 API 3개 엔드포인트 구현 완료 (경주계획표 / 출전표 / 경주결과)
- APScheduler 16개 스케줄 등록 완료
- Redis Rate Limit (일 3,000콜 / 2,800 자동 중단) + 체크포인트 복구 구현 완료
- 결측값 품질 점수 기준 확정: GOOD(85↑) / WARNING(60~84) / CRITICAL(60↓)

**미확인 항목 (실API 테스트 필요)**
- 결측값 실제 비율
- 2019년 구버전 데이터 포맷 일관성

**테스트 방법**: Docker 실행 → 실제 API 호출 → `GET /collection/status` 조회

---

#### ✅ 팀 구성 변경 (창현님 확정)

- **Git 관리자 (GIT) 신규 추가** — 브랜치 전략, PR 관리, CI/CD, 버전 관리, Git 가이드 문서화 담당
- **노션 담당자 (NOTION) 신규 추가** — API 명세/DB 스키마/컴포넌트/디자인시스템/버그트래킹/스프린트/배포이력/포트폴리오 문서화 담당
- **Terraform/AWS 인프라 역할** — Phase 4 시점에 별도 역할 재논의
- **총 팀 구성**: BE / FE / ARCH / PM / WR / DESIGN / GIT / NOTION — 8명 체제 확정

---

#### ✅ 외부 API 확정 (창현님 확정)

- 마사회 / 기상청 / 카카오 OAuth / OpenAI GPT — .env 기입 완료
- 결제: KakaoPay → **포트원(PortOne)** 으로 변경, Freemium 도입 시 연동

---

#### ✅ 재점검: 전체 확정사항 재검토 (2026-05-08)

**API 엔드포인트 수정** (34 → 39개)
- 카카오 OAuth 2개: GET /auth/kakao, GET /auth/kakao/callback
- 알림설정 2개: GET /user/notifications, PATCH /user/notifications/{type}
- Refresh Token 1개: POST /auth/refresh
- 상세 목록은 "BE API 엔드포인트 확정" 섹션 참고

**DB 테이블 수정**
- `odds_history`: Phase 2 이후 → 즉시 생성 테이블로 이동 (ML 피처 활용 가능)
- Phase 2 이후 테이블: 4개 → 3개 (`horse_training_logs / race_sectional_detail / search_history`)

**FE 25개 라우트 목록 확정**

| 분류 | 라우트 |
|------|--------|
| **공개** | /, /races, /races/:raceId, /races/:raceId/entries, /races/:raceId/result, /races/:raceId/prediction, /races/:raceId/commentary |
| **경주마/기수/조교사** | /horses, /horses/:horseId, /horses/:horseId/history, /jockeys/:jockeyId, /trainers/:trainerId |
| **경마장** | /racecourses, /racecourses/:meetCode |
| **대시보드/검색** | /dashboard, /dashboard/weekly, /search |
| **인증** | /login, /register, /auth/kakao/callback |
| **로그인 필요** | /profile, /favorites, /settings |
| **관리자** | /admin, /admin/collection |

> 인트로 영상은 별도 라우트 없음 — `/` (홈) 진입 시 localStorage 체크 후 조건부 렌더링

**인트로 영상 구현 스펙 재확인 ✅**
- 파일: `영상2.mp4` (6초 / 6.4MB / MP4 원본)
- poster: `intro-poster.jpg` (파일 존재 확인 완료)
- 끊김 방지: canplaythrough + preload="auto" + 골드 프로그레스 바 + 10초 타임아웃 + onEnded
- 엔딩 슬레이트: 다크 네이비 + 골드 + "RacePulse" + "Made by Changhyun Ahn"

---

#### ✅ DB 테이블 최종 확정 — 43개 Phase별 분리 (창현님 확정)

- 전체 제안 55개 → 통합/제거 후 **43개** 확정
- **Flyway** 마이그레이션 도구 도입 확정 (Spring Boot 의존성 추가)
- Phase 0 (15개) → Phase 1 (12개) → Phase 2 (11개) → Phase 3 (5개)
- 상세 목록은 "DB 설계 확정" 섹션 참고

---

#### ✅ 안건 3~5: 오늘 실행할 프롬프트 4개 확정

**프롬프트 #1 — DB 스키마 (init.sql)**
> PostgreSQL 25개 테이블 CREATE TABLE SQL + ENUM type + 인덱스 + 외래키 + created_at DEFAULT NOW() + updated_at 트리거. 파일명: init.sql

**프롬프트 #2 — Spring Boot 프로젝트 생성**
> Java 21 / Spring Boot 3.x / 의존성: Web, Security, JPA, QueryDSL, PostgreSQL, Redis, Actuator, Validation, jjwt, Lombok, MapStruct, SpringDoc OpenAPI / domain 패키지별 구조 / application-dev.yml + prod.yml / /api/v1/health 즉시 응답 / Swagger UI 접근

**프롬프트 #3 — FastAPI 프로젝트 생성**
> Python 3.11 / 의존성: fastapi, uvicorn, sqlalchemy(async), asyncpg, redis-py, apscheduler, httpx, openai, pydantic-settings, pytest / api/ scheduler/ models/ services/ core/ 구조 / /health 즉시 응답 / APScheduler 뼈대 포함 / requirements.txt

**프롬프트 #4 — React 프로젝트 생성**
> React 18 + TypeScript + Vite / 의존성: react-router-dom v6, axios, tailwindcss, recharts, vite-plugin-pwa, @tanstack/react-query / brand 토큰 tailwind.config.ts / Playfair Display + Inter (Google Fonts) / 25개 라우트 뼈대 / PWA manifest.json / pages/ components/ hooks/ api/ types/ store/ 구조

#### ✅ 안건 6: 인트로 영상
- Veo 3.1 접근권 미확보 → Day 5에 영상2.mp4(6.4MB)로 임시 연동, Veo 완성 후 교체

---

#### ✅ Day 1 작업 완료 (2026-05-08)

**DB / 인프라**
- PostgreSQL + Redis Docker 컨테이너 실행 완료 (healthy)
- V1__phase0.sql 실행 완료 → 15개 테이블 생성 확인
- Flyway 베이스라인 설정 완료

**Spring Boot**
- 프로젝트 생성: Java 21 / Spring Boot 3.5.14 / Gradle / YAML
- 패키지 구조 생성: domain(user/race/horse/prediction/commentary) + global(config/security/exception/response)
- SecurityConfig: STATELESS / JWT 방식 / permitAll 설정
- HealthController: GET /api/v1/health → {"status":"UP"} 확인
- application.yaml / application-dev.yaml / application-prod.yaml 설정 완료
- Swagger UI 정상 확인: http://localhost:8080/swagger-ui.html
- 의존성 문서: `racepulse/docs/dependencies.md` 저장 완료

**다음 작업 (Day 2)**
- FastAPI 프로젝트 생성 + DB 연동

---

## 🔍 ARCH 데이터 품질 체크리스트

- [x] 제공 데이터 컬럼 목록 확인 — 핵심 피처 20개 이상 확인
- [x] 과거 데이터 조회 가능 기간 — 2019년부터 확인 (약 85,000건 이상)
- [x] 레이스 결과 데이터 포함 여부 — 순위, 기록, 구간 기록 포함 확인
- [x] API rate limit — 개발계정 일 3,000콜 / 이용계정 신청 시 증가 가능
- [x] ML 피처로 활용 가능한 컬럼 수 — 20개 이상 (기준 충족)
- [ ] 결측값 비율 — 실제 API 응답 호출 후 확인 필요
- [ ] 데이터 포맷 일관성 — 2019년 구버전 스키마 확인 필요

---

## 추가 안건: 17~20번 구현 반영 및 문서 최신화

- **17~20번 프롬프트 구현 상태 반영**
  - 동적 UI 16종 구현 및 `/demo` 확인 페이지 추가
  - Monte Carlo 시뮬레이션 API 추가
  - 통합 검색 페이지 `/search` 및 검색 API 추가
  - 마이페이지 `/profile`, 즐겨찾기 `/favorites`, 설정 `/settings` 흐름 추가

- **API 명세 최신화**
  - `GET /api/v1/search`
  - `GET /api/v1/predictions/{raceId}/simulation`
  - `GET /api/v1/user/favorites`
  - `POST /api/v1/user/favorites`
  - `DELETE /api/v1/user/favorites/{id}`
  - `GET /api/v1/user/preferences`
  - `PATCH /api/v1/user/preferences`
  - `GET /api/v1/user/notifications`, `PATCH /api/v1/user/notifications/{type}`는 기존 `PushController`가 담당하므로 중복 구현 금지

- **DB 스키마 문서 갱신**
  - 실제 구현 기준으로 `user_favorites`, `user_preferences` 테이블 반영
  - `V5__create_user_profile_tables.sql` 기준 컬럼/인덱스/유니크 제약 정리
  - 문서상 `favorites`, `user_views` 등 미구현 테이블은 Phase 또는 보류 상태를 명확히 표시

- **Monte Carlo 운영 기준 확정**
  - 기본 반복 횟수 10,000회 유지 여부
  - 결과 저장 테이블 `monte_carlo_simulations` 운영 방식
  - 예측 결과가 없을 때 시뮬레이션 생성 실패 처리 방식
  - 재계산 주기와 캐시 만료 기준 확정

- **프론트 번들 크기 개선 논의**
  - 현재 빌드는 통과하지만 Vite에서 500KB 초과 청크 경고 발생
  - `/demo`, 차트, 마이페이지 등 lazy loading 분리 시점 결정

- **문서 인코딩/Notion 동기화 품질 점검**
  - 터미널 출력에서 한글 깨짐이 확인되므로 실제 파일 UTF-8 저장 상태 확인
  - Notion 자동 동기화 시 한글이 깨지지 않는지 점검
  - 회의록 원본과 Notion 반영본의 인코딩/표 형식 유지 여부 확인

---

## ✅ Phase 1 완료 현황 (2026-05-14 기준)

### 테스트 전략 구현 완료 (6단계)

| 단계 | 내용 | 결과 |
|------|------|------|
| 1단계 | BE 단위 테스트 — `JwtTokenProviderTest` | ✅ 10개 통과 |
| 2단계 | ML 단위 테스트 — `test_feature_engineering.py` | ✅ 22개 통과 |
| 3단계 | ML 단위 테스트 — `test_monte_carlo.py` | ✅ 18개 통과 |
| 4단계 | BE 컨트롤러 테스트 — `AuthControllerTest` | ✅ 11개 통과 |
| 5단계 | FE 컴포넌트 테스트 — `DataStatusBadge.test.tsx` | ✅ 9개 통과 |
| 6단계 | GitHub Actions CI — 3개 병렬 job (BE/ML/FE) | ✅ 전체 통과 |

**주요 구현 사항**
- `JwtTokenProvider.validateToken()` — null/blank 가드 + `IllegalArgumentException` 캐치 버그픽스
- `AuthControllerTest` — `@WebMvcTest` 대신 `MockMvcBuilders.standaloneSetup()` 채택 (Spring Security 복잡도 회피)
- ML pytest — `AsyncMock` 패턴으로 DB 의존성 제거, 수학적 불변식(확률 합계 = 100%) 검증
- Vitest — `css: false` 설정으로 Tailwind v4 + jsdom 충돌 해결
- CI — gradlew 실행권한 `git update-index --chmod=+x`, npm ci → npm install 변경

### GIT 작업 완료

- [x] develop 브랜치 생성 및 운영 시작
- [x] `.github/workflows/test.yml` CI 파이프라인 구성 (develop push + main PR 트리거)
- [x] main 브랜치에 `test.yml` 추가 (PR CI 정상 동작 보장)
- [x] `.claude/` 폴더 `.gitignore` 추가
- [x] PR #3 생성 (develop → main, Phase 1 테스트 전략 구현)

### 미완료 — Phase 2 시작 전 처리 필요

| 항목 | 담당 | 우선순위 |
|------|------|----------|
| ml-server Dockerfile 작성 | 창현님 직접 | 🔴 높음 (마사회 API 테스트 전제조건) |
| `ErrorCode.java` + `BusinessException.java` + `GlobalExceptionHandler.java` | BE | 🔴 높음 (API 명세 전제조건) |
| API 응답에 `last_updated / data_status / next_update` 필드 추가 | BE | 🟡 중간 |
| 마사회 API 실데이터 테스트 (결측값 비율 / 구버전 포맷 확인) | ARCH | 🟡 중간 (Dockerfile 완료 후) |
| ML 모델 정확도 측정 (Top-3 60%/70% 기준 판단) | ML | 🟡 중간 (실데이터 수집 후) |
| GPT-4o-mini 프롬프트 초안 (금요일용 / 월요일용) | BE | 🟢 낮음 |
| ~~인트로 영상 제작~~ | FE | ✅ 완료 (Veo 3.1 제작 = 영상2.mp4 확정) |

---

---

### [날짜: 2026-05-14] 4차 회의 (Phase 2 킥오프)
- **참석**: BE, FE, ARCH, PM, DESIGN, GIT, NOTION, ML, WR, 창현님

---

#### ✅ 프로젝트 방향 재확정 — 실운영 가능성 열어두기

- 예측 정확도 80% 이상 달성 시 실제 운영 진행 예정
- **포트폴리오 수준이 아닌 실운영 최고 품질 기준으로 모든 설계 결정**
- 마사회 API 상업적 이용 허가 → 80% 달성 + 운영 결정 후 진행 (사업자/도메인 선행 필요)
- OpenAI 비용 초과 시 서비스 중단 방식 폐기 → Freemium + 광고 수익화 (Phase 3~4 안건)

---

#### ✅ Dockerfile 이관 결정

- ml-server Dockerfile 작성 → **Phase 2 첫 번째 태스크로 이관** (회의 후 창현님 직접 작성)
- 이후 순서: Dockerfile → 실데이터 수집 → ML 모델 정확도 측정 → Phase 2 진행 기준 판단

---

#### ✅ BE 예외처리 구조 확정

- **HTTP 상태 코드**: A방식 (에러코드별 4xx/5xx 분리)
- **에러 표시 방식**:
  - 에러 페이지 3종: `404` / `401·403` / `500`
  - 페이지 내 API 실패 → 토스트 메시지
  - 401 → `/login` 자동 리다이렉트
- **에러코드 추가**: 개발 중 필요 시 수시 추가
- **에러 응답 포맷**: `{ "success": false, "data": null, "message": "ERROR_CODE" }`

---

#### ✅ Phase 2 DB — `ml_feature_store` 최종 구조

```sql
ml_feature_store (
  id                  BIGSERIAL PRIMARY KEY,
  race_entry_id       BIGINT    NOT NULL REFERENCES race_entries(id),
  model_version_id    BIGINT    NOT NULL REFERENCES model_versions(id),
  features            JSONB     NOT NULL,
  win_score           FLOAT,
  form_score          FLOAT,
  jockey_win_rate     FLOAT,
  odds_implied_prob   FLOAT,
  data_quality_score  FLOAT,
  computation_status  VARCHAR   DEFAULT 'PENDING'
                      CHECK (computation_status IN ('PENDING','COMPLETED','FAILED')),
  error_message       TEXT      NULL,
  is_latest           BOOLEAN   DEFAULT true,
  expires_at          TIMESTAMP,
  computed_at         TIMESTAMP DEFAULT NOW(),
  updated_at          TIMESTAMP DEFAULT NOW(),

  UNIQUE (race_entry_id, model_version_id),
  INDEX  (race_entry_id, is_latest),
  GIN INDEX (features)
)
```

---

#### ✅ Phase 2 DB — 나머지 10개 테이블 최종 구조

**`horse_breakdown_stats`**
- stat_type VARCHAR CHECK ('DISTANCE','CONDITION','COURSE','WEIGHT')
- meet_code, period_type CHECK ('ALL_TIME','1_YEAR','6_MONTH')
- race_count, win_count, place_count, win_rate, place_rate
- avg_finish_position, top3_rate, avg_odds
- updated_at

**`combination_stats`**
- combination_type CHECK ('JOCKEY_HORSE','TRAINER_HORSE')
- horse_id, partner_id, meet_code, period_type
- race_count, win_count, place_count, win_rate, place_rate
- avg_finish_position, top3_rate, avg_odds
- streak_current, last_race_date
- UNIQUE (combination_type, horse_id, partner_id, period_type, meet_code)

**`participant_form_stats`**
- participant_type CHECK ('JOCKEY','TRAINER')
- participant_id, meet_code, period_days CHECK (30,60,90), reference_date
- race_count, win_count, place_count, win_rate, place_rate
- avg_finish_position, top3_rate
- UNIQUE (participant_type, participant_id, period_days, reference_date, meet_code)

**`horse_form_index`**
- horse_id, form_score, prev_form_score
- trend CHECK ('IMPROVING','STABLE','DECLINING')
- volatility (폼 변동성 — Monte Carlo 신뢰구간 연동)
- peak_form_score, races_included, weight_config JSONB
- valid_until, calculated_at

**`horse_running_style`**
- horse_id, style CHECK ('LEADER','STALKER','CLOSER','PRESSER')
- track_type CHECK ('TURF','DIRT','ALL')
- distance_category CHECK ('SHORT','MIDDLE','LONG')
- pace_preference CHECK ('FAST','SLOW','AVERAGE')
- confidence_score, race_count
- avg_early_position, avg_final_position
- updated_at
- UNIQUE (horse_id, track_type, distance_category)

**`gate_bias_stats`**
- meet_code, gate_no, distance, track_type CHECK ('TURF','DIRT')
- period_type CHECK ('ALL_TIME','1_YEAR','6_MONTH')
- weather_condition CHECK ('CLEAR','RAIN','ALL')
- sample_count, win_rate, place_rate, bias_score
- avg_finish_position, top3_rate
- updated_at
- UNIQUE (meet_code, gate_no, distance, track_type, weather_condition)

**`feature_importance_log`**
- model_version_id FK, feature_name
- importance_score, previous_score, change_rate
- importance_rank, feature_category CHECK ('HORSE','JOCKEY','RACE','WEATHER','COMBINATION')
- shap_mean_abs (XGBoost/LightGBM SHAP value — 예측 설명력)
- alert_triggered BOOLEAN DEFAULT false
- recorded_at

**`equipment_changes`**
- horse_id FK, race_id FK
- equipment_type CHECK ('BLINKER','HOOD','TONGUE_TIE','SHADOW_ROLL','OTHER')
- change_type CHECK ('ADDED','REMOVED')
- effect_observed CHECK ('POSITIVE','NEUTRAL','NEGATIVE','UNKNOWN') DEFAULT 'UNKNOWN'
- notes TEXT NULL, changed_at

**`rival_records`**
- horse_id_1, horse_id_2, meet_code, distance
- total_races, horse1_wins, horse2_wins
- horse1_avg_position, horse2_avg_position
- last_race_id FK, last_race_date
- updated_at
- CHECK (horse_id_1 < horse_id_2)
- UNIQUE (horse_id_1, horse_id_2, meet_code, distance)

**`horse_pedigree`**
- horse_id UNIQUE FK
- sire_id nullable FK, sire_name VARCHAR (외국마 대비 병행)
- dam_id nullable FK, dam_name VARCHAR
- bloodline_score FLOAT, bloodline_category VARCHAR
- country_of_origin VARCHAR
- created_at, updated_at

---

#### ✅ Monte Carlo 시뮬레이션 운영 기준 확정

**Phase 2 적용:**
- 기법: QMC(Sobol) + Antithetic Variates + Gaussian 상관행렬
- 횟수: Adaptive (10k~100k 자동 조정, CI ±0.5% 이하 수렴 시 중단)
- 병렬처리: Python multiprocessing 4코어
- 게이트 브레이크 시뮬레이션 포함
- 날씨 불확실성 전파 (예보 확률 기반 샘플링)
- 스마트 머니 탐지 (배당률 30% 이상 급변 감지)
- 시뮬레이션 신뢰도 점수 표시
- Counterfactual 인터랙티브 UI (Web Worker 기반)
- 결과 저장: Redis 캐싱 + 경주 종료 후 DB 아카이빙
- 재계산 트리거: 출전표 확정 / 마체중·기수변경 수집 후 / 기수변경 즉시
- 예측 없을 시: 배당률 기반 대체 시뮬레이션

**Phase 3 적용:**
- Bayesian 실시간 업데이트
- Sequential Race Dynamics (경주 과정 단계별 시뮬레이션)
- Copula 기반 상관관계 (Gumbel Copula)
- 피로도/휴식 랜덤 모델링
- 시뮬레이션 앙상블 (3개 모델 가중 평균)
- Celery 분산처리

**Phase 4 / 로드맵:**
- 월별 캘리브레이션 자동화 (데이터 2~3개월 축적 필요)
- 실시간 레이스 포지션 업데이트 (KRA 실시간 피드 확보 선행)

**`monte_carlo_simulations` 테이블 (V3__phase2.sql 포함):**
```sql
monte_carlo_simulations (
  id                   BIGSERIAL PRIMARY KEY,
  race_id              BIGINT NOT NULL REFERENCES races(id),
  race_entry_id        BIGINT NOT NULL REFERENCES race_entries(id),
  simulation_version   INT NOT NULL DEFAULT 1,
  technique            VARCHAR CHECK (technique IN ('STANDARD','QMC','ANTITHETIC','ADAPTIVE')),
  iterations_actual    INT NOT NULL,
  win_probability      FLOAT,
  place_probability    FLOAT,
  win_prob_ci_lower    FLOAT,
  win_prob_ci_upper    FLOAT,
  rank_distribution    JSONB,
  scenario_breakdown   JSONB,
  upset_probability    FLOAT,
  competitiveness_idx  FLOAT,
  winning_conditions   TEXT,
  computation_ms       INT,
  trigger_type         VARCHAR CHECK (trigger_type IN
                       ('SCHEDULED','JOCKEY_CHANGE','WEIGHT_UPDATE','MANUAL')),
  is_latest            BOOLEAN DEFAULT true,
  computed_at          TIMESTAMP DEFAULT NOW(),
  UNIQUE (race_entry_id, simulation_version),
  INDEX (race_id, is_latest)
)
```

---

#### ✅ 디자인 시스템 확정

**철학**: "Bloomberg Terminal meets Premium Sports Analytics" — 지성미 있는 생동감

**컬러 팔레트:**
- page-bg: #07091A / surface: #0D1227 / elevated: #131A36 / border: #1A2444
- gold-primary: #D4A843 / gold-highlight: #F5C842 / gold-deep: #B8922E
- 골드 글로우: box-shadow 0 0 24px rgba(212,168,67,0.35)
- 데이터 팔레트: data-blue #3B82F6 / data-purple #8B5CF6 / data-teal #14B8A6 / data-amber #F59E0B

**타이포그래피:**
- Playfair Display → 브랜드/감성 (말 이름, 히어로)
- Inter → 데이터/정밀 (수치, 본문)
- JetBrains Mono → 기술 데이터 (확률, CI, 타임스탬프) ← 신규 추가
- 수치: Data-XL(36px) / Data-L(24px) / Data-M(16px) / Data-S(13px)

**애니메이션 토큰:**
- duration: fast(150ms) / base(250ms) / slow(400ms) / slower(600ms) / hero(1200ms)
- easing: snap / bounce / smooth

**진행하면서 수정 가능 — 토큰 레벨 변경 자유, 컴포넌트 구조 변경은 DESIGN→FE 사전 공유**

---

#### ✅ 동적 UI 16종 우선순위 확정

**Phase 2 필수 (10종)**: #1 컨디션 게이지 / #2 승률 바 스윕 / #6 게이트 슬라이드 인 / #7 레이스 시뮬레이션 / #8 스파크라인 / #12 정확도 원형 게이지 / #13 수집 카운트다운 / #14 경기 카운트다운 / #15 AI 해설 타이핑 / #16 로딩 말 달리기

**Phase 3 (5종)**: #3 호버 상세 팝업 / #5 레이더 차트 / #9 착순 역순 공개 / #10 구간별 라인 차트 / #11 예측 vs 실제 게이지

**통합 처리 (1종)**: #4 컨디션 색상 코딩 → #1 게이지에 포함

---

#### ✅ 인트로 영상 최종 확정

- `영상2.mp4` = Veo 3.1로 직접 제작한 최종본 확정
- 구현 완료 상태 유지 (canplaythrough + preload="auto" + 골드 프로그레스 바)

---

#### ✅ AWS 배포 환경 확정

**서버 구조**: FE(Nginx) / BE(Spring Boot) / ML(FastAPI) 3서버 분리 + ALB + CloudFront CDN

**인스턴스**: 최소 스펙 시작 → 실운영 결정 시 스케일업

| 서버 | 개발 | 실운영 |
|------|------|--------|
| FE | t3.micro | t3.small |
| BE | t3.small | t3.medium |
| ML | t3.medium | t3.large |
| RDS | db.t3.micro | db.t3.small |
| Redis | cache.t3.micro | cache.t3.small |

**도메인/SSL**: Route 53 + ACM (무료)

**배포 방식**: ~~Blue-Green 무중단 폐기~~ → **매주 화요일 02:00~06:00 정기 점검일 배포**
- 사전 공지: 월요일 22:00 푸시 알림 + 오후 배너
- 점검 모드 페이지: 브랜드 톤 + 종료 카운트다운
- Blue-Green 재검토: DAU 수천 이상 시점

---

#### ✅ GIT 브랜치 전략 + PR 기준 확정

**브랜치 구조:**
```
main          Phase 완료 PR + 버전 태그 (v0.2.0 / v0.3.0 / v1.0.0)
  ↑
develop       기능 단위 PR (3~5 프롬프트 묶음)
  ↑
feat/*        프롬프트 단위 커밋
hotfix/*      긴급 버그 (실운영 시)
```

**커밋 단위**: 프롬프트 1개 = 커밋 1개
**커밋 메시지**: `feat: [prompt-N] 설명`
**feat 브랜치 기준**: 논리적으로 묶이는 3~5개 프롬프트 = 브랜치 하나

**main PR 체크리스트 (4개):**
- [ ] CI 전체 통과 (BE/ML/FE 3개 job)
- [ ] 신규 기능은 테스트 코드 포함
- [ ] API 변경 시 NOTION 명세서 업데이트 확인
- [ ] .env 시크릿 커밋 여부 확인

*(점검일 배포 원칙은 실운영 전환 시점에 추가)*

---

#### ✅ 번들 최적화 전략 확정 (우선순위 순)

| 순서 | 방법 | 효과 |
|------|------|------|
| 1 | Bundle 분석 (rollup-plugin-visualizer) | 원인 파악 |
| 2 | Brotli 압축 (vite-plugin-compression) | -70~80% |
| 3 | Resource Hints (preconnect/prefetch) | 체감 속도 즉시 개선 |
| 4 | WebM 변환 (영상2.mp4 병행) | -2.6MB |
| 5 | Font 서브셋 (한국어+Latin) | -700KB |
| 6 | moment → dayjs 교체 확인 | -230KB |
| 7 | recharts → Apache ECharts | -220KB |
| 8 | manualChunks 전략 | 캐시 최적화 |
| 9 | Lazy Loading (route 단위) | 초기 로드 분산 |
| 10 | Web Worker (Monte Carlo Counterfactual) | UI 버벅임 방지 필수 |
| 11 | 목록 가상화 (@tanstack/virtual) | 대규모 데이터 대응 |
| 12 | Service Worker 캐싱 전략 (Workbox) | 재방문/오프라인 |
| 13 | Bundle Size CI 모니터링 (size-limit) | 자동 감지 |
| 14 | Intersection Observer | 하단 컴포넌트 지연 렌더링 |

---

#### ✅ 실운영 대비 추가 확정 사항

| 항목 | 시점 | 담당 |
|------|------|------|
| 개인정보보호법 준수 (약관/처리방침/동의) | Phase 2~3 | BE + DESIGN |
| OpenAI 비용 → Freemium + 광고 수익화 | Phase 3~4 안건 | PM |
| 마사회 API 상업적 이용 허가 | 80% 달성 후 | 창현님 |
| 장애 감지 + Slack 알림 | Phase 4 | ARCH |
| DB 자동 백업 전략 | Phase 4 | ARCH |
| AWS Secrets Manager 키 관리 | Phase 4 | GIT + ARCH |
| 접근성(a11y) 기본 대응 | Phase 4 | FE |
| 부하 테스트 (k6) | Phase 4 | ARCH + BE |
| 무중단 배포 재검토 | DAU 수천 이상 시점 | ARCH |

---

## 🔜 다음 회의 안건 (5차 회의)

| 우선순위 | 안건 | 담당 |
|----------|------|------|
| 🔴 | Dockerfile 작성 완료 확인 → 실데이터 수집 시작 | 창현님 + ARCH |
| 🔴 | ML 모델 정확도 측정 결과 공유 (Top-3 60%/70% 기준) | ML |
| 🔴 | BE 예외처리 구현 완료 확인 | BE |
| 🟡 | V3__phase2.sql 생성 완료 확인 | ARCH |
| 🟡 | Phase 2 프롬프트 진행 현황 점검 | 팀 전체 |
| 🟡 | 개인정보보호법 준수 체계 설계 (약관/처리방침) | BE + DESIGN |
| 🟢 | Freemium 수익화 모델 세부 설계 | PM |
