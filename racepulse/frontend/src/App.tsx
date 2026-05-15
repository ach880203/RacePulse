// =============================================================================
// App.tsx — 앱의 라우팅(페이지 연결) 설정
// =============================================================================
// 라우팅이란? URL 주소에 따라 어떤 페이지를 보여줄지 결정하는 것
// 예: /races → 경주 목록 페이지, /horses → 경주마 목록 페이지
//
// BrowserRouter = 주소창 URL을 기반으로 페이지를 전환해주는 컴포넌트
// Routes = 여러 Route 중 현재 URL에 맞는 것 하나를 선택
// Route = "이 URL이면 이 페이지를 보여줘" 라는 규칙 하나
// =============================================================================

import { useState } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'

import IntroVideo, { INTRO_WATCHED_STORAGE_KEY } from './components/IntroVideo'
import HomePage from './pages/HomePage'
import RaceListPage from './pages/RaceListPage'

// 11번 프롬프트에서 구현한 상세 페이지들
import RaceDetailPage    from './pages/race/RaceDetailPage'
import RaceEntriesPage   from './pages/race/RaceEntriesPage'
import RacePredictionPage from './pages/race/RacePredictionPage'
import HorseDetailPage   from './pages/horse/HorseDetailPage'
import JockeyDetailPage  from './pages/jockey/JockeyDetailPage'
import TrainerDetailPage from './pages/trainer/TrainerDetailPage'

// 14번 프롬프트에서 구현한 대시보드 페이지들
import DashboardPage       from './pages/DashboardPage'
import WeeklyDashboardPage from './pages/WeeklyDashboardPage'
import PrivateRoute from './components/PrivateRoute'
import ComponentDemoPage from './pages/ComponentDemoPage'
import SearchPage from './pages/SearchPage'
import ProfilePage from './pages/user/ProfilePage'
import FavoritesPage from './pages/user/FavoritesPage'
import SettingsPage from './pages/user/SettingsPage'
import UnauthorizedPage from './pages/error/UnauthorizedPage'
import ServerErrorPage from './pages/error/ServerErrorPage'
import NotFoundPage from './pages/error/NotFoundPage'

// -----------------------------------------------------------------------------
// 아직 구현 전인 페이지의 임시 컴포넌트
// -----------------------------------------------------------------------------
const Placeholder = ({ name }: { name: string }) => (
  <div className="min-h-screen bg-brand-navy-950 px-8 py-12 font-body text-white">
    <h1 className="font-heading text-4xl text-brand-gold-400">레이스펄스</h1>
    <p className="mt-4 text-white/60">[ {name} ] 페이지 준비 중...</p>
  </div>
)

function readIntroWatchStatus() {
  try {
    return localStorage.getItem(INTRO_WATCHED_STORAGE_KEY) === 'true'
  } catch (error) {
    console.error('인트로 시청 상태를 읽는 중 오류가 발생했습니다.', error)
    return false
  }
}

function HomeRoute() {
  const [hasWatchedIntro, setHasWatchedIntro] = useState<boolean>(
    () => readIntroWatchStatus(),
  )

  if (!hasWatchedIntro) {
    return <IntroVideo onComplete={() => setHasWatchedIntro(true)} />
  }

  return <HomePage />
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* ----------------------------------------------------------------
            공개 페이지 (로그인 없이 접근 가능)
            ---------------------------------------------------------------- */}
        <Route path="/" element={<HomeRoute />} />

        {/* 경주 관련 — 11번에서 실제 페이지로 교체 */}
        <Route path="/races"                          element={<RaceListPage />} />
        <Route path="/races/:raceId"                  element={<RaceDetailPage />} />
        <Route path="/races/:raceId/entries"          element={<RaceEntriesPage />} />
        <Route path="/races/:raceId/result"           element={<Placeholder name="경주 결과" />} />
        <Route path="/races/:raceId/prediction"       element={<RacePredictionPage />} />
        <Route path="/races/:raceId/commentary"       element={<Placeholder name="AI 해설" />} />

        {/* 경주마 관련 — 11번에서 실제 페이지로 교체 */}
        <Route path="/horses"                         element={<Placeholder name="경주마 목록" />} />
        <Route path="/horses/:horseId"                element={<HorseDetailPage />} />
        <Route path="/horses/:horseId/history"        element={<Placeholder name="경주마 성적 이력" />} />

        {/* 기수 / 조교사 — 11번에서 실제 페이지로 교체 */}
        <Route path="/jockeys/:jockeyId"              element={<JockeyDetailPage />} />
        <Route path="/trainers/:trainerId"            element={<TrainerDetailPage />} />

        {/* 경마장 */}
        <Route path="/racecourses"                    element={<Placeholder name="경마장 목록" />} />
        <Route path="/racecourses/:meetCode"          element={<Placeholder name="경마장 상세" />} />

        {/* 대시보드 — 14번 프롬프트에서 실제 페이지로 교체 */}
        <Route path="/dashboard"                      element={<DashboardPage />} />
        <Route path="/dashboard/weekly"               element={<WeeklyDashboardPage />} />
        <Route path="/search"                         element={<SearchPage />} />
        <Route path="/demo"                           element={<ComponentDemoPage />} />

        {/* ----------------------------------------------------------------
            인증 페이지 — TODO: [Phase 2] 카카오 로그인 연동
            ---------------------------------------------------------------- */}
        <Route path="/login"                          element={<Placeholder name="로그인" />} />
        <Route path="/register"                       element={<Placeholder name="회원가입" />} />
        <Route path="/auth/kakao/callback"            element={<Placeholder name="카카오 OAuth 콜백" />} />

        {/* 로그인 필요 페이지 */}
        <Route element={<PrivateRoute />}>
          <Route path="/profile"                      element={<ProfilePage />} />
          <Route path="/favorites"                    element={<FavoritesPage />} />
          <Route path="/settings"                     element={<SettingsPage />} />
        </Route>

        {/* 관리자 페이지 */}
        <Route path="/admin"                          element={<Placeholder name="관리자 대시보드" />} />
        <Route path="/admin/collection"               element={<Placeholder name="수집 현황" />} />
        {/* 에러 페이지 */}
        <Route path="/unauthorized"                   element={<UnauthorizedPage/>} />
        <Route path="/forbidden"                      element={<UnauthorizedPage variant="forbidden" />} />
        <Route path="/error"                          element={<ServerErrorPage />} />
        {/* 존재하지 않는 모든 URL을 404로 */}
        <Route path="*"                               element={<NotFoundPage />} />                
      </Routes>
    </BrowserRouter>
  )
}

export default App
