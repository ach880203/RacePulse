import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'

import { search } from '../api/searchApi'
import Layout from '../components/layout/Layout'
import { useDebounce } from '../hooks/useDebounce'
import type { SearchItem, SearchType } from '../types/search'

const RECENT_SEARCH_KEY = 'racepulse_recent_searches'

const filterItems: { type: SearchType; label: string }[] = [
  { type: 'ALL', label: '전체' },
  { type: 'HORSE', label: '경주마' },
  { type: 'JOCKEY', label: '기수' },
  { type: 'TRAINER', label: '조교사' },
  { type: 'RACE', label: '경주' },
]

function readRecentSearches() {
  try {
    return JSON.parse(localStorage.getItem(RECENT_SEARCH_KEY) ?? '[]') as string[]
  } catch {
    return []
  }
}

function SearchPage() {
  const [query, setQuery] = useState('')
  const [type, setType] = useState<SearchType>('ALL')
  const [recentSearches, setRecentSearches] = useState<string[]>(() => readRecentSearches())
  const debouncedQuery = useDebounce(query.trim(), 300)

  const searchQuery = useQuery({
    queryKey: ['search', debouncedQuery, type],
    queryFn: () => search(debouncedQuery, type),
    enabled: debouncedQuery.length > 0,
    staleTime: 60 * 1000,
  })

  useEffect(() => {
    if (!debouncedQuery || searchQuery.isFetching) return
    const timer = window.setTimeout(() => {
      setRecentSearches((currentSearches) => {
        const nextSearches = [debouncedQuery, ...currentSearches.filter((item) => item !== debouncedQuery)].slice(0, 10)
        localStorage.setItem(RECENT_SEARCH_KEY, JSON.stringify(nextSearches))
        return nextSearches
      })
    }, 0)
    return () => window.clearTimeout(timer)
  }, [debouncedQuery, searchQuery.isFetching])

  const data = searchQuery.data
  const hasResult = Boolean(data && (data.horses.length || data.jockeys.length || data.trainers.length || data.races.length))

  return (
    <Layout>
      <main className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl text-white">통합 검색</h1>
        <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.04] p-4">
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="경주마, 기수, 조교사, 경주 검색"
            className="w-full rounded-lg border border-white/10 bg-brand-navy-900 px-4 py-3 text-white outline-none transition focus:border-brand-gold-400"
          />
          <div className="mt-4 flex flex-wrap gap-2">
            {filterItems.map((item) => (
              <button
                key={item.type}
                type="button"
                onClick={() => setType(item.type)}
                className={`rounded-full px-4 py-2 text-sm transition ${type === item.type ? 'bg-brand-gold-400 text-brand-navy-950' : 'bg-white/8 text-white/75 hover:bg-white/12'}`}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>

        {recentSearches.length > 0 && (
          <div className="mt-5 flex flex-wrap gap-2">
            {recentSearches.map((item) => (
              <button key={item} type="button" onClick={() => setQuery(item)} className="rounded-full bg-white/8 px-3 py-1 text-sm text-white/70">
                {item}
              </button>
            ))}
          </div>
        )}

        <div className="mt-8">
          {searchQuery.isFetching && <SearchSkeleton />}
          {!searchQuery.isFetching && debouncedQuery && !hasResult && (
            <div className="rounded-lg border border-white/10 bg-white/[0.04] p-8 text-center text-white/65">검색 결과가 없습니다</div>
          )}
          {data && hasResult && (
            <div className="space-y-8">
              <ResultSection title="경주마" items={data.horses} pathPrefix="/horses" />
              <ResultSection title="기수" items={data.jockeys} pathPrefix="/jockeys" />
              <ResultSection title="조교사" items={data.trainers} pathPrefix="/trainers" />
              <ResultSection title="경주" items={data.races} pathPrefix="/races" />
            </div>
          )}
        </div>
      </main>
    </Layout>
  )
}

function ResultSection({ title, items, pathPrefix }: { title: string; items: SearchItem[]; pathPrefix: string }) {
  if (items.length === 0) return null
  return (
    <section>
      <h2 className="mb-3 font-heading text-2xl text-brand-gold-400">{title}</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        {items.map((item) => (
          <Link key={`${pathPrefix}-${item.id}`} to={`${pathPrefix}/${item.id}`} className="rounded-lg border border-white/10 bg-white/[0.04] p-4 transition hover:border-brand-gold-400/60">
            <p className="font-semibold text-white">{item.name}</p>
            {item.subText && <p className="mt-1 text-sm text-white/55">{item.subText}</p>}
          </Link>
        ))}
      </div>
    </section>
  )
}

function SearchSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, index) => (
        <div key={index} className="h-20 animate-pulse rounded-lg bg-white/8" />
      ))}
    </div>
  )
}

export default SearchPage
