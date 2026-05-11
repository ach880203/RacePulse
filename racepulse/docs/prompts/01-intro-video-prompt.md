# 01. RacePulse 인트로 영상 연동 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

## 목표
React + TypeScript 프로젝트에 인트로 영상 컴포넌트를 구현합니다.

---

## 프로젝트 기술 스택
- React 18 + TypeScript
- Vite
- Tailwind CSS v4 (브랜드 토큰: brand-navy-950, brand-gold-400 등)
- React Router v6

---

## 파일 준비 사항
아래 두 파일이 `frontend/public/` 폴더에 있어야 합니다.
- `영상2.mp4` (6초, 6.4MB, 인트로 영상 원본)
- `intro-poster.jpg` (영상 1번째 프레임 정지 이미지)

---

## 구현 사항

### 1. IntroVideo 컴포넌트 생성
`frontend/src/components/IntroVideo.tsx` 파일을 생성해주세요.

**동작 방식:**
1. 페이지 진입 시 localStorage에 `racepulse_intro_watched` 키 확인
2. 값이 있으면 (이미 본 경우) → 인트로 건너뜀, 바로 메인 화면
3. 값이 없으면 (처음 방문) → 인트로 영상 표시

**영상 재생 로직:**
- `preload="auto"` → 페이지 진입 즉시 백그라운드에서 영상 로딩 시작
- `poster="intro-poster.jpg"` → 영상 로딩 전 검은 화면 대신 첫 프레임 이미지 표시
- `canplaythrough` 이벤트 → 영상이 완전히 버퍼링된 후에만 재생 시작
- `onEnded` → 영상 재생 완료 시 메인 페이지로 자연스럽게 전환
- **10초 타임아웃** → 느린 환경에서 10초 안에 버퍼링 안 되면 자동으로 스킵

**로딩 중 표시:**
- 화면 중앙에 골드 색상 프로그레스 바 표시
- 프로그레스 바 아래 "Loading RacePulse..." 텍스트
- 배경은 다크 네이비 (brand-navy-950)

**영상 재생 화면:**
- 영상이 전체 화면을 꽉 채우도록 (object-fit: cover)
- 우측 하단에 "Skip" 버튼 (클릭 시 바로 메인 전환)
- 배경은 다크 네이비

**전환 효과:**
- 영상 종료 또는 스킵 시 → 페이드 아웃 후 메인 화면으로 전환
- localStorage에 `racepulse_intro_watched = "true"` 저장

---

### 2. App.tsx 수정
홈 경로(`/`)에서 IntroVideo 컴포넌트를 조건부 렌더링합니다.
- localStorage 체크 후 인트로 미시청 → IntroVideo 컴포넌트 렌더링
- 인트로 완료 또는 기시청 → 홈 대시보드 렌더링

---

## 디자인 스펙

| 항목 | 값 |
|------|-----|
| 배경색 | `var(--color-brand-navy-950)` (#080e1f) |
| 프로그레스 바 색상 | `var(--color-brand-gold-400)` (#f5c842) |
| 로딩 텍스트 색상 | 흰색 |
| Skip 버튼 | 반투명 흰색 배경, 흰색 텍스트 |
| 전환 애니메이션 | fadeOut 0.5초 |

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
코드를 작성할 때 **학생을 가르친다는 생각**으로 주석을 달아주세요.
나중에 개발자가 코드를 보면서 혼자 리뷰하고 이해할 수 있어야 합니다.

**주석 작성 기준:**
- 모든 코드에 한국어 주석 필수 (영어 주석 금지)
- import 한 줄 한 줄마다 "이게 뭐하는 라이브러리인지" 설명
- 함수/변수 하나하나 "왜 있는지, 무슨 역할인지" 설명
- `canplaythrough`, `preload`, `localStorage`, `useEffect`, `useState` 등
  처음 보는 개념은 반드시 쉬운 말로 풀어서 설명
- "이게 뭔지(WHAT)"뿐 아니라 "왜 이렇게 했는지(WHY)"도 설명
- 코드 블록 시작 전에 "이 블록이 하는 일" 요약 주석 포함

**예시 (이런 스타일로):**
```tsx
// useEffect = 컴포넌트가 화면에 나타났을 때 자동으로 실행되는 함수
// 두 번째 인자 [] = 처음 한 번만 실행하겠다는 의미
useEffect(() => {
  // localStorage = 브라우저에 데이터를 저장하는 공간
  // 탭을 닫아도 데이터가 유지됨 (로그인 상태 유지와 비슷한 원리)
  const watched = localStorage.getItem('racepulse_intro_watched')
  ...
}, [])

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 인코딩**으로 저장할 것
- Windows 환경에서는 반드시 **BOM 없는 UTF-8 (UTF-8 without BOM)** 사용
- 한글 주석과 한글 문자열이 깨지지 않도록 저장 전 인코딩 확인
- VS Code 기준: 우측 하단 인코딩 클릭 → "UTF-8" 확인

---

## 완료 기준
1. `http://localhost:3000` 최초 접속 시 인트로 영상 재생
2. 영상 종료 후 홈 대시보드로 전환
3. 재방문 시 인트로 영상 건너뜀
4. 브라우저 개발자 도구 → Application → localStorage에 `racepulse_intro_watched` 키 생성 확인
5. Skip 버튼 동작 확인
