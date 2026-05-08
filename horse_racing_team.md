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
- [x] **ARCH**: DB 테이블 목록 확정 → ✅ PostgreSQL, 즉시 24개 + Phase2 4개
- [ ] **ARCH**: DB 스키마 상세 작성 (컬럼/인덱스/관계 정의)
- [ ] **ARCH**: FastAPI APScheduler + Redis 수집 파이프라인 설계
- [x] **BE**: Spring Boot API 엔드포인트 확정 → ✅ 39개 / /api/v1/ 버전 포함 (34→36 카카오 추가 → 38 알림설정 추가 → 39 refresh 추가)
- [x] **BE**: 인증 보안 구조 확정 → ✅ JWT + Rotation + Family 감지 + BCrypt + Rate Limiting
- [x] **BE**: 환경별 설정 분리 확정 → ✅ dev(HTTP) / prod(HTTPS) 프로파일
- [ ] **BE**: Spring Boot 프로젝트 세팅 + Security 설정 구현
- [ ] **BE**: 카카오 OAuth 2.0 연동 (로그인/회원가입)
- [ ] **창현님**: 카카오 개발자 센터 앱 등록 + REST API 키 발급
- [ ] **BE**: API 응답에 last_updated / data_status / next_update 필드 포함 설계
- [ ] **FE**: 페이지 구조 (라우팅) 초안 작성
- [ ] **FE**: 데이터 상태 UI 컴포넌트 설계 (준비중 / 업데이트 예정 / 데이터 수집 중 / 기수변경 뱃지)
- [ ] **PM**: Phase 0 상세 일정 수립
- [x] **팀 전체**: 안건 1 확정 → ✅ 선택지 B (Spring Boot 메인, FastAPI 마이크로서비스)
- [x] **팀 전체**: 안건 2 확정 → ✅ ML 기반 직행 (XGBoost/LightGBM, 2019년~데이터 활용)
- [x] **팀 전체**: 안건 3 확정 → ✅ APScheduler 스케줄 수집 (아래 상세 일정 참조)
- [x] **팀 전체**: 안건 4 확정 → ✅ GPT-4o-mini 캐싱, 금/월 해설, 동적 UI 16종, 인트로 영상
- [x] **팀 전체**: 프로젝트명 확정 → ✅ RacePulse
- [x] **팀 전체**: 인트로 영상 방향 변경 → ✅ 시네마틱 실사 / 다크 네이비 + 골드
- [x] **팀 전체**: DB 선택 → ✅ PostgreSQL (윈도우 함수/JSONB/ML 분석 쿼리 이점)
- [x] **팀 전체**: DB 테이블 목록 → ✅ 즉시 25개 확정 (24→25, notification_settings 분리 추가 / Phase 2 이후 4개 별도)
- [ ] **FE**: 인트로 영상 제작 (Veo 3.1 시네마틱 실사 스타일)
- [x] **FE**: TypeScript 기반 라우팅 구조 확정 → ✅ 25개 라우트 (목록 확정, /intro는 별도 라우트 아닌 홈의 조건부 렌더링으로 처리)
- [ ] **BE**: GPT-4o-mini 프롬프트 초안 작성 (금요일용 / 월요일용)
- [ ] **ARCH**: Monte Carlo 시뮬레이션 Phase 2 설계 문서 작성
- [x] **PM**: Phase 0 일정 확정 → ✅ 7일 일정
- [x] **창현님**: 카카오 개발자 센터 앱 등록 완료 ✅
- [x] **팀 전체**: Figma 사용 확정 ✅ (DESIGN 주도)
- [x] **팀 전체**: Swagger/OpenAPI 추가 확정 ✅
- [x] **팀 전체**: Git 브랜치 전략 확정 ✅ (main/develop/feature/*)
- [x] **팀 전체**: 로깅 확정 ✅ (SLF4J+Logback 기본 / FastAPI logging)
- [ ] **ARCH**: PostgreSQL Docker + 25개 테이블 init.sql 생성 및 실행 (Day 1) ← 오늘
- [ ] **ARCH**: FastAPI 프로젝트 생성 + DB 연동 (Day 2)
- [ ] **ARCH**: 마사회 API + 기상청 API 연동 테스트 (Day 3~4)
- [ ] **BE**: Spring Boot 프로젝트 생성 + PostgreSQL + Security (Day 1) ← 오늘
- [ ] **BE**: 카카오 OAuth 연동 (Day 3)
- [ ] **BE**: Web Push 알림 로직 + VAPID 키 설정
- [ ] **BE**: 기본 API 엔드포인트 3~5개 완성 (Day 4)
- [ ] **FE**: React+TypeScript 프로젝트 생성 + 라우팅 뼈대 25개 (Day 1) ← 오늘
- [ ] **FE**: PWA 설정 (manifest.json + Vite PWA Plugin + Service Worker)
- [ ] **FE**: 홈/경주목록 페이지 뼈대 (Day 5)
- [ ] **FE**: 인트로 영상 임시 연동 → 영상2.mp4 사용 (Day 5, Veo 3.1 완성 전까지)
- [ ] **DESIGN**: Figma 컬러 팔레트 + 디자인 토큰 초안 (Day 5)
- [x] **팀 전체**: 2차 회의 확정 → ✅ DB 스키마 25개 / 폰트(Playfair Display+Inter) / Tailwind brand 토큰 / 프로젝트 세팅 프롬프트 4개

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

### 즉시 생성 테이블 — 25개

> 2차 회의 재점검: 24→25 (notification_settings 독립 분리 + odds_history Phase2→즉시 포함)

| 분류 | 테이블 | 수 |
|------|--------|----|
| **마스터** | horses, jockeys, trainers, racecourses | 4 |
| **경주** | races, race_entries, race_results | 3 |
| **이력** | track_conditions, horse_weight_history, jockey_changes, entry_cancellations, horse_clinic, horse_ratings_history, odds_history | 7 |
| **날씨** | weather_forecasts | 1 |
| **ML/AI** | predictions, prediction_accuracy_logs, model_versions, ai_commentary | 4 |
| **수집** | collection_logs | 1 |
| **유저** | users, favorites, user_views, user_preferences, notification_settings | 5 |

### Phase 2 이후 테이블 — 3개
`horse_training_logs` / `race_sectional_detail` / `search_history`

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

## 🔜 다음 회의 준비사항

### 신규 참석자
- **웹디자이너 (DESIGN)** 합류 — 온보딩 필요

### 웹디자이너를 위한 사전 공유 자료 (PM 준비)
- 프로젝트 개요 및 핵심 가치 (사행성 없는 분석 플랫폼)
- 확정된 기술스택 (React 18 + TypeScript + Tailwind CSS)
- 인트로 영상 방향 (시네마틱 실사, 다크 네이비 + 골드)
- 16종 동적 UI 요소 목록
- 데이터 상태 표시 UX 가이드

### 다음 회의 안건

| 우선순위 | 안건 | 담당 |
|----------|------|------|
| 🔴 | 웹디자이너 온보딩 + 디자인 방향 합의 (컬러, 톤앤매너) | DESIGN + 팀 전체 |
| 🔴 | DB 스키마 초안 검토 | ARCH 발표 |
| 🔴 | Spring Boot API 엔드포인트 초안 검토 | BE 발표 |
| 🟡 | FE TypeScript 라우팅 구조 초안 검토 | FE 발표 |
| 🟡 | Phase 0 상세 일정 확정 | PM 발표 |
| 🟢 | 인트로 영상 Veo 3.1 시안 공유 | FE |

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

**이력 (8개)**
- `track_conditions`: id, race_id(FK), meet_code, rc_date, moisture_rate, condition(ENUM: DRY/WET/HUMID/SATURATED), recorded_at
- `horse_weight_history`: id, horse_id(FK), race_id(FK), rc_date, weight, weight_diff, recorded_at
- `jockey_changes`: id, race_entry_id(FK), race_id(FK), horse_id(FK), prev_jockey_id(FK), new_jockey_id(FK), changed_at, reason
- `entry_cancellations`: id, race_id(FK), horse_id(FK), race_entry_id(FK), reason, cancelled_at
- `horse_clinic`: id, horse_id(FK), diagnosis, treatment, clinic_date, return_expected_date, created_at
- `horse_ratings_history`: id, horse_id(FK), rating_1~4, recorded_date, created_at
- `weather_forecasts`: id, meet_code, forecast_date, temp_min, temp_max, precipitation_prob, wind_speed, condition, source, created_at, updated_at
- `odds_history`: id, race_entry_id(FK), race_id(FK), odds_win, odds_place, odds_quinella, recorded_at

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

## 🔍 ARCH 데이터 품질 체크리스트

- [x] 제공 데이터 컬럼 목록 확인 — 핵심 피처 20개 이상 확인
- [x] 과거 데이터 조회 가능 기간 — 2019년부터 확인 (약 85,000건 이상)
- [x] 레이스 결과 데이터 포함 여부 — 순위, 기록, 구간 기록 포함 확인
- [x] API rate limit — 개발계정 일 3,000콜 / 이용계정 신청 시 증가 가능
- [x] ML 피처로 활용 가능한 컬럼 수 — 20개 이상 (기준 충족)
- [ ] 결측값 비율 — 실제 API 응답 호출 후 확인 필요
- [ ] 데이터 포맷 일관성 — 2019년 구버전 스키마 확인 필요
