import { useNavigate } from 'react-router-dom'

import { getAccessToken } from '../api/axiosInstance'
import { useAddFavorite, useDeleteFavorite, useFavorites } from '../hooks/useUser'
import type { FavoriteItem } from '../types/user'

interface FavoriteButtonProps {
  targetType: FavoriteItem['targetType']
  targetId: number
}

function FavoriteButton({ targetType, targetId }: FavoriteButtonProps) {
  const navigate = useNavigate()
  const favoritesQuery = useFavorites()
  const addMutation = useAddFavorite()
  const deleteMutation = useDeleteFavorite()
  const currentFavorite = favoritesQuery.data?.find((item) => item.targetType === targetType && item.targetId === targetId)

  const handleClick = () => {
    if (!getAccessToken()) {
      navigate('/login')
      return
    }
    if (currentFavorite) {
      deleteMutation.mutate(currentFavorite.id)
      return
    }
    addMutation.mutate({ targetType, targetId })
  }

  return (
    <button type="button" onClick={handleClick} className="rounded-full border border-brand-gold-400/60 px-3 py-1 text-sm text-brand-gold-400 transition hover:bg-brand-gold-400 hover:text-brand-navy-950">
      {currentFavorite ? '♥ 즐겨찾기' : '♡ 즐겨찾기'}
    </button>
  )
}

export default FavoriteButton
