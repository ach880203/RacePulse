// React의 StrictMode = 개발 중 위험한 코드 패턴을 더 빨리 발견하게 도와주는 검사 모드입니다.
import { StrictMode } from 'react'
// createRoot = React 화면을 실제 HTML에 연결해 주는 최신 렌더링 시작점입니다.
import { createRoot } from 'react-dom/client'
// registerSW = PWA용 Service Worker를 등록해 설치/오프라인 캐시 기능을 켜는 도구입니다.
import { registerSW } from 'virtual:pwa-register'

// =============================================================================
// React Query 설정
// =============================================================================
// QueryClient = React Query의 데이터 캐시를 관리하는 핵심 객체입니다.
//   모든 API 데이터, 로딩 상태, 에러 상태가 여기에 저장됩니다.
// QueryClientProvider = React Query를 앱 전체에서 사용할 수 있게 연결하는 컴포넌트입니다.
//   BrowserRouter처럼 최상단에 한 번만 감싸줍니다.
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// 전역 CSS 파일입니다. 앱 전체 색상, 폰트, 인트로 스타일이 들어 있습니다.
import './index.css'
// App = 실제 화면 라우팅과 UI를 담고 있는 최상위 컴포넌트입니다.
import App from './App.tsx'

// -----------------------------------------------------------------------------
// QueryClient 생성 및 기본 설정
// -----------------------------------------------------------------------------
// QueryClient를 한 번만 만들어서 앱 전체에서 공유합니다.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // staleTime = 데이터를 "신선하다"고 판단하는 시간입니다.
      // 5분 동안은 같은 API를 다시 호출하지 않습니다.
      staleTime: 5 * 60 * 1000,

      // retry = API 요청이 실패했을 때 몇 번 더 시도할지입니다.
      // 1번만 재시도하고, 그래도 실패하면 오류 상태로 표시합니다.
      retry: 1,

      // refetchOnWindowFocus = 브라우저 탭을 다시 클릭할 때 자동으로 새 데이터를 불러올지 여부입니다.
      // 경마 데이터는 탭 전환마다 재요청할 필요가 없으므로 끕니다.
      refetchOnWindowFocus: false,
    },
  },
})

// Service Worker = 브라우저 뒤에서 조용히 동작하며 파일을 캐시해 주는 작업자라고 생각하면 쉽습니다.
// 개발 환경(import.meta.env.DEV)에서는 vite-plugin-pwa가 sw.js를 생성하지 않으므로
// 프로덕션 빌드에서만 Service Worker를 등록합니다.
if (!import.meta.env.DEV) {
  registerSW({ immediate: true })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {/*
      QueryClientProvider로 App 전체를 감싸야
      모든 컴포넌트에서 useQuery, useMutation 같은 React Query 훅을 쓸 수 있습니다.
    */}
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </StrictMode>,
)
