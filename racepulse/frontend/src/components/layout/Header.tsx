// ReactNode를 직접 쓰지는 않지만, 이 파일은 React 컴포넌트를 만드는 JSX 파일입니다.
// modern React 환경에서는 import 없이도 JSX를 쓸 수 있지만, 아래 라우터 import 설명과 흐름을 맞추기 위해 파일 맥락을 분명히 둡니다.
// react-router-dom의 Link = 페이지 전체 새로고침 없이 앱 내부 주소로 이동시키는 링크입니다.
// react-router-dom의 NavLink = 현재 URL과 맞는 메뉴에 "활성 상태 스타일"을 주기 쉬운 링크입니다.
import { Link, NavLink } from 'react-router-dom'

// =============================================================================
// Header.tsx — 모든 페이지 상단에 공통으로 보이는 헤더
// =============================================================================
// 이 헤더의 역할:
// 1) 사용자가 주요 메뉴(홈/경주/경주마/대시보드)로 빠르게 이동하게 돕습니다.
// 2) 브랜드 이름과 톤을 처음부터 분명하게 보여줍니다.
// 3) 모바일 화면에서도 메뉴가 줄바꿈되며 자연스럽게 보이도록 Mobile First로 구성합니다.
// =============================================================================

// 메뉴 정의를 배열로 빼두면 나중에 메뉴를 추가/삭제할 때 JSX를 여러 줄 수정하지 않아도 됩니다.
const navigationItems = [
  { to: '/', label: '홈' },
  { to: '/races', label: '경주' },
  { to: '/horses', label: '경주마' },
  { to: '/dashboard', label: '대시보드' },
]

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-brand-navy-950/95 backdrop-blur-md">
      {/* --------------------------------------------------------------------
          이 블록이 하는 일:
          로고, 메뉴, 로그인 버튼을 한 줄 안에 배치합니다.
          모바일 우선이라 기본은 세로에 가까운 여백 기준으로 두고,
          sm: 이상 화면부터 조금 더 넓게 보여주도록 여백을 늘렸습니다.
          -------------------------------------------------------------------- */}
      <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-4 py-4 sm:px-6 lg:px-8">
        <Link to="/" className="flex items-center gap-3 text-white">
          {/* 간단한 원형 마크는 실제 로고 전 임시 브랜드 포인트 역할을 합니다. */}
          <span className="flex h-10 w-10 items-center justify-center rounded-full border border-brand-gold-400/70 bg-brand-navy-900 text-sm font-semibold text-brand-gold-400">
            RP
          </span>
          <span className="flex flex-col">
            <span className="font-heading text-2xl leading-none text-brand-gold-400">
              레이스펄스
            </span>
            <span className="text-xs tracking-[0.24em] text-white/55">
              DATA RACING PLATFORM
            </span>
          </span>
        </Link>

        {/* nav = 주요 탐색 메뉴 묶음입니다.
            flex-wrap을 준 이유:
            모바일에서 가로 공간이 부족할 때 메뉴가 아래 줄로 내려가도 레이아웃이 깨지지 않게 하기 위해서입니다. */}
        <nav className="flex flex-wrap items-center gap-2 text-sm sm:gap-3">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  'rounded-full px-4 py-2 transition-colors',
                  isActive
                    ? 'bg-brand-gold-400 text-brand-navy-950'
                    : 'text-white/72 hover:bg-white/8 hover:text-white',
                ].join(' ')
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <Link
          to="/login"
          className="rounded-full border border-brand-gold-400/60 px-4 py-2 text-sm font-medium text-brand-gold-400 transition-colors hover:bg-brand-gold-400 hover:text-brand-navy-950"
        >
          로그인
        </Link>
      </div>
    </header>
  )
}

export default Header
