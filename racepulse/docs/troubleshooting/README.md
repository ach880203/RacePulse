# RacePulse 트러블슈팅 자료

개발 중 발생한 에러와 해결 방법을 기록합니다.
새 에러가 생기면 `TS-번호-짧은-설명.md` 파일을 추가하세요.

---

## 목록

| 번호 | 제목 | 서버 | 발생일 |
|------|------|------|--------|
| [TS-001](TS-001-ml-server-pandas-not-found.md) | ModuleNotFoundError: No module named 'pandas' | ML 서버 (FastAPI) | 2026-05-11 |
| [TS-002](TS-002-postgresql-enum-vs-varchar.md) | operator does not exist: race_status = character varying | Spring Boot | 2026-05-11 |
| [TS-003](TS-003-spring-env-variable-not-resolved.md) | Could not resolve placeholder 'JWT_SECRET' | Spring Boot | 2026-05-11 |
| [TS-004](TS-004-jwt-base64-illegal-character.md) | DecodingException: Illegal base64 character '-' | Spring Boot | 2026-05-11 |
| [TS-005](TS-005-pwa-manifest-syntax-error.md) | manifest.webmanifest Line 1 Syntax error | React 프론트 | 2026-05-11 |

---

## 파일 이름 규칙

```
TS-{번호}-{핵심-키워드}.md

예시:
  TS-004-redis-connection-refused.md
  TS-005-cors-blocked-frontend.md
  TS-006-flyway-checksum-mismatch.md
```

## 문서 구조 (템플릿)

```markdown
# TS-번호 | 에러 제목

- 발생일 / 서버 / 엔드포인트 또는 단계

## 에러 메시지
(실제 로그 붙여넣기)

## 원인
(왜 발생했는지 설명)

## 해결 방법
(수정 전/후 코드 직접 포함)

## 교훈
(다음에 같은 실수 안 하려면)
```
