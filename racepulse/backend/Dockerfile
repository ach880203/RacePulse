# -----------------------------------------------------------------------------
# 빌드 스테이지
# -----------------------------------------------------------------------------
# Gradle Wrapper로 실행 가능한 Spring Boot JAR 파일을 생성합니다.
FROM eclipse-temurin:21-jdk-alpine AS builder

WORKDIR /app

# 의존성 내려받기는 시간이 오래 걸리므로, 설정 파일을 먼저 복사해 Docker 캐시를 활용합니다.
COPY gradlew gradlew.bat ./
COPY gradle/ gradle/
COPY build.gradle settings.gradle ./

# Windows에서 복사된 gradlew는 실행 권한이 없을 수 있어 Linux 빌드 단계에서 권한을 보정합니다.
RUN chmod +x gradlew

# 의존성 캐시만 미리 준비합니다. 네트워크나 일부 플러그인 문제로 실패해도 실제 빌드 단계에서 다시 검증됩니다.
RUN ./gradlew dependencies --no-daemon || true

# 소스 전체를 복사한 뒤 테스트 없이 실행용 JAR만 빌드합니다.
COPY src/ src/
RUN ./gradlew bootJar -x test --no-daemon

# -----------------------------------------------------------------------------
# 실행 스테이지
# -----------------------------------------------------------------------------
# JRE만 포함한 이미지로 바꿔 컨테이너 크기를 줄입니다.
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# docker-compose.yml의 curl 기반 헬스체크가 동작하도록 실행 이미지에 curl만 추가합니다.
RUN apk add --no-cache curl

# root 권한 실행을 피하기 위해 애플리케이션 전용 사용자를 만듭니다.
RUN addgroup -S racepulse && adduser -S racepulse -G racepulse
USER racepulse

# 빌드 스테이지에서 생성된 JAR 파일만 실행 이미지로 가져옵니다.
COPY --from=builder /app/build/libs/*.jar app.jar

EXPOSE 8080

# Spring Profile과 DB 접속 정보는 docker-compose.yml의 환경변수로 주입합니다.
ENTRYPOINT ["java", "-jar", "app.jar"]
