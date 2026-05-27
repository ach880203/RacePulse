# Codex 프롬프트 — Phase 4-6: 운영 품질 정리

## 작업 개요
Phase 4 운영 품질 정리 항목 중 빠르게 처리 가능한 4가지를 한 번에 처리합니다.

---

## 작업 1: .gitignore 로그 파일 추가

**파일**: `racepulse/ml-server/.gitignore` (없으면 신규 생성)
또는 프로젝트 루트 `.gitignore`

추가할 항목:
```gitignore
# ML 서버 스크립트 실행 로그 — 로컬 실행 결과물, 커밋 불필요
racepulse/ml-server/scripts/bulk_stdout.txt
racepulse/ml-server/scripts/bulk_stderr.txt
racepulse/ml-server/scripts/nightly_log.txt

# Task Scheduler 관련 스크립트 — 환경별로 다름
racepulse/ml-server/scripts/fix_scheduler_admin.ps1
```

---

## 작업 2: UI 영어 문구 한글화

아래 파일들의 영어 문구를 한글로 바꿉니다.
**코드 내부 식별자(변수명, 클래스명, enum)는 그대로 유지합니다.**
화면에 표시되는 텍스트(label, placeholder, heading)만 변경합니다.

### `racepulse/frontend/src/pages/HomePage.tsx`
```
'AI RACE INTELLIGENCE'  →  'AI 경주 분석'
'TODAY RACES'           →  '오늘의 경주'  (이미 아래에 한글이 있으므로 위 소제목만 삭제 또는 한글로)
'PREDICTION SCORE'      →  '예측 정확도'
```

### `racepulse/frontend/src/pages/DashboardPage.tsx`
```
'PREDICTION SCORE'  →  '예측 정확도'
```

### `racepulse/frontend/src/pages/RaceListPage.tsx`
```
'RACE BOARD'  →  '경주 목록'
```

### `racepulse/frontend/src/components/layout/Header.tsx`
```
'DATA RACING PLATFORM'  →  '데이터 경마 분석 플랫폼'
```

**확인 방법**: 변경 후 화면에 영어가 남지 않아야 합니다.
(단, 브랜드명 "RacePulse" → "레이스펄스"는 이미 돼 있으므로 건드리지 마세요)

---

## 작업 3: 대시보드 isDemo 플래그 + 안내 문구

**파일**: `racepulse/frontend/src/pages/DashboardPage.tsx`

현재 DEMO_PREDICTIONS 데이터를 쓰는 "최근 예측 결과" 섹션에
이미 `데모 데이터` 뱃지가 있습니다. 이것을 보완합니다:

```tsx
// 현재 isDemo 뱃지 위치 확인 후, 해당 섹션 상단에 아래 안내 추가
<div className="rounded-2xl border border-brand-gold-400/20 bg-brand-gold-400/5 px-4 py-3 text-sm text-white/60">
  {/* 실제 예측 API 연동 전까지 샘플 데이터로 표시합니다. */}
  현재 표시되는 예측 결과는 시스템 검증용 샘플 데이터입니다.
  실제 경주 예측은 경주 상세 페이지에서 확인하세요.
</div>
```

---

## 작업 4: FastAPI charset 명시

**파일**: `racepulse/ml-server/main.py` (또는 FastAPI 앱 진입점)

FastAPI 응답에 UTF-8 charset을 명시해서 한글 깨짐을 방지합니다:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

# 기본 JSONResponse가 charset을 명시하지 않아 일부 클라이언트에서 한글이 깨짐.
# 미들웨어로 모든 JSON 응답에 charset=utf-8을 추가합니다.
@app.middleware("http")
async def add_charset_header(request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response
```

기존에 이미 설정돼 있다면 중복 추가하지 마세요.

---

## 코드 작성 규칙
- 모든 변경에 주석으로 이유 설명
- 기존 동작을 바꾸지 않는 최소한의 변경만

## 완료 기준
1. `git status`에서 `bulk_stdout.txt` 등이 untracked으로 보이지 않음
2. 브라우저에서 홈/대시보드/경주목록 화면에 영어 문구 없음
3. 대시보드 샘플 데이터 안내 문구 표시
4. FastAPI 응답 헤더: `Content-Type: application/json; charset=utf-8`
