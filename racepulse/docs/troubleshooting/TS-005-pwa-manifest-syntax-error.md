# TS-005 | manifest.webmanifest: Line 1, column 1, Syntax error

- **발생일:** 2026-05-11
- **서버:** React 프론트엔드 (Vite dev, 포트 3000)
- **위치:** 브라우저 콘솔

---

## 에러 메시지

```
manifest.webmanifest:1 Manifest: Line: 1, column: 1, Syntax error.

(index):1 <meta name="apple-mobile-web-app-capable" content="yes"> is deprecated.
          Please include <meta name="mobile-web-app-capable" content="yes">
```

---

## 원인

### 에러 1: manifest.webmanifest Syntax Error

`vite-plugin-pwa`는 `npm run build` 시 `dist/index.html`에
`<link rel="manifest" href="/manifest.webmanifest">`를 자동으로 삽입한다.

**dev 서버에서 `devOptions.enabled: false`로 설정했을 때의 문제:**
- 브라우저가 `/manifest.webmanifest` 파일을 요청
- dev 서버에 해당 파일이 없음 → HTML 형태의 404 응답을 반환
- 브라우저가 이 HTML을 JSON으로 파싱 시도 → `Line 1, column 1 Syntax error`

```
브라우저 요청: GET /manifest.webmanifest
실제 서버 응답: <!DOCTYPE html>... (404 HTML 페이지)
브라우저 해석: JSON 파싱 시도 → < 문자에서 즉시 Syntax Error
```

### 에러 2: apple-mobile-web-app-capable deprecated

`index.html`에 Apple 전용 구형 태그만 있었고, 표준 태그가 누락되어 있었다.

```html
<!-- 수정 전: Apple 전용 태그만 있음 (deprecated 경고 발생) -->
<meta name="apple-mobile-web-app-capable" content="yes" />
```

---

## 해결 방법

### 수정 1: public/manifest.webmanifest 정적 파일 생성

`public/` 폴더의 파일은 Vite가 dev/prod 모두에서 정적으로 서빙한다.
여기에 `manifest.webmanifest`를 만들면 dev 서버에서도 항상 올바른 JSON을 반환한다.

**`frontend/public/manifest.webmanifest` 생성:**
```json
{
  "name": "레이스펄스",
  "short_name": "레이스펄스",
  "description": "경마 데이터 분석 & 예측 플랫폼",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#080e1f",
  "theme_color": "#080e1f",
  "lang": "ko",
  "scope": "/",
  "orientation": "portrait",
  "icons": [
    { "src": "/icon-192x192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512x512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

> `vite.config.ts`의 `manifest` 설정과 내용을 동일하게 유지해야 한다.
> 둘 중 하나를 바꾸면 나머지도 함께 바꿔야 한다.

### 수정 2: index.html 메타 태그 수정

```html
<!-- 수정 전 -->
<meta name="apple-mobile-web-app-capable" content="yes" />

<!-- 수정 후: 표준 태그 추가, Apple 태그는 하위 호환을 위해 유지 -->
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
```

| 태그 | 대상 | 상태 |
|------|------|------|
| `mobile-web-app-capable` | Android Chrome (표준) | 현행 표준 |
| `apple-mobile-web-app-capable` | iOS Safari | Deprecated (하위 호환용 유지) |

---

## 수정 전 / 수정 후

### 수정 전 (에러)

```
public/
  favicon.ico
  icon-192x192.png    ← manifest 없음!
  icon-512x512.png

브라우저: GET /manifest.webmanifest → 404 HTML → Syntax Error
```

### 수정 후 (정상)

```
public/
  favicon.ico
  icon-192x192.png
  icon-512x512.png
  manifest.webmanifest  ← 추가!

브라우저: GET /manifest.webmanifest → 유효한 JSON → 정상 파싱
```

---

## 교훈: vite-plugin-pwa + devOptions 주의사항

| 설정 | 동작 |
|------|------|
| `devOptions.enabled: true` | dev 서버에서 SW + manifest 모두 가상 서빙 |
| `devOptions.enabled: false` | SW 비활성화, manifest는 **직접 파일 필요** |

`devOptions.enabled: false`로 설정할 경우 반드시 `public/manifest.webmanifest`를 수동으로 생성해야 한다.
