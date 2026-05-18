# 25. RacePulse 번들 최적화 14단계 프롬프트

> ⚠️ 이 프롬프트를 실행하기 전에 `docs/PROJECT_RULES.md` 파일을 먼저 읽고
> 모든 규칙을 준수하여 코드를 작성해주세요.

---

## 목표

4차 회의 확정사항인 번들 최적화 14단계 레이어드 전략을 구현합니다.
실운영을 위한 성능 기준:
- 초기 로드: LCP(Largest Contentful Paint) < 2.5초
- 번들 크기: 각 청크 500KB 미만 (현재 일부 초과 경고 있음)
- Service Worker로 재방문 시 오프라인/초고속 로딩

---

## 프로젝트 환경

- React 18 / TypeScript / Vite 5
- Tailwind CSS v4
- 폰트: Playfair Display / Inter / JetBrains Mono (Google Fonts)
- 현재 이슈: Vite 빌드 시 500KB 초과 청크 경고 발생

---

## 현재 파일/폴더 구조

```
frontend/
├── src/
│   ├── pages/         ← 라우트별 페이지 컴포넌트
│   ├── components/    ← 공통/동적 UI 컴포넌트
│   ├── api/           ← API 호출
│   └── workers/       ← Web Worker (prompt-23에서 생성)
├── public/
│   ├── intro-video.mp4
│   └── intro-poster.jpg
├── vite.config.ts
├── index.html
└── package.json
```

---

## 구현 사항 — 14단계

---

### 단계 1. Brotli 압축 설정

**패키지**: `vite-plugin-compression`

```typescript
// vite.config.ts
import compression from 'vite-plugin-compression'

plugins: [
  compression({ algorithm: 'brotliCompress', ext: '.br' }),
  compression({ algorithm: 'gzip', ext: '.gz' }),  // 폴백용
]
```

Brotli란? 구글이 만든 압축 방식으로 gzip보다 20~30% 더 작게 압축됩니다.

---

### 단계 2. WebM 비디오 변환

인트로 영상(`public/intro-video.mp4`)의 WebM 버전을 안내합니다.

```tsx
// IntroVideo.tsx
<video>
  <source src="/intro-video.webm" type="video/webm" />  {/* 최우선 */}
  <source src="/intro-video.mp4"  type="video/mp4"  />  {/* 폴백 */}
</video>
```

WebM 변환 명령어를 주석으로 안내:
```bash
# ffmpeg -i intro-video.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 intro-video.webm
```

---

### 단계 3. ECharts 도입 (Recharts 교체)

Recharts → Apache ECharts (`echarts-for-react`)로 교체합니다.
ECharts는 번들 크기가 작고 성능이 더 좋습니다.

교체 대상 컴포넌트:
- `PaceLineChart.tsx` (라인 차트)
- `RatingRadarChart.tsx` (레이더 차트)
- `AccuracyCircleGauge.tsx` (게이지)
- Phase 2 신규 컴포넌트들

패키지 추가: `echarts`, `echarts-for-react`
패키지 제거: `recharts`

---

### 단계 4. 폰트 서브셋

Google Fonts 대신 필요한 문자만 포함한 폰트 파일 사용:

```html
<!-- index.html -->
<!-- 기존: 전체 폰트 로드 -->
<!-- 변경: 필요한 문자 범위만 로드 (display=swap + text 파라미터) -->
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&display=swap&text=RacePulse가-힣" rel="stylesheet">
```

또는 `@font-face` + `unicode-range`로 한국어/영어 구분 로드.

---

### 단계 5. Route 기반 Lazy Loading

**모든 페이지 컴포넌트**를 `React.lazy`로 변경:

```typescript
// App.tsx
const RacePredictionPage = React.lazy(() => import('./pages/race/RacePredictionPage'))
const DashboardPage      = React.lazy(() => import('./pages/DashboardPage'))
// ...모든 페이지 동일하게
```

`<Suspense fallback={<LoadingAnimation />}>` 으로 감쌉니다.

---

### 단계 6. Web Worker 분리

`frontend/src/workers/monte-carlo.worker.ts` 파일이 존재하면 활용,
없으면 Vite `import.meta.url` 방식으로 등록:

```typescript
// 사용 예
const worker = new Worker(
  new URL('../workers/monte-carlo.worker.ts', import.meta.url),
  { type: 'module' }
)
```

---

### 단계 7. 리스트 가상화

경주 목록(`RaceListPage.tsx`)이 100개 이상일 때 성능 저하 방지:

```bash
npm install react-window @types/react-window
```

```tsx
import { FixedSizeList } from 'react-window'
// 전체 목록을 DOM에 다 넣지 않고 화면에 보이는 항목만 렌더링합니다.
```

---

### 단계 8. Service Worker 캐싱 전략

기존 PWA Service Worker (`vite-plugin-pwa`)에 캐싱 전략 추가:

```typescript
// vite.config.ts workbox 설정
workbox: {
  runtimeCaching: [
    {
      // API 응답 캐싱: 경주 목록은 1시간 캐시
      urlPattern: /\/api\/v1\/races/,
      handler: 'StaleWhileRevalidate',
      options: { cacheName: 'api-races', expiration: { maxAgeSeconds: 3600 } }
    },
    {
      // 이미지 캐싱: 말 사진 등
      urlPattern: /\.(png|jpg|webp)$/,
      handler: 'CacheFirst',
      options: { cacheName: 'images', expiration: { maxAgeSeconds: 86400 } }
    }
  ]
}
```

---

### 단계 9. CI 번들 크기 모니터링

`.github/workflows/test.yml` 에 번들 크기 체크 단계 추가:

```yaml
- name: 번들 크기 체크
  run: |
    cd racepulse/frontend
    npm run build
    # 500KB 초과 파일 경고
    find dist/assets -name "*.js" -size +500k -exec echo "경고: {} 파일이 500KB 초과" \;
```

---

### 단계 10. WebP 이미지 최적화

`public/` 의 이미지 파일을 WebP로 변환하고 폴백 제공:

```tsx
<picture>
  <source srcSet="/intro-poster.webp" type="image/webp" />
  <img src="/intro-poster.jpg" alt="RacePulse 인트로" />
</picture>
```

변환 명령어 주석으로 안내:
```bash
# cwebp -q 80 intro-poster.jpg -o intro-poster.webp
```

---

### 단계 11. Tree Shaking 강화

불필요한 전체 import를 named import로 변경:

```typescript
// ❌ 전체 import (번들에 전부 포함됨)
import _ from 'lodash'

// ✅ named import (필요한 함수만 포함)
import { debounce } from 'lodash-es'
```

`vite.config.ts`에 `treeshake: true` 확인.

---

### 단계 12. Dynamic Import (Heavy 컴포넌트)

무거운 컴포넌트를 조건부 로드:

```tsx
const CounterfactualUI = React.lazy(
  () => import('./components/dynamic/CounterfactualUI')
)
// 사용자가 "가상 시나리오" 탭을 클릭할 때만 로드됩니다.
```

---

### 단계 13. Preload 핵심 자원

중요 자원을 미리 불러오기:

```html
<!-- index.html -->
<link rel="preload" href="/intro-video.mp4"    as="video" />
<link rel="preload" href="/intro-poster.jpg"   as="image" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="dns-prefetch" href="http://localhost:8080" />
```

---

### 단계 14. 번들 시각화 도구 설정

빌드 결과물을 시각적으로 분석:

```bash
npm install -D rollup-plugin-visualizer
```

```typescript
// vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer'

plugins: [
  visualizer({
    filename: 'dist/bundle-analysis.html',
    open: false,   // CI에서는 자동 열지 않음
    gzipSize: true,
    brotliSize: true,
  })
]
```

`npm run build` 후 `dist/bundle-analysis.html` 열어서 큰 파일 식별.

---

## 주석 요구사항 ⚠️ 반드시 지켜주세요

이 프로젝트의 개발자는 **코딩 입문자**입니다.
**학생을 가르친다는 생각**으로 모든 코드에 한국어 주석을 달아주세요.

- 번들(Bundle)이 무엇인지 쉽게 설명
- Lazy Loading이 왜 성능에 좋은지 설명
- `React.lazy`와 `Suspense`의 관계 설명
- Service Worker가 뭔지 쉽게 설명 (오프라인 비서 비유)
- Tree Shaking이 무엇인지 설명 (나무에서 죽은 잎 떨어뜨리기 비유)
- 각 최적화 단계가 실제로 얼마나 효과가 있는지 설명
- Vite 설정 파일(`vite.config.ts`) 옵션들 설명

---

## 인코딩 주의사항 ⚠️

- 모든 파일은 **UTF-8 (BOM 없음)** 으로 저장
- 한글 주석이 깨지지 않도록 저장 전 확인

---

## Git 규칙

```
브랜치: feat/phase2-fe-bundle-optimization
커밋 메시지: feat: [prompt-25] 번들 최적화 14단계 구현 (Brotli/Lazy/SW캐싱/가상화 등)
```

---

## 완료 기준

```bash
cd racepulse/frontend

# 1. 빌드 성공
npm run build
# → dist/ 생성, 500KB 초과 청크 경고 없음

# 2. 번들 분석
# → dist/bundle-analysis.html 생성 확인

# 3. 주요 청크 크기 확인
ls -la dist/assets/*.js | sort -k5 -n
# → 가장 큰 청크 500KB 미만 확인
```
