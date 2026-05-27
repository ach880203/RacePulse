// =============================================================================
// vite.config.ts — Vite 빌드 도구 설정 파일
// =============================================================================
// Vite = React 프로젝트를 빠르게 실행하고 빌드해주는 도구
// plugins에 추가한 것들이 프로젝트에서 활성화됩니다
// =============================================================================

import { existsSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { gzipSync } from 'node:zlib'
// defineConfig = Vite 설정에 타입 힌트를 붙여 오타를 줄여주는 도우미 함수입니다.
import { defineConfig } from 'vitest/config'
// react = Vite가 React의 JSX/TSX 파일을 이해하도록 도와주는 공식 플러그인입니다.
import react from '@vitejs/plugin-react'
// tailwindcss = Tailwind CSS 유틸리티 클래스를 빌드 과정에 연결하는 플러그인입니다.
import tailwindcss from '@tailwindcss/vite'
// compression = 빌드 결과 JS/CSS를 Brotli와 gzip으로 미리 압축해 배포 서버가 작은 파일을 보낼 수 있게 합니다.
import compression from 'vite-plugin-compression'
// VitePWA = 웹앱을 설치 가능한 PWA로 바꿔주는 플러그인입니다.
import { VitePWA } from 'vite-plugin-pwa'
// visualizer = 번들 안에 어떤 라이브러리가 큰지 HTML 보고서로 보여주는 분석 도구입니다.
import { visualizer } from 'rollup-plugin-visualizer'

function splitVendorChunk(id: string) {
  if (!id.includes('node_modules')) {
    return undefined
  }

  if (id.includes('zrender')) {
    return 'vendor-zrender'
  }
  if (id.includes('echarts-for-react')) {
    return 'vendor-echarts-react'
  }
  if (id.includes('echarts/lib/chart') || id.includes('echarts/charts')) {
    return 'vendor-echarts-charts'
  }
  if (id.includes('echarts/lib/component') || id.includes('echarts/components')) {
    return 'vendor-echarts-components'
  }
  if (id.includes('echarts/lib/coord')) {
    return 'vendor-echarts-coord'
  }
  if (id.includes('echarts/lib/scale')) {
    return 'vendor-echarts-scale'
  }
  if (id.includes('echarts/lib/data')) {
    return 'vendor-echarts-data'
  }
  if (id.includes('echarts/renderers')) {
    return 'vendor-echarts-renderers'
  }
  if (id.includes('echarts/core') || id.includes('echarts/lib') || id.includes('echarts')) {
    return 'vendor-echarts-core'
  }
  if (id.includes('@tanstack')) {
    return 'vendor-query'
  }
  if (id.includes('react-router-dom')) {
    return 'vendor-router'
  }
  if (id.includes('react') || id.includes('react-dom')) {
    return 'vendor-react'
  }
  return 'vendor'
}

function gzipCompressionPlugin() {
  const compressibleFilePattern = /\.(js|mjs|json|css|html)$/i

  function collectFiles(directoryPath: string): string[] {
    if (!existsSync(directoryPath)) {
      return []
    }

    return readdirSync(directoryPath).flatMap((fileName) => {
      const filePath = join(directoryPath, fileName)
      const fileStat = statSync(filePath)

      if (fileStat.isDirectory()) {
        return collectFiles(filePath)
      }

      return compressibleFilePattern.test(filePath) ? [filePath] : []
    })
  }

  return {
    name: 'racepulse:gzip-compression',
    apply: 'build' as const,
    closeBundle() {
      // gzip은 Brotli를 지원하지 않는 서버/브라우저를 위한 폴백 압축 파일입니다.
      // vite-plugin-compression을 두 번 쓰면 내부 캐시 때문에 gzip이 생략되어, 이 작은 플러그인으로 보완합니다.
      const outputDirectory = join(process.cwd(), 'dist')
      const files = collectFiles(outputDirectory)

      files.forEach((filePath) => {
        const source = readFileSync(filePath)
        const compressed = gzipSync(source, { level: 9 })
        writeFileSync(`${filePath}.gz`, compressed)
      })
    },
  }
}

export default defineConfig({
  plugins: [
    react(),        // React 지원
    tailwindcss(),  // Tailwind CSS 지원
    // Brotli는 gzip보다 보통 20~30% 더 작게 압축됩니다.
    // 서버가 .br 파일 전송을 지원하면 첫 로딩 네트워크 비용이 줄어듭니다.
    compression({ algorithm: 'brotliCompress', ext: '.br' }),
    // gzip은 오래된 서버/브라우저 환경에서도 널리 지원되는 폴백 압축 방식입니다.
    gzipCompressionPlugin(),
    // VitePWA 설정 블록이 하는 일:
    // 1) manifest 파일을 자동 생성합니다.
    // 2) Service Worker 파일을 빌드 결과물에 포함합니다.
    // 3) 설치 아이콘, 포스터, 영상 같은 정적 파일을 PWA 자산으로 묶습니다.
    VitePWA({
      // autoUpdate = 새 버전이 올라왔을 때 Service Worker를 자동 갱신해
      // 사용자가 오래된 파일을 계속 보는 상황을 줄여줍니다.
      registerType: 'autoUpdate',
      // includeAssets = manifest에 직접 적지 않은 정적 파일도 함께 보존할 목록입니다.
      includeAssets: [
        'favicon.ico',
        'icon-192x192.png',
        'icon-512x512.png',
        'intro-poster.jpg',
        'intro-poster.webp',
        'intro-video.mp4',
        'intro-video.webm',
      ],
      manifest: {
        // 홈 화면에 보이는 앱 이름은 사용자 UI이므로 프로젝트 규칙에 맞춰 한글로 둡니다.
        name: '레이스펄스',
        short_name: '레이스펄스',
        description: '경마 데이터 분석 & 예측 플랫폼',
        // theme/background color를 같은 값으로 맞춘 이유:
        // 설치 화면과 앱 실행 배경이 브랜드 네이비 톤으로 일관되게 보이게 하기 위해서입니다.
        theme_color: '#080e1f',
        background_color: '#080e1f',
        // standalone = 주소창이 없는 앱 같은 화면으로 열어
        // "웹페이지"보다 "설치 앱"에 가까운 느낌을 만들기 위한 핵심 설정입니다.
        display: 'standalone',
        // 세로형 서비스 성격이 강하므로 portrait로 고정합니다.
        orientation: 'portrait',
        start_url: '/',
        icons: [
          {
            src: '/icon-192x192.png',
            sizes: '192x192',
            type: 'image/png',
          },
          {
            src: '/icon-512x512.png',
            sizes: '512x512',
            type: 'image/png',
          },
        ],
      },
      // devOptions.enabled: false = 개발 서버에서는 Service Worker를 비활성화합니다.
      // 이유: dev 모드에서 sw.js 파일이 아직 생성되지 않아 오류가 발생하기 때문입니다.
      // PWA 기능(오프라인, 설치)은 npm run build 후 프로덕션 환경에서만 동작합니다.
      devOptions: {
        enabled: false,
      },
      // Service Worker란?
      //   브라우저 안에서 네트워크 요청을 도와주는 "오프라인 비서"입니다.
      //   한 번 받은 경주 목록/이미지를 캐시에 보관했다가 재방문 시 더 빠르게 보여줄 수 있습니다.
      workbox: {
        runtimeCaching: [
          {
            urlPattern: /\/api\/v1\/races/,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'api-races',
              expiration: {
                maxEntries: 80,
                maxAgeSeconds: 60 * 60,
              },
            },
          },
          {
            urlPattern: /\.(?:png|jpg|jpeg|webp|svg)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'racepulse-images',
              expiration: {
                maxEntries: 120,
                maxAgeSeconds: 24 * 60 * 60,
              },
            },
          },
        ],
      },
    }),
    // 번들 분석 파일은 dist/bundle-analysis.html에 생성됩니다.
    // 자동으로 브라우저를 열지 않아 CI나 터미널 빌드에서도 방해가 없습니다.
    visualizer({
      filename: 'dist/bundle-analysis.html',
      open: false,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
  server: {
    port: 3000,
  },
  optimizeDeps: {
    // 개발 서버에서 대시보드에 처음 진입할 때 ECharts 래퍼를 즉시 변환하면
    // Vite 의존성 캐시 상태에 따라 동적 import가 500으로 실패할 수 있어 미리 최적화합니다.
    include: ['echarts', 'echarts/core', 'echarts-for-react/lib/core'],
  },
  build: {
    // chunkSizeWarningLimit은 경고 기준을 낮추거나 숨기는 용도가 아닙니다.
    // 목표가 500KB 미만이므로 기본 기준을 그대로 명시해 CI에서 초과를 빠르게 알아차립니다.
    chunkSizeWarningLimit: 500,
    rollupOptions: {
      // treeshake = 사용하지 않는 export를 번들에서 제거하는 Rollup 최적화입니다.
      // ECharts core import와 함께 쓰면 차트 라이브러리 크기 절감 효과가 커집니다.
      treeshake: true,
      output: {
        // manualChunks = 큰 라이브러리를 기능별 파일로 나눠 특정 화면에서만 내려받도록 돕는 설정입니다.
        // 라우트 Lazy Loading과 함께 쓰면 초기 진입 청크가 작아집니다.
        manualChunks: splitVendorChunk,
      },
    },
    rolldownOptions: {
      output: {
        // Vite 8은 내부 빌드 엔진이 Rolldown이므로 같은 청크 분리 규칙을 Rolldown에도 전달합니다.
        manualChunks: splitVendorChunk,
      },
    },
  },
  // Vitest 설정 — 테스트 전용 옵션입니다. 빌드/개발 서버에는 영향 없음.
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    globals: true,
    // Tailwind v4(@tailwindcss/vite)는 jsdom 환경과 충돌합니다.
    // CSS 처리 플러그인을 테스트에서 제외합니다.
    // 컴포넌트 테스트는 CSS 렌더링이 아닌 DOM 구조만 검증하므로 문제없습니다.
    css: false,
  },
})
