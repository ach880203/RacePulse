# Codex 프롬프트 — Phase 4-2: BE SecurityConfig + API 구현

## 작업 개요
Spring Boot 백엔드에서 현재 403/500 오류가 나는 API들을 수정하고,
없는 컨트롤러를 구현합니다.

## 기술 스택
- Spring Boot 3.5 / Java 21
- JPA + QueryDSL / PostgreSQL 16
- 공통 응답: `ApiResponse<T>` 래퍼 (기존 코드 확인 후 동일하게 사용)
- 인증: Spring Security + JWT (기존 SecurityConfig 확인 후 수정)

## 프로젝트 구조
```
racepulse/backend/src/main/java/com/racepulse/backend/
├── config/
│   └── SecurityConfig.java          ← 수정 대상
├── domain/
│   ├── race/
│   │   ├── controller/RaceController.java
│   │   ├── service/RaceService.java
│   │   └── dto/
│   ├── horse/
│   │   └── controller/HorseController.java  ← 확인 (500 원인)
│   ├── jockey/
│   │   └── controller/               ← 신규 구현
│   ├── trainer/
│   │   └── controller/               ← 신규 구현
│   └── racecourse/
│       └── controller/RacecourseController.java  ← 확인 (500 원인)
```

---

## 수정 1: SecurityConfig 공개 경로 추가

**파일**: `SecurityConfig.java`

아래 경로들을 `permitAll()` 목록에 추가하세요:
```
/api/v1/home
/api/v1/jockeys/**
/api/v1/trainers/**
```

현재 이 경로들이 인증 필요로 설정돼 있어 비로그인 사용자에게 403이 반환됩니다.

---

## 수정 2: `/horses/{id}` 500 → 정상 동작

`HorseController.java` 또는 `HorseService.java`를 확인해서:
- ID로 말 단건 조회 구현
- 해당 ID가 없을 경우 500 대신 **404 ResponseStatus** 반환
- 404 응답 형식: `ApiResponse` 래퍼 사용

```java
// 없는 경우 예시
throw new ResponseStatusException(HttpStatus.NOT_FOUND, "해당 말을 찾을 수 없습니다.");
```

---

## 수정 3: `/jockeys/{id}` 구현 (신규)

기수 단건 조회 엔드포인트를 구현합니다.
기존 Jockey 엔티티/리포지토리가 있다면 그것을 사용하고, 없으면 Horse 도메인을 참고해서 작성합니다.

응답 필드 (최소):
```json
{
  "id": 1,
  "name": "기수명",
  "birthDate": "1990-01-01",
  "nationality": "KR",
  "licenseNo": "J001",
  "recentWinRate": 0.32
}
```

없는 경우 404 반환.

---

## 수정 4: `/trainers/{id}` 구현 (신규)

jockeys와 동일한 패턴으로 구현합니다.

응답 필드 (최소):
```json
{
  "id": 1,
  "name": "조교사명",
  "licenseNo": "T001",
  "stableLocation": "서울",
  "recentTop3Rate": 0.45
}
```

---

## 수정 5: `/racecourses/{meetCode}` 500 수정

`RacecourseController.java`를 확인해서:
- meetCode로 단건 조회 구현
- 없는 경우 404 반환

---

## 수정 6: `/races/upcoming` 500 수정

`RaceService.java`의 upcoming 쿼리를 확인하고 오류를 수정합니다.
오늘 날짜 이후의 SCHEDULED 상태 경주를 최대 20개 반환해야 합니다.

---

## 수정 7: `/races/results` 500 수정

최근 완료된 경주(COMPLETED) 목록을 날짜 내림차순으로 반환하는 쿼리를 수정합니다.

---

## 수정 8: `/dashboard/weekly` 500 수정

주간 집계 쿼리 수정. 이번 주 예측 결과 요약 데이터를 반환해야 합니다.

---

## ⚠️ 프로젝트 필수 규칙

### 커밋
- 커밋 메시지: `feat: [prompt-2] BE API 403/500 수정`

### BE 코딩 규칙
- **예외 처리**: `ResponseStatusException` 사용 금지 — 반드시 `BusinessException(ErrorCode.XXX)` 사용
  - 필요한 ErrorCode가 없으면 `global/exception/ErrorCode.java` enum에 추가 후 사용
  - 예: `throw new BusinessException(ErrorCode.HORSE_NOT_FOUND);`
- **공통 응답**: `ApiResponse.success(data)` 래퍼 필수 / 목록은 `PageResponse<T>` 사용
- **URL prefix**: `/api/v1/` 전체 적용 — 누락 금지
- **민감키 노출 금지**: `application-dev.yaml`에 실제 키·비밀번호 기본값 하드코딩 금지
- **화면 표시 문구**: 응답 message 필드 한국어 필수
- **주석**: 메서드마다 WHY를 설명하는 주석 한 줄 이상
- **도메인 구조**: Controller → Service → Repository 패턴 유지

## 코드 작성 규칙
1. **주석 필수**: 메서드/클래스마다 왜 이렇게 구현했는지 한 줄 이상 주석
2. **공통 응답**: 반드시 기존 `ApiResponse<T>` 래퍼 사용
3. **예외 처리**: 404는 `BusinessException(ErrorCode.XXX)` 사용, 500은 발생하지 않도록
4. **한글 에러 메시지**: 응답 message 필드는 한국어
5. 새 파일 작성 시 기존 도메인 구조(Controller → Service → Repository) 패턴 동일하게 적용

## 완료 기준
```bash
curl http://localhost:8080/api/v1/home              # 200
curl http://localhost:8080/api/v1/jockeys/1         # 200 또는 404
curl http://localhost:8080/api/v1/trainers/1        # 200 또는 404
curl http://localhost:8080/api/v1/horses/1          # 200 또는 404 (500 아님)
curl http://localhost:8080/api/v1/races/upcoming    # 200
curl http://localhost:8080/api/v1/races/results     # 200
curl http://localhost:8080/api/v1/dashboard/weekly  # 200
```
