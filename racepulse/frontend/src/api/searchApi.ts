import axiosInstance from './axiosInstance'
import type { ApiResponse } from '../types/race'
import type { SearchResponse, SearchType } from '../types/search'

export async function search(query: string, type: SearchType = 'ALL'): Promise<SearchResponse> {
  const response = await axiosInstance.get<ApiResponse<SearchResponse>>('/search', {
    params: { q: query, type },
  })
  return response.data.data
}
