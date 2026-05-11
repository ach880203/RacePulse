# 20. RacePulse 유저 마이페이지 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
로그인한 유저의 프로필, 즐겨찾기, 알림 설정 페이지를 구현합니다.
로그인 상태 관리와 로그아웃 기능도 함께 구현합니다.

---

## 프로젝트 환경
- React 18 + TypeScript + Vite
- Tailwind CSS v4
- @tanstack/react-query
- React Router v6
- Spring Boot API: http://localhost:8080/api/v1

---

## 관련 Spring Boot API
```
GET    /api/v1/auth/me                       ← 내 정보 조회
POST   /api/v1/auth/logout                   ← 로그아웃
GET    /api/v1/user/favorites                ← 즐겨찾기 목록
POST   /api/v1/user/favorites                ← 즐겨찾기 추가
DELETE /api/v1/user/favorites/{id}           ← 즐겨찾기 삭제
GET    /api/v1/user/history                  ← 조회 이력
PATCH  /api/v1/user/preferences              ← 설정 변경
GET    /api/v1/user/notifications            ← 알림 설정 조회
PATCH  /api/v1/user/notifications/{type}     ← 알림 설정 변경
```

---

## 구현 파일 목록

### 1. 인증 상태 관리
`src/store/authStore.ts`
- 로그인 유저 정보 전역 관리 (Zustand 또는 Context API)
- Access Token 저장 및 관리
- 로그인/로그아웃 액션

### 2. 프로필 페이지
`src/pages/user/ProfilePage.tsx` → 라우트: `/profile`

구성:
```
① 프로필 카드
   - 닉네임
   - 이메일
   - 가입 방법 (이메일 / 카카오)
   - 가입일

② 활동 요약
   - 즐겨찾기 수
   - 최근 조회한 경주마 수

③ 설정 메뉴
   - 알림 설정 → /settings 이동
   - 즐겨찾기 → /favorites 이동
   - 로그아웃 버튼 (클릭 시 확인 모달 후 로그아웃)
```

### 3. 즐겨찾기 페이지
`src/pages/user/FavoritesPage.tsx` → 라우트: `/favorites`

구성:
```
① 탭: 경주마 / 기수 / 경주
② 즐겨찾기 목록 (타입별)
③ 각 항목 우측: 즐겨찾기 해제 버튼 (하트 아이콘)
④ 빈 상태: "즐겨찾기한 항목이 없습니다"
```

### 4. 알림 설정 페이지
`src/pages/user/SettingsPage.tsx` → 라우트: `/settings`

구성:
```
① 알림 설정 섹션
   - 경주 시작 알림 (토글 스위치)
   - 기수변경 알림 (토글 스위치)
   - 경주 결과 알림 (토글 스위치)

② 화면 설정
   - 다크/라이트 모드 토글 (user_preferences.theme)

③ 계정 설정
   - 닉네임 변경
```

### 5. 즐겨찾기 버튼 컴포넌트
`src/components/FavoriteButton.tsx`
- props: `targetType: 'HORSE' | 'JOCKEY' | 'RACE'`, `targetId: number`
- 로그인 시: 하트 아이콘 (즐겨찾기 추가/해제 토글)
- 비로그인 시: 클릭하면 로그인 페이지로 이동

### 6. 로그인 보호 라우트
`src/components/PrivateRoute.tsx`
- 로그인하지 않은 상태에서 `/profile`, `/favorites`, `/settings` 접근 시
- `/login` 페이지로 리다이렉트

---

## 다크/라이트 모드 토글
```tsx
// index.css에 라이트 모드 추가
// html.light 클래스 시 라이트 모드 적용
// 토글 시 html 태그에 'light' 클래스 추가/제거
// user_preferences.theme에 저장
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 전역 상태 관리가 왜 필요한지 설명 (Context API 또는 Zustand 개념)
- Access Token을 어디에 저장하는지와 보안상 이유 설명
- PrivateRoute (보호된 라우트) 개념 설명
- 토글 스위치 구현 방법 설명
- 다크/라이트 모드 CSS 클래스 전환 원리 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석/문자열이 깨지지 않도록 확인

---

## 완료 기준
1. `/profile` 로그인한 유저 정보 표시
2. `/favorites` 즐겨찾기 목록 표시 + 해제 버튼 동작
3. `/settings` 알림 토글 설정 저장 확인
4. 로그아웃 후 `/` 홈으로 이동 확인
5. 비로그인 상태에서 `/profile` 접근 시 `/login` 리다이렉트 확인
6. 다크/라이트 모드 토글 동작 확인
