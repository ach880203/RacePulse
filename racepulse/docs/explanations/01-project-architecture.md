# 01. 프로젝트 아키텍처

아키텍처는 프로젝트의 큰 구조입니다. RacePulse는 역할별로 세 서버가 나뉩니다.

## 폴더 구조

```text
racepulse/
  backend/      Spring Boot API 서버
  frontend/     React 화면
  ml-server/    FastAPI 기반 데이터 수집/ML 서버
  docs/         문서와 프롬프트
```

## 요청 흐름

### 경주 목록 조회

```text
브라우저
  ↓ GET /api/v1/races
Spring Boot RaceController
  ↓
RaceService
  ↓
PostgreSQL races 테이블
  ↓
JSON 응답
```

사용자는 React 화면에서 경주 목록을 봅니다. React는 `axios` 또는 React Query 기반 API 함수를 통해 Spring Boot에 요청합니다. Spring Boot는 DB를 조회한 뒤 JSON으로 응답합니다.

### 예측/시뮬레이션 조회

```text
브라우저
  ↓ GET /api/v1/predictions/{raceId}/simulation
Spring Boot PredictionController
  ↓
PredictionService
  ↓
FastAPI ML 서버
  ↓
PostgreSQL predictions / monte_carlo_simulations
```

예측 관련 계산은 Python 쪽이 더 적합합니다. 그래서 Spring Boot는 직접 계산하기보다 ML 서버에 요청을 넘기고, 결과를 프론트엔드에 전달합니다.

## 백엔드와 ML 서버를 나눈 이유

Spring Boot는 안정적인 API, 인증, 권한, 사용자 기능에 강합니다. 반면 Python은 데이터 분석, 머신러닝, 수치 계산 라이브러리가 풍부합니다.

RacePulse는 두 장점을 나눠 사용합니다.

| 서버 | 주 역할 | 이유 |
| --- | --- | --- |
| Spring Boot | 사용자 API, 인증, 권한, 일반 조회 | 웹 서비스 백엔드에 적합 |
| FastAPI | 데이터 수집, 예측, 시뮬레이션 | Python ML 생태계 활용 |

## 데이터베이스 중심 구조

PostgreSQL은 여러 서버가 공유하는 중심 저장소입니다.

```text
Spring Boot  → PostgreSQL ← FastAPI
```

주의할 점은 두 서버가 같은 테이블을 만질 수 있다는 것입니다. 그래서 테이블 구조 변경은 가능하면 Flyway로 관리하고, 임의로 런타임에서 테이블을 만드는 방식은 최소화하는 것이 좋습니다.

## Redis의 위치

Redis는 메인 DB가 아닙니다. 사라져도 다시 만들 수 있는 임시 데이터를 다루는 데 적합합니다.

RacePulse에서는 다음 용도에 적합합니다.

- 같은 수집 작업이 동시에 두 번 실행되지 않도록 막는 락
- 하루 외부 API 호출 횟수 카운터
- 짧게 보관해도 되는 캐시
- 스케줄 작업 체크포인트

## 운영 관점에서 중요한 연결

| 연결 | 실패하면 생기는 일 |
| --- | --- |
| 프론트엔드 → Spring Boot | 화면에 데이터 로딩 실패 표시 |
| Spring Boot → PostgreSQL | 대부분의 API 조회 실패 |
| Spring Boot → Redis | 인증/캐시/락 관련 기능 일부 실패 가능 |
| Spring Boot → FastAPI | 예측/시뮬레이션 조회 실패 |
| FastAPI → 외부 KRA/날씨 API | 최신 데이터 수집 실패 |
| FastAPI → PostgreSQL | 수집 데이터 저장 실패 |

## 이 구조에서 디버깅하는 순서

1. 브라우저 개발자 도구에서 요청 URL과 상태 코드를 확인합니다.
2. Spring Boot 로그에서 컨트롤러/서비스 오류를 확인합니다.
3. ML 관련 API라면 FastAPI 로그를 확인합니다.
4. DB 오류라면 Flyway 마이그레이션 적용 여부를 확인합니다.
5. 중복 실행이나 호출 제한 문제라면 Redis 키 상태를 확인합니다.

