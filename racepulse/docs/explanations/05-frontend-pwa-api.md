# 05. 프론트엔드, PWA, API 연결

프론트엔드는 사용자가 직접 보는 영역입니다. RacePulse에서는 React와 Vite를 사용합니다.

## 주요 기술

| 기술 | 역할 |
| --- | --- |
| React | 화면 컴포넌트 구성 |
| Vite | 개발 서버와 빌드 |
| TypeScript | 타입으로 실수 줄이기 |
| React Router | 페이지 이동 |
| React Query | API 데이터 요청/캐시 |
| Axios | HTTP 요청 |
| PWA | 웹앱 설치와 오프라인 기반 기능 |

## API 연결 흐름

```text
페이지 컴포넌트
  ↓
커스텀 훅
  ↓
API 함수
  ↓
axiosInstance
  ↓
Spring Boot API
```

예를 들어 경주 목록 화면은 대략 다음 흐름으로 동작합니다.

```text
RaceListPage
  ↓
useRaces
  ↓
raceApi
  ↓
GET /api/v1/races
```

## React Query가 하는 일

React Query는 API 요청 상태를 관리합니다.

화면에서 직접 `loading`, `error`, `data`를 매번 구현하면 코드가 복잡해집니다. React Query는 이 패턴을 정리해줍니다.

```text
isLoading: 아직 불러오는 중
isError: 요청 실패
data: 성공한 응답 데이터
refetch: 다시 불러오기
```

## Axios 인스턴스

Axios 인스턴스는 API 요청의 공통 설정을 모아둔 객체입니다.

주로 다음 설정이 들어갑니다.

- 기본 API 주소
- 요청 헤더
- JWT 토큰 자동 첨부
- 에러 공통 처리

## CORS가 필요한 이유

개발 중에는 프론트엔드와 백엔드 주소가 다릅니다.

```text
프론트엔드: http://localhost:5173
백엔드: http://localhost:8080
```

브라우저는 보안상 다른 출처로 요청할 때 CORS 설정을 검사합니다. 백엔드가 허용 헤더를 내려주지 않으면 브라우저가 요청을 차단합니다.

## PWA란

PWA는 Progressive Web App의 약자입니다. 웹사이트를 앱처럼 사용할 수 있게 해주는 방식입니다.

RacePulse에서는 다음 기능과 관련됩니다.

- 홈 화면 설치
- 앱 아이콘과 이름
- Service Worker
- 푸시 알림 기반 준비

## Service Worker란

Service Worker는 브라우저 뒤에서 동작하는 작은 스크립트입니다.

주로 다음 역할을 합니다.

- 정적 파일 캐시
- 오프라인 응답 처리
- 푸시 알림 수신

주의할 점은 Service Worker가 캐시를 사용하기 때문에, 새 배포 후에도 예전 파일이 남아 보일 수 있다는 것입니다. 개발 중 이상한 화면이 보이면 브라우저의 애플리케이션 탭에서 Service Worker와 캐시를 확인합니다.

## Vite PWA에서 자주 나는 문제

### `sw.js` 파일 없음

개발 모드에서 PWA 플러그인이 Service Worker 파일을 찾으려 할 때 설정이 맞지 않으면 `dev-dist/sw.js` 관련 오류가 날 수 있습니다.

확인할 항목은 다음과 같습니다.

- `vite.config.ts`의 PWA 개발 모드 설정
- `public/manifest.webmanifest` 존재 여부
- Service Worker 생성 방식
- 개발 서버 재시작 여부

## 번들 크기 경고

Vite 빌드에서 500KB 초과 청크 경고가 날 수 있습니다. 빌드 실패는 아니지만, 초기 로딩 속도에 영향을 줄 수 있습니다.

개선 방법은 다음과 같습니다.

- 페이지 단위 lazy loading
- 차트 라이브러리 분리
- 데모 페이지를 별도 청크로 분리
- 사용하지 않는 컴포넌트 제거

## 한글 UI 주의사항

RacePulse 규칙상 화면에 표시되는 문구는 반드시 한글이어야 합니다.

프론트엔드 작업 시 다음을 확인합니다.

- 버튼, 라벨, 빈 상태, 오류 메시지가 한글인지 확인
- API 에러 메시지를 그대로 노출할 때 영어가 나오지 않는지 확인
- 폰트가 한글을 안정적으로 표시하는지 확인
- JSON 응답과 화면 출력에서 한글이 깨지지 않는지 확인

