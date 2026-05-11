import { getAccessToken, setAccessToken, clearAccessToken } from '../api/axiosInstance'

type Listener = () => void

let listeners: Listener[] = []

export function getAuthSnapshot() {
  return Boolean(getAccessToken())
}

export function subscribeAuth(listener: Listener) {
  listeners = [...listeners, listener]
  return () => {
    listeners = listeners.filter((item) => item !== listener)
  }
}

export function saveLoginToken(token: string) {
  setAccessToken(token)
  listeners.forEach((listener) => listener())
}

export function clearLoginToken() {
  clearAccessToken()
  listeners.forEach((listener) => listener())
}
