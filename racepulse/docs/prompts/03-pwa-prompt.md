# 03. RacePulse PWA 설정 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표
React 앱을 PWA(Progressive Web App)로 만들어 스마트폰 홈 화면에 설치할 수 있게 합니다.
설치하면 앱 아이콘이 생기고, 앱처럼 실행됩니다.

---

## PWA란?
웹사이트를 스마트폰 앱처럼 설치해서 쓸 수 있게 해주는 기술입니다.
- 홈 화면에 아이콘 추가 가능
- 오프라인에서도 일부 기능 사용 가능
- 앱스토어 없이 배포 가능

---

## 프로젝트 환경
- React 18 + TypeScript
- Vite 6.x
- Tailwind CSS v4
- 이미 설치된 패키지: `vite-plugin-pwa` (package.json 확인)
- 포트: 3000

---

## 현재 파일 구조
```
frontend/
├── public/
│   ├── 영상2.mp4
│   ├── intro-poster.jpg
│   └── vite.svg  ← 삭제해도 됨
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── vite.config.ts
└── package.json
```

---

## 구현 사항

### 1. vite.config.ts 수정
`vite-plugin-pwa` 플러그인을 추가합니다.

```ts
// 이런 방식으로 VitePWA 플러그인 추가
import { VitePWA } from 'vite-plugin-pwa'
```

PWA 설정 내용:
- `registerType: 'autoUpdate'` → 새 버전 나오면 자동 업데이트
- `includeAssets` → 아이콘, 영상 파일 포함
- `manifest` → 앱 이름, 색상, 아이콘 등 정보

manifest 설정값:
```
name: 'RacePulse'
short_name: 'RacePulse'
description: '경마 데이터 분석 & 예측 플랫폼'
theme_color: '#080e1f'        (brand-navy-950)
background_color: '#080e1f'   (brand-navy-950)
display: 'standalone'         (앱처럼 전체화면으로 실행)
orientation: 'portrait'       (세로 방향)
start_url: '/'
icons: 아래 아이콘 목록 참고
```

### 2. 아이콘 파일 생성
`frontend/public/` 폴더에 아래 아이콘 파일들이 필요합니다.
지금은 임시로 placeholder 역할을 하는 SVG 파일을 생성해주세요.
(나중에 DESIGN이 실제 아이콘으로 교체 예정)

필요한 파일:
```
frontend/public/
├── icon-192x192.png   ← 스마트폰 홈 화면 아이콘
├── icon-512x512.png   ← 스플래시 화면 아이콘
└── favicon.ico        ← 브라우저 탭 아이콘
```

임시 방법: vite.svg를 복사해서 이름만 바꿔도 됩니다.

### 3. index.html 수정
`<head>` 안에 아래 메타 태그 추가:
```html
<!-- PWA 관련 메타 태그 -->
<meta name="theme-color" content="#080e1f">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="RacePulse">
<link rel="apple-touch-icon" href="/icon-192x192.png">
```

### 4. src/main.tsx 수정
PWA Service Worker 등록 코드 추가:
```tsx
import { registerSW } from 'virtual:pwa-register'
// 자동 업데이트 등록
registerSW({ immediate: true })
```

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- PWA, Service Worker, manifest, registerSW 등 개념을 쉬운 말로 설명
- 각 설정값이 어떤 역할인지 설명
- `display: 'standalone'` 같은 값이 왜 이 값인지 설명
- 모든 import 한 줄 한 줄 설명

---

## 인코딩 주의사항 ⚠️
- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 저장 전 인코딩 확인

---

## 완료 기준
1. `npm run dev` 실행 후 브라우저 주소창 오른쪽에 설치 아이콘(⊕) 표시
2. Chrome 개발자 도구 → Application → Manifest 탭에서 앱 정보 확인
3. Chrome 개발자 도구 → Application → Service Workers 탭에서 SW 등록 확인
4. 모바일 브라우저에서 "홈 화면에 추가" 옵션 표시
