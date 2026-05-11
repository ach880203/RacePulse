export interface CurrentUser {
  id: string
  email: string
  nickname: string
  role: string
  tier: string
  authProvider: string
}

export interface FavoriteItem {
  id: number
  targetType: 'HORSE' | 'JOCKEY' | 'RACE'
  targetId: number
  name: string
  subText: string | null
}

export interface UserPreference {
  theme: 'dark' | 'light'
  nickname: string | null
}

export interface NotificationSetting {
  type: string
  enabled: boolean
  typeLabel: string
}
