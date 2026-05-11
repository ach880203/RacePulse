import axiosInstance, { clearAccessToken } from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { CurrentUser, FavoriteItem, NotificationSetting, UserPreference } from '../types/user'

export async function fetchMe(): Promise<CurrentUser> {
  const response = await axiosInstance.get<ApiResponse<CurrentUser>>('/auth/me')
  return response.data.data
}

export async function logout(): Promise<void> {
  await axiosInstance.post('/auth/logout')
  clearAccessToken()
}

export async function fetchFavorites(): Promise<FavoriteItem[]> {
  const response = await axiosInstance.get<ApiResponse<FavoriteItem[]>>('/user/favorites')
  return response.data.data
}

export async function addFavorite(targetType: FavoriteItem['targetType'], targetId: number): Promise<FavoriteItem> {
  const response = await axiosInstance.post<ApiResponse<FavoriteItem>>('/user/favorites', { targetType, targetId })
  return response.data.data
}

export async function deleteFavorite(id: number): Promise<void> {
  await axiosInstance.delete(`/user/favorites/${id}`)
}

export async function fetchPreferences(): Promise<UserPreference> {
  const response = await axiosInstance.get<ApiResponse<UserPreference>>('/user/preferences')
  return response.data.data
}

export async function updatePreferences(payload: Partial<UserPreference>): Promise<UserPreference> {
  const response = await axiosInstance.patch<ApiResponse<UserPreference>>('/user/preferences', payload)
  return response.data.data
}

export async function fetchNotifications(): Promise<NotificationSetting[]> {
  const response = await axiosInstance.get<ApiResponse<NotificationSetting[]>>('/user/notifications')
  return response.data.data
}

export async function updateNotification(type: string, enabled: boolean): Promise<NotificationSetting> {
  const response = await axiosInstance.patch<ApiResponse<NotificationSetting>>(`/user/notifications/${type}`, null, {
    params: { enabled },
  })
  return response.data.data
}
