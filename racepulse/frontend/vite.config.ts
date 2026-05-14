// =============================================================================
// vite.config.ts — Vite 빌드 도구 설정 파일
// =============================================================================
// Vite = React 프로젝트를 빠르게 실행하고 빌드해주는 도구
// plugins에 추가한 것들이 프로젝트에서 활성화됩니다
// =============================================================================

// defineConfig = Vite 설정에 타입 힌트를 붙여 오타를 줄여주는 도우미 함수입니다.
import { defineConfig } from 'vitest/config'
// react = Vite가 React의 JSX/TSX 파일을 이해하도록 도와주는 공식 플러그인입니다.
import react from '@vitejs/plugin-react'
// tailwindcss = Tailwind CSS 유틸리티 클래스를 빌드 과정에 연결하는 플러그인입니다.
import tailwindcss from '@tailwindcss/vite'
// VitePWA = 웹앱을 설치 가능한 PWA로 바꿔주는 플러그인입니다.
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),        // React 지원
    tailwindcss(),  // Tailwind CSS 지원
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
        'intro-video.mp4',
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
    }),
  ],
  server: {
    port: 3000,
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
