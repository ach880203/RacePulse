# 44. RacePulse 통합 테스트 + 코드 리뷰 프롬프트

---

## 📚 실행 전 필수 인식 단계 (반드시 순서대로 읽으세요)

```
1. horse_racing_team.md        ← Phase 0~1 킥오프, 팀 구성, 초기 규칙 전체
2. horse_racing_team_v2.md     ← Phase 2 전체 기록
3. horse_racing_team_v3.md     ← Phase 3 킥오프, 14차 회의 확정사항 (모든 Phase 3 기능)
4. docs/PROJECT_RULES.md       ← 코딩 규칙 20개
```

**선행 조건**: **prompt-29~43 전체 완료** — Phase 3 모든 기능 구현 후 실행

---

## 🗂️ Phase 3 전체 구현 완료 체크리스트

### DB / ML
| Prompt | 기능 | 확인 |
|--------|------|------|
| 29 | V13 마이그레이션 (trainer_changes / equipment_changes / user_wallets / AI 품질 컬럼) | □ |
| 30 | Bayesian MC (BayesianUpdater + monte_carlo.py prior 주입) | □ |
| 31 | Sequential Race Dynamics (Redis 당일 결과 + 뒷 경주 예측) | □ |
| 32 | Copula 상관행렬 (말-말 상관관계 확장) | □ |

### BE
| Prompt | 기능 | 확인 |
|--------|------|------|
| 33 | 변경감지 5종 ChangeDetector + APScheduler 30분 잡 | □ |
| 34 | 변경감지 BE API + Redis 구독 + 웹 푸시 | □ |
| 35 | AI 해설 GPT-4.1 전환 + 품질 점수 | □ |
| 36 | 개인정보보호법 BE (/privacy · /terms + 동의 처리) | □ |
| 37 | 편자 시스템 BE (지갑 API 7개 + 이원화) | □ |

### FE
| Prompt | 기능 | 확인 |
|--------|------|------|
| 38 | 개인정보보호법 FE + 사행성 팝업 | □ |
| 39 | Freemium 잠금 UI (blur + 편자 소비 + WalletHUD) | □ |
| 40 | 말 Stat 카드 (FIFA 카드 + 수치 게이지) | □ |
| 41 | 동적 UI Phase 3 (27~31번) | □ |
| 42 | 변경사항 FE UI (뱃지 + 카드 + 타임라인) | □ |
| 43 | /admin 패널 4탭 | □ |

---

## 목표

Phase 3 기능 전체를 통합 검증합니다.

1. **빌드/컴파일 검증** — BE, FE, ML 서버 모두 에러 없이 빌드
2. **핵심 플로우 E2E 테스트** — 사용자 여정 5개 흐름 검증
3. **프로젝트 규칙 검토** — 규칙 20개 준수 여부 확인
4. **Phase 3 완료 선언** — develop PR 작성 + v3.0.0 태그 준비

---

## 구현 사항

### 1. 빌드 검증 3종

```bash
# ML 서버
cd racepulse/ml-server
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
# → 오류 없이 기동 확인

# BE
cd racepulse/backend
.\gradlew build
# → BUILD SUCCESSFUL

# FE
cd racepulse/frontend
npm run build
# → 빌드 성공, 번들 크기 경고 확인
```

---

### 2. E2E 테스트 5개 플로우

#### 플로우 1: 신규 유저 온보딩 (개인정보보호법)
```
1. 앱 최초 접속
2. 사행성+약관 팝업 표시 확인
3. 스크롤 전 "확인함" 비활성 확인
4. 스크롤 완료 → "확인함" 활성화 → 클릭
5. "동의하기" 클릭 → 팝업 닫힘
6. localStorage에 racepulse_terms_agreed=true 저장 확인
7. 재접속 시 팝업 미표시 확인
```

#### 플로우 2: Freemium 편자 흐름
```
1. 로그인 → GET /api/v1/wallet → 잔액 0 확인
2. POST /api/v1/wallet/earn/attendance → 이벤트 편자 +1, 건초 +3
3. /races/1/prediction 접속 → Top-1 영역 blur 잠금 확인
4. "편자 소비하기" (35편자) → INSUFFICIENT_HORSESHOE 에러 확인
5. POST /api/v1/wallet/earn/ad?duration=60 (×5) → 이벤트 편자 +10
6. Top-1 편자 소비 → 잠금 해제 → 콘텐츠 표시 확인
7. GET /api/v1/wallet/transactions → 거래 내역 7건 확인
```

#### 플로우 3: 변경감지 → 예측 재시뮬레이션
```
1. POST /ml/changes/detect?rc_date=오늘 → 변경 감지 실행
2. 기수 변경 감지 시:
   - trainer_changes 또는 race_entries 업데이트 확인
   - Redis 'racepulse:changes' 채널 발행 확인
   - Spring Boot ChangeEventSubscriber 수신 → 웹 푸시 발행
3. /races/{id}/entries 접속 → ChangeBadge 🔴 표시 확인
4. /races/{id} 변경이력 탭 → 타임라인 표시 확인
5. AI 해설 캐시 무효화 확인 (Redis key 삭제)
```

#### 플로우 4: Bayesian MC 예측
```
1. POST /ml/simulate (use_bayesian=true, use_copula=true)
2. 응답에 bayesian_priors 필드 포함 확인
3. 말A 최근 2회 1위 → prior 30% → posterior > 30% 확인
4. BayesianUpdateAnimation 컴포넌트에 prior/posterior 전달 → 카운트업 확인
```

#### 플로우 5: ADMIN 패널 접근
```
1. 일반 유저로 /admin 접속 → /unauthorized 리다이렉트 확인
2. ADMIN 유저로 /admin 접속 → 4탭 표시 확인
3. AI 해설 품질 탭 → quality_score 통계 표시 확인
4. 편자 통계 탭 → wallet_transactions 집계 표시 확인
```

---

### 3. 프로젝트 규칙 검토 체크리스트 (규칙 20개)

**FE 규칙 (자동 검사):**
```bash
# 컬러 하드코딩 검사 (규칙 10)
grep -rn "#[0-9A-Fa-f]\{6\}" racepulse/frontend/src --include="*.tsx" --include="*.ts"
# → 결과 없어야 함 (brand-navy-950 등 토큰 사용 확인)

# 하드코딩 hex 색상 허용 예외: tailwind.config.ts의 색상 정의만 허용

# API 호출 위치 검사 (규칙 9)
grep -rn "axios\|fetch(" racepulse/frontend/src/pages --include="*.tsx"
# → src/api/ 밖의 API 호출 없어야 함
```

**BE 규칙 (수동 확인):**
```
□ ApiResponse<T> 모든 응답에 사용 (규칙 5)
□ BusinessException + ErrorCode 에러 처리 (규칙 6)
□ Entity를 API 응답에 직접 사용하지 않음 (규칙 7)
□ 환경변수 .env 관리 (규칙 3)
```

**DB 규칙:**
```bash
# 인덱스 네이밍 검사 (규칙 12)
grep -n "CREATE INDEX" racepulse/backend/src/main/resources/db/migration/V13*.sql
# → idx_테이블명_컬럼명 형식 확인
```

**공통:**
```bash
# 한국어 주석 존재 확인 (규칙 1)
# Phase 3 신규 파일들에 한국어 주석 있는지 샘플 확인

# TODO 주석 형식 확인 (규칙 4)
grep -rn "TODO:" racepulse --include="*.java" --include="*.py" --include="*.tsx"
# → [Phase 숫자] 형식 사용 확인
```

---

### 4. 성능 확인

```bash
# FE 번들 크기 (Phase 2 기준선 대비)
npm run build 2>&1 | grep "dist/"
# → 청크별 크기 확인, 500KB 초과 청크 경고 시 코드 스플리팅 검토

# ML 서버 응답 시간
curl -w "@curl-format.txt" -X POST http://localhost:8000/ml/simulate \
  -d '{"race_id": 1, "use_bayesian": true, "use_copula": true}'
# → 목표: 3초 이내 (10k 시뮬레이션 기준)
```

---

### 5. Phase 3 완료 선언 작업

```bash
# 1. develop 브랜치에 PR 생성 (Phase 3 전체)
# 제목: feat: Phase 3 완료 — Bayesian MC / 변경감지 / Freemium / AI 해설 고도화 / 관리자 패널

# 2. develop → main Squash merge 후 v3.0.0 태그
git tag v3.0.0
git push origin v3.0.0

# 3. horse_racing_team_v3.md 업데이트
# - 프롬프트 실행 현황 29~44 전부 ✅ 표시
# - Phase 3 완료 선언
# - Phase 4 방향 메모 추가
```

**horse_racing_team_v3.md Phase 3 완료 선언 추가:**
```markdown
### [날짜: 2026-06-XX] Phase 3 완료 선언

| 조건 | 상태 |
|------|------|
| prompt-29~44 전체 구현 | ✅ |
| Bayesian MC + Sequential + Copula | ✅ |
| 변경감지 5종 + BE + FE | ✅ |
| AI 해설 GPT-4.1 고도화 + 품질 점수 | ✅ |
| 개인정보보호법 BE + FE | ✅ |
| 편자 시스템 전체 (BE + FE) | ✅ |
| /admin 패널 4탭 | ✅ |
| develop → main PR + v3.0.0 태그 | ✅ |
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

테스트/검토 코드에도 한국어 주석 필수:
- 각 E2E 플로우가 무엇을 검증하는지 설명
- 실패 시 원인 추적 방법 설명
- `grep -rn` 검사 명령이 무엇을 찾는지 설명

---

## Git 규칙

```
브랜치: feat/phase3-review
커밋 메시지: feat: [prompt-44] Phase 3 통합 테스트 + 코드 리뷰 완료 — E2E 5개 플로우 검증
```

---

## 완료 기준

```bash
# 모든 빌드 성공
.\gradlew build       # BE: BUILD SUCCESSFUL
npm run build         # FE: 성공
uvicorn app.main:app  # ML: 오류 없이 기동

# E2E 5개 플로우 전부 통과
# 규칙 20개 검토 체크리스트 전부 □ → ✅

# develop → main PR 생성 완료
# v3.0.0 태그 push 완료
```

---

## ⚠️ 알려진 Phase 4 TODO 항목 (지금 구현하지 말 것)

Phase 3에서 껍데기만 만들어 둔 것들 — Phase 4에서 구현:
- `POST /api/v1/wallet/earn/purchase` — 포트원 결제 연동
- `GET /api/v1/horses/{id}/stats` — ML 스탯 계산 실제 연동
- 다마고치 + 퀴즈 + 토너먼트 (Phase 5)
- AWS 배포 (EC2 + ALB + CloudFront)
- 부하 테스트 (동시 100명, p95 500ms)
