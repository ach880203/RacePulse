import { Link } from 'react-router-dom'

import Layout from '../../components/layout/Layout'
import { useDeleteFavorite, useFavorites } from '../../hooks/useUser'

const targetPathMap = {
  HORSE: '/horses',
  JOCKEY: '/jockeys',
  RACE: '/races',
}

function FavoritesPage() {
  const favoritesQuery = useFavorites()
  const deleteMutation = useDeleteFavorite()
  const favorites = favoritesQuery.data ?? []

  return (
    <Layout>
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl text-white">즐겨찾기</h1>
        {favorites.length === 0 ? (
          <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.04] p-8 text-center text-white/65">즐겨찾기한 항목이 없습니다</div>
        ) : (
          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            {favorites.map((item) => (
              <div key={item.id} className="rounded-lg border border-white/10 bg-white/[0.04] p-4">
                <Link to={`${targetPathMap[item.targetType]}/${item.targetId}`} className="font-semibold text-white hover:text-brand-gold-400">{item.name}</Link>
                <p className="mt-1 text-sm text-white/55">{item.subText}</p>
                <button type="button" onClick={() => deleteMutation.mutate(item.id)} className="mt-4 text-sm font-semibold text-brand-gold-400">♥ 해제</button>
              </div>
            ))}
          </div>
        )}
      </main>
    </Layout>
  )
}

export default FavoritesPage
