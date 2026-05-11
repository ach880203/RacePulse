// =============================================================================
// raceApi.ts — 경주 관련 API 호출 함수 모음
// =============================================================================
// 규칙 9: API 호출 코드는 반드시 src/api/ 폴더에 도메인별로 분리합니다.
// 컴포넌트 안에 직접 axios.get(...)을 쓰면 코드가 길어지고 재사용하기 어렵습니다.
//
// async/await란?
//   서버에 요청을 보내고 응답이 올 때까지 기다리는 비동기 코드를 쉽게 쓰는 문법입니다.
//   await = "이 응답이 올 때까지 여기서 잠깐 기다리세요"라는 뜻입니다.
// =============================================================================

// axiosInstance = 기본 URL과 인터셉터가 설정된 공통 HTTP 클라이언트입니다.
import axiosInstance from './axiosInstance'
// axios = ML 서버(8000번 포트) 직접 호출용으로 별도 인스턴스를 만들 때 사용합니다.
import axios from 'axios'
// 타입 정의 (TypeScript가 데이터 모양을 검증할 수 있게 해줍니다)
import type { ApiResponse, PageResponse, Race, RaceListParams } from '../types/race'
import type { RaceEntry, RaceResult } from '../types/entry'
import type { WeatherForecast } from '../types/weather'

// ML 서버(FastAPI, 포트 8000)에 직접 요청하는 별도 클라이언트입니다.
// Spring Boot(8080)와 FastAPI(8000)는 서버가 다르므로 baseURL을 분리합니다.
const mlAxios = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 10_000,
})

/**
 * 경주 목록을 페이지 단위로 조회합니다.
 * Spring Boot: GET /api/v1/races
 */
export async function fetchRaces(params: RaceListParams = {}): Promise<PageResponse<Race>> {
  // meetCode가 'ALL'이면 파라미터에서 제외합니다.
  const query = { ...params }
  if (query.meetCode === 'ALL') delete query.meetCode

  const response = await axiosInstance.get<ApiResponse<PageResponse<Race>>>('/races', {
    params: query,
  })
  // Spring Boot ApiResponse<T>의 data 필드를 꺼냅니다.
  return response.data.data
}

/**
 * 경주 1건 상세를 조회합니다.
 * Spring Boot: GET /api/v1/races/{raceId}
 */
export async function fetchRaceById(raceId: number): Promise<Race> {
  const response = await axiosInstance.get<ApiResponse<Race>>(`/races/${raceId}`)
  return response.data.data
}

/**
 * 오늘 예정된 경주(SCHEDULED) 목록을 조회합니다.
 * 홈 페이지의 "오늘의 경주" 섹션에서 사용합니다.
 */
export async function fetchUpcomingRaces(): Promise<Race[]> {
  const today = new Date().toISOString().slice(0, 10)
  const response = await axiosInstance.get<ApiResponse<PageResponse<Race>>>('/races', {
    params: {
      rcDate: today,
      status: 'SCHEDULED',
      size: 6,  // 홈 화면에는 최대 6개만 표시합니다.
    },
  })
  return response.data.data.content
}

/**
 * 특정 경주의 출전 명단을 조회합니다.
 * Spring Boot: GET /api/v1/races/{raceId}/entries
 */
export async function fetchRaceEntries(raceId: number): Promise<RaceEntry[]> {
  const response = await axiosInstance.get<ApiResponse<RaceEntry[]>>(
    `/races/${raceId}/entries`,
  )
  return response.data.data
}

/**
 * 특정 경주의 결과를 조회합니다.
 * Spring Boot: GET /api/v1/races/{raceId}/result
 */
export async function fetchRaceResult(raceId: number): Promise<RaceResult[]> {
  const response = await axiosInstance.get<ApiResponse<RaceResult[]>>(
    `/races/${raceId}/result`,
  )
  return response.data.data
}

/**
 * 특정 경마장·날짜의 날씨 예보를 ML 서버에서 조회합니다.
 * FastAPI ML 서버: GET /weather/{meetCode}/{date}
 */
export async function fetchWeather(
  meetCode: string,
  date: string,
): Promise<WeatherForecast | null> {
  try {
    const response = await mlAxios.get<{ success: boolean; data: WeatherForecast }>(
      `/weather/${meetCode}/${date}`,
    )
    return response.data.data
  } catch {
    // 날씨 데이터가 없어도 페이지는 정상 표시합니다.
    return null
  }
}
