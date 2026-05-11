import { useSyncExternalStore } from 'react'
import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { getAuthSnapshot, subscribeAuth } from '../store/authStore'

function PrivateRoute() {
  const isLoggedIn = useSyncExternalStore(subscribeAuth, getAuthSnapshot)
  const location = useLocation()

  if (!isLoggedIn) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}

export default PrivateRoute
