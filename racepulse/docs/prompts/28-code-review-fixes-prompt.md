# 28. RacePulse Phase 2 코드 리뷰 및 버그 수정 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

> 📌 **상태: ✅ 2026-05-15 완료** — 이 파일은 소급 문서화 파일입니다.
> 실제 작업은 Phase 2 마무리 시점에 수행되었습니다.

---

## 목표

Phase 2 전체 코드에 대한 교차 리뷰 및 버그 수정을 수행합니다.

- 프롬프트 01~27 작업 결과물 전체를 대상으로 합니다.
- 코드 품질, 규칙 준수, 보안 취약점, 성능 이슈를 검토합니다.

---

## 검토 대상

### FE (React)
- 컬러 하드코딩 여부 (규칙 10: Tailwind 토큰만 허용)
- API 호출 위치 (규칙 9: `src/api/` 분리 여부)
- 한국어 주석 누락 여부 (규칙 1)
- TODO 주석 형식 준수 (규칙 4)

### BE (Spring Boot)
- ApiResponse 통일 여부 (규칙 5)
- Exception 처리 통일 여부 (규칙 6)
- DTO ↔ Entity 분리 여부 (규칙 7)
- 환경변수 노출 여부 (규칙 3)

### ML (FastAPI)
- 한국어 주석 누락 여부 (규칙 1)
- `# -*- coding: utf-8 -*-` 헤더 여부 (규칙 2)
- 환경변수 관리 여부 (규칙 3)

### DB (Flyway)
- 인덱스 네이밍 규칙 준수 (규칙 12: `idx_테이블명_컬럼명`)
- 마이그레이션 파일 수정 금지 (규칙 13)

---

## 완료 조건

```bash
# BE 컴파일
cd racepulse/backend && .\gradlew compileJava

# FE 빌드
cd racepulse/frontend && npm run build

# ML 서버 기동 확인
cd racepulse/ml-server && python -m uvicorn app.main:app --port 8000
```

---

## Git 규칙

```
브랜치: feat/phase2-code-review
커밋 메시지: feat: [prompt-28] Phase 2 코드 리뷰 및 버그 수정
```
