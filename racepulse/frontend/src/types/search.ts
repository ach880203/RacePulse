export type SearchType = 'ALL' | 'HORSE' | 'JOCKEY' | 'TRAINER' | 'RACE'

export interface SearchItem {
  id: number
  name: string
  subText: string | null
  thumbnailUrl: string | null
}

export interface SearchResponse {
  query: string
  horses: SearchItem[]
  jockeys: SearchItem[]
  trainers: SearchItem[]
  races: SearchItem[]
}
