// ReactNode = 컴포넌트 태그 사이에 들어오는 JSX 조각(children)의 타입입니다.
import type { ReactNode } from 'react'

// Header = 모든 페이지가 공통으로 공유하는 상단 네비게이션 컴포넌트입니다.
import Header from './Header'

// =============================================================================
// Layout.tsx — 모든 페이지의 공통 뼈대
// =============================================================================
// 왜 따로 분리했나?
// Header와 Footer를 각 페이지마다 반복해서 쓰면 수정 지점이 늘어나고 실수도 많아집니다.
// 공통 레이아웃으로 묶어두면 페이지 내용만 바꿔 끼우면 되므로 유지보수가 쉬워집니다.
// =============================================================================

type LayoutProps = {
  // children = <Layout>여기 안에 들어오는 실제 페이지 본문</Layout> 을 뜻합니다.
  children: ReactNode
}

function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-brand-navy-950 text-white">
      <Header />

      {/* main = 페이지의 핵심 본문 영역입니다.
          flex-1을 주는 이유:
          화면이 길지 않은 페이지도 Footer가 아래쪽에 자연스럽게 붙게 만들기 위해서입니다. */}
      <main className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-7xl flex-col px-4 py-8 sm:px-6 lg:px-8">
        {children}
      </main>

      <footer className="border-t border-white/10 bg-brand-navy-900/60">
        <div className="mx-auto flex max-w-7xl flex-col gap-2 px-4 py-6 text-sm text-white/60 sm:px-6 lg:px-8">
          <p className="font-heading text-lg text-brand-gold-400">레이스펄스</p>
          <p>경마 데이터를 더 읽기 쉽고 빠르게 정리하는 분석 플랫폼</p>
        </div>
      </footer>
    </div>
  )
}

export default Layout
