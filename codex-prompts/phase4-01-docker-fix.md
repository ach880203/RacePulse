# Codex 프롬프트 — Phase 4-1: Docker 실행 재현성 복구

## 작업 개요
RacePulse 프로젝트의 Docker Compose가 현재 완전히 실행 불가 상태입니다.
아래 3가지 문제를 순서대로 수정해주세요.

## 프로젝트 구조
```
racepulse/
├── docker-compose.yml        ← 수정 대상
├── ml-server/
│   └── Dockerfile            ← 수정 대상
└── backend/
    └── Dockerfile            ← 신규 작성 대상 (없음)
```

---

## 수정 1: ML Dockerfile 이미지명 오타 수정

**파일**: `racepulse/ml-server/Dockerfile`

현재 첫 번째 줄:
```dockerfile
FROM python=:3.11-slim
```

수정 후:
```dockerfile
FROM python:3.11-slim
```

`=:` → `:` 오타 수정. 이 오타로 인해 `docker compose up` 시 빌드 자체가 실패합니다.

---

## 수정 2: docker-compose.yml ML 서버 DB 연결 URL 수정

**파일**: `racepulse/docker-compose.yml`

ML 서버(FastAPI) 서비스의 환경변수에서:
```yaml
DATABASE_URL: postgresql://...
```

다음으로 수정:
```yaml
DATABASE_URL: postgresql+asyncpg://...
```

**이유**: FastAPI ML 서버는 비동기 ORM(SQLAlchemy async)을 사용합니다.
`asyncpg` 드라이버가 없으면 DB 연결 시 런타임 오류가 발생합니다.

---

## 수정 3: BE Dockerfile 신규 작성 + docker-compose.yml 연결

### 3-1. `racepulse/backend/Dockerfile` 신규 작성

Spring Boot 3.5 / Java 21 멀티스테이지 빌드:

```dockerfile
# ── 빌드 스테이지 ─────────────────────────────────────────────
# Gradle Wrapper로 실행 가능한 JAR를 생성합니다.
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /app

# 의존성 캐시를 최대화하기 위해 빌드 설정 파일을 먼저 복사합니다.
COPY gradlew gradlew.bat ./
COPY gradle/ gradle/
COPY build.gradle settings.gradle ./

# 의존성만 먼저 내려받아 Docker 레이어 캐시를 활용합니다.
RUN ./gradlew dependencies --no-daemon || true

# 소스 전체 복사 후 테스트 없이 JAR 빌드
COPY src/ src/
RUN ./gradlew bootJar -x test --no-daemon

# ── 실행 스테이지 ─────────────────────────────────────────────
# JDK 대신 JRE만 포함한 경량 이미지로 전환해 컨테이너 크기를 줄입니다.
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# 보안상 root가 아닌 별도 사용자로 실행합니다.
RUN addgroup -S racepulse && adduser -S racepulse -G racepulse
USER racepulse

# 빌드 스테이지에서 생성된 JAR만 복사합니다.
COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080

# Spring Profile은 Compose에서 환경변수로 주입합니다.
ENTRYPOINT ["java", "-jar", "app.jar"]
```

### 3-2. `racepulse/docker-compose.yml` BE 서비스 수정

현재 임시 이미지로 돼 있는 BE 서비스를 실제 앱으로 교체합니다:

```yaml
backend:
  build:
    context: ./backend          # Dockerfile 위치
    dockerfile: Dockerfile
  ports:
    - "8080:8080"
  environment:
    SPRING_PROFILES_ACTIVE: docker
    SPRING_DATASOURCE_URL: jdbc:postgresql://postgres:5432/racepulse
    SPRING_DATASOURCE_USERNAME: ${DB_USERNAME}
    SPRING_DATASOURCE_PASSWORD: ${DB_PASSWORD}
    JWT_SECRET: ${JWT_SECRET}
  depends_on:
    postgres:
      condition: service_healthy
    redis:
      condition: service_healthy
  restart: unless-stopped
```

**주의**: 기존 `eclipse-temurin:21-jre` 이미지를 직접 쓰던 서비스 정의를 위 내용으로 교체합니다.

---

## 완료 기준

```bash
# 이 명령이 오류 없이 실행되어야 합니다
cd racepulse
docker compose up --build -d

# 헬스체크 확인
curl http://localhost:8080/api/v1/health
# → {"success":true,"data":"OK",...}

curl http://localhost:8000/health
# → {"status":"ok",...}
```

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-1] Docker 실행 재현성 복구`
- 변경 대상 파일 외 수정 금지 (Dockerfile, docker-compose.yml 외)

### Docker 규칙
- `.env` 파일의 실제 값은 절대 수정 금지
- `postgres`, `redis` 서비스 정의 수정 금지
- 기존 네트워크·볼륨 이름 변경 금지
- 주석: 각 스테이지·환경변수에 WHY 설명 한 줄 이상

## 주의사항
- `.env` 파일의 실제 값은 건드리지 마세요
- DB 마이그레이션은 Spring Boot 시작 시 Flyway가 자동 실행합니다
- 기존 `postgres`, `redis` 서비스 정의는 수정하지 마세요
