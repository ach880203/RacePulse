# RacePulse 기술 학습서

이 폴더는 RacePulse 프로젝트에서 실제로 사용하는 기술을 초보자도 따라갈 수 있게 설명하기 위한 문서 모음입니다.

## 읽는 순서

1. [00. 전체 기술 지도](./00-technology-map.md)
2. [01. 프로젝트 아키텍처](./01-project-architecture.md)
3. [02. 몬테카를로 시뮬레이션](./02-monte-carlo.md)
4. [03. Flyway와 데이터베이스 마이그레이션](./03-flyway-database.md)
5. [04. APScheduler와 Redis](./04-apscheduler-redis.md)
6. [05. 프론트엔드, PWA, API 연결](./05-frontend-pwa-api.md)
7. [06. 인증, 카카오 OAuth, JWT, Web Push](./06-auth-push.md)
8. [07. 머신러닝 서버와 데이터 파이프라인](./07-ml-data-pipeline.md)

## 이 문서를 보는 방법

- 먼저 전체 흐름을 보고 싶으면 `00-technology-map.md`와 `01-project-architecture.md`를 먼저 읽습니다.
- 특정 기술만 이해하고 싶으면 해당 주제 문서로 바로 이동해도 됩니다.
- 운영 중 문제가 생겼을 때는 `docs/troubleshooting` 문서와 함께 보면 원인 추적이 쉽습니다.

## RacePulse 기준 핵심 기술

| 영역 | 사용 기술 | 프로젝트 안에서 하는 일 |
| --- | --- | --- |
| 백엔드 API | Spring Boot, Spring Security, JPA | 화면에서 필요한 경주, 예측, 사용자 API 제공 |
| DB 관리 | PostgreSQL, Flyway | 경주/마필/사용자 데이터를 저장하고 스키마 변경 이력을 관리 |
| 캐시/락 | Redis | API 호출 제한, 중복 수집 방지, 임시 데이터 관리 |
| ML 서버 | FastAPI, SQLAlchemy, scikit-learn 계열 | KRA/날씨 데이터 수집, 예측, 몬테카를로 시뮬레이션 수행 |
| 자동 작업 | APScheduler | 정해진 시간에 경주/날씨/해설 데이터를 자동 수집 |
| 프론트엔드 | React, Vite, React Query | 사용자가 보는 화면과 API 데이터 표시 |
| PWA | vite-plugin-pwa, Service Worker | 앱처럼 설치 가능한 웹 경험 제공 |
| 인증/알림 | Kakao OAuth, JWT, Web Push, VAPID | 로그인, 토큰 인증, 브라우저 푸시 알림 제공 |

