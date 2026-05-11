import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { addFavorite, deleteFavorite, fetchFavorites, fetchMe, fetchNotifications, fetchPreferences, logout, updateNotification, updatePreferences } from '../api/userApi'
import { clearLoginToken } from '../store/authStore'
import type { FavoriteItem, UserPreference } from '../types/user'

export function useMe() {
  return useQuery({ queryKey: ['me'], queryFn: fetchMe, retry: false })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: logout,
    onSettled: () => {
      clearLoginToken()
      queryClient.clear()
    },
  })
}

export function useFavorites() {
  return useQuery({ queryKey: ['favorites'], queryFn: fetchFavorites })
}

export function useAddFavorite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ targetType, targetId }: { targetType: FavoriteItem['targetType']; targetId: number }) => addFavorite(targetType, targetId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['favorites'] }),
  })
}

export function useDeleteFavorite() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: deleteFavorite,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['favorites'] }),
  })
}

export function usePreferences() {
  return useQuery({ queryKey: ['preferences'], queryFn: fetchPreferences })
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: Partial<UserPreference>) => updatePreferences(payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['preferences'] }),
  })
}

export function useNotifications() {
  return useQuery({ queryKey: ['notifications'], queryFn: fetchNotifications })
}

export function useUpdateNotification() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ type, enabled }: { type: string; enabled: boolean }) => updateNotification(type, enabled),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  })
}
