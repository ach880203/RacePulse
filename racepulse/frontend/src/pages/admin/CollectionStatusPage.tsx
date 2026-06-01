import { AxiosError } from 'axios'
import { useCallback, useEffect, useRef, useState } from 'react'

import axiosInstance from '../../api/axiosInstance'
import Toast, { type ToastType } from '../../components/Toast'
import type { ApiResponse } from '../../types/race'

type CollectionStatus = 'SUCCESS' | 'FAILED' | 'RUNNING' | 'UNKNOWN' | 'PARTIAL' | 'SKIPPED'

type CollectionStatusResponse = {
  lastEntriesCollection: string | null
  lastResultsCollection: string | null
  lastEntriesStatus: CollectionStatus
  lastResultsStatus: CollectionStatus
}

type TriggerResponse = {
  triggeredAt: string
  type: 'ENTRIES' | 'RESULTS'
}

type TriggerType = 'entries' | 'results' | 'all' | null

function getApiErrorMessage(error: unknown, fallbackMessage: string): string {
  // 서버가 409 중복 실행 같은 이유를 알려주면 Toast에 그대로 보여 운영자가 원인을 바로 알 수 있게 합니다.
  if (error instanceof AxiosError) {
    const responseData = error.response?.data as Partial<ApiResponse<unknown>> | undefined
    return responseData?.message ?? fallbackMessage
  }

  return fallbackMessage
}

function formatDateTime(value: string | null): string {
  if (!value) return '기록 없음'

  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value

  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

function getStatusLabel(status: CollectionStatus): string {
  const labels: Record<CollectionStatus, string> = {
    SUCCESS: '성공',
    FAILED: '실패',
    RUNNING: '실행 중',
    UNKNOWN: '확인 전',
    PARTIAL: '부분 성공',
    SKIPPED: '건너뜀',
  }

  return labels[status] ?? '확인 전'
}

function getStatusClassName(status: CollectionStatus): string {
  if (status === 'SUCCESS') return 'bg-emerald-500/15 text-emerald-300 ring-emerald-400/30'
  if (status === 'RUNNING') return 'bg-brand-gold-400/15 text-brand-gold-400 ring-brand-gold-400/30'
  if (status === 'FAILED') return 'bg-red-500/15 text-red-300 ring-red-400/30'
  return 'bg-white/10 text-white/70 ring-white/15'
}

function StatusBadge({ status }: { status: CollectionStatus }) {
  return (
    <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ring-1 ${getStatusClassName(status)}`}>
      {getStatusLabel(status)}
    </span>
  )
}

function CollectionStatusPage() {
  const [status, setStatus] = useState<CollectionStatusResponse | null>(null)
  const [isLoadingStatus, setIsLoadingStatus] = useState(true)
  const [activeTrigger, setActiveTrigger] = useState<TriggerType>(null)
  const [toast, setToast] = useState<{ message: string; type: ToastType } | null>(null)
  const pollingTimerRef = useRef<number | null>(null)

  const fetchStatus = useCallback(async () => {
    // 관리자 화면은 최신 수집 로그가 핵심이므로 진입과 수동 실행 후 같은 함수로 상태를 다시 읽습니다.
    const response = await axiosInstance.get<ApiResponse<CollectionStatusResponse>>('/admin/collection/trigger/status')
    setStatus(response.data.data)
  }, [])

  const startPolling = useCallback(() => {
    // 수집 시작 직후에는 완료 시각이 늦게 반영되므로 10초 간격으로 최대 5회만 자동 갱신합니다.
    let count = 0

    if (pollingTimerRef.current !== null) {
      window.clearInterval(pollingTimerRef.current)
    }

    pollingTimerRef.current = window.setInterval(() => {
      count += 1
      void fetchStatus()

      if (count >= 5 && pollingTimerRef.current !== null) {
        window.clearInterval(pollingTimerRef.current)
        pollingTimerRef.current = null
      }
    }, 10_000)
  }, [fetchStatus])

  useEffect(() => {
    const loadInitialStatus = async () => {
      try {
        await fetchStatus()
      } catch (error) {
        setToast({ message: getApiErrorMessage(error, '수집 상태를 불러오지 못했습니다.'), type: 'error' })
      } finally {
        setIsLoadingStatus(false)
      }
    }

    void loadInitialStatus()

    return () => {
      if (pollingTimerRef.current !== null) {
        window.clearInterval(pollingTimerRef.current)
      }
    }
  }, [fetchStatus])

  const triggerCollection = async (type: Exclude<TriggerType, 'all' | null>) => {
    // 버튼별 수동 수집 API를 호출하고 성공하면 상태 폴링을 시작합니다.
    await axiosInstance.post<ApiResponse<TriggerResponse>>(`/admin/collection/trigger/${type}`)
  }

  const handleTrigger = async (type: Exclude<TriggerType, null>) => {
    setActiveTrigger(type)

    try {
      if (type === 'all') {
        // 전체 수집은 출전표가 먼저 준비되어야 결과 수집이 더 안정적이므로 순차 실행합니다.
        await triggerCollection('entries')
        await triggerCollection('results')
      } else {
        await triggerCollection(type)
      }

      setToast({ message: '수집이 시작되었습니다', type: 'success' })
      await fetchStatus()
      startPolling()
    } catch (error) {
      setToast({
        message: getApiErrorMessage(error, '수집 시작에 실패했습니다. 다시 시도해주세요.'),
        type: 'error',
      })
    } finally {
      setActiveTrigger(null)
    }
  }

  const isRunning = activeTrigger !== null

  return (
    <main className="min-h-screen bg-brand-navy-950 px-4 py-10 font-body text-white sm:px-6 lg:px-8">
      {toast && (
        <div className="fixed right-4 top-4 z-50">
          <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />
        </div>
      )}

      <section className="mx-auto max-w-5xl">
        <div className="rounded-[2rem] border border-white/10 bg-brand-navy-900/60 p-6 shadow-2xl shadow-black/30 lg:p-8">
          <div className="border-b border-white/10 pb-6">
            <p className="text-sm font-semibold text-brand-gold-400">관리자</p>
            <h1 className="mt-2 font-heading text-3xl text-white">데이터 수집 현황</h1>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <section className="rounded-2xl border border-white/10 bg-brand-navy-950/70 p-5">
              <h2 className="text-lg font-semibold text-white">자동 수집 스케줄</h2>
              <div className="mt-5 space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white">03:00 대량 수집</p>
                    <p className="text-sm text-white/55">예약 작업</p>
                  </div>
                  <StatusBadge status="SUCCESS" />
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white">05:00 야간 파이프라인</p>
                    <p className="text-sm text-white/55">피처 계산과 모델 학습</p>
                  </div>
                  <StatusBadge status="SUCCESS" />
                </div>
              </div>
            </section>

            <section className="rounded-2xl border border-white/10 bg-brand-navy-950/70 p-5">
              <h2 className="text-lg font-semibold text-white">마지막 수집</h2>
              <div className="mt-5 space-y-4">
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white">출전표</p>
                    <p className="text-sm text-white/55">
                      {isLoadingStatus ? '불러오는 중' : formatDateTime(status?.lastEntriesCollection ?? null)}
                    </p>
                  </div>
                  <StatusBadge status={status?.lastEntriesStatus ?? 'UNKNOWN'} />
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white">경기 결과</p>
                    <p className="text-sm text-white/55">
                      {isLoadingStatus ? '불러오는 중' : formatDateTime(status?.lastResultsCollection ?? null)}
                    </p>
                  </div>
                  <StatusBadge status={status?.lastResultsStatus ?? 'UNKNOWN'} />
                </div>
              </div>
            </section>
          </div>

          <section className="mt-6 rounded-2xl border border-white/10 bg-brand-navy-950/70 p-5">
            <h2 className="text-lg font-semibold text-white">수동 수집</h2>
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <button
                type="button"
                disabled={isRunning}
                onClick={() => void handleTrigger('entries')}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-left transition hover:-translate-y-0.5 hover:border-brand-gold-400/60 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <span className="text-lg font-semibold text-brand-gold-400">출전표 수집</span>
                <span className="mt-2 block text-sm text-white/60">예정 경주 데이터</span>
                <span className="mt-4 block rounded-full bg-brand-gold-400 px-4 py-2 text-center text-sm font-semibold text-brand-navy-950">
                  {activeTrigger === 'entries' ? '시작 중...' : '수집 시작'}
                </span>
              </button>

              <button
                type="button"
                disabled={isRunning}
                onClick={() => void handleTrigger('results')}
                className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 text-left transition hover:-translate-y-0.5 hover:border-brand-gold-400/60 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
              >
                <span className="text-lg font-semibold text-brand-gold-400">결과 수집</span>
                <span className="mt-2 block text-sm text-white/60">완료 경기 데이터</span>
                <span className="mt-4 block rounded-full bg-brand-gold-400 px-4 py-2 text-center text-sm font-semibold text-brand-navy-950">
                  {activeTrigger === 'results' ? '시작 중...' : '수집 시작'}
                </span>
              </button>
            </div>

            <button
              type="button"
              disabled={isRunning}
              onClick={() => void handleTrigger('all')}
              className="mt-4 w-full rounded-2xl bg-brand-gold-400 px-6 py-4 text-sm font-semibold text-brand-navy-950 transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:translate-y-0"
            >
              {activeTrigger === 'all' ? '전체 수집 시작 중...' : '전체 수집 시작'}
              <span className="mt-1 block text-xs font-medium text-brand-navy-950/70">출전표와 결과를 순서대로 실행합니다</span>
            </button>

            <p className="mt-5 text-sm text-white/55">주의: 수집 중에는 버튼이 비활성화됩니다.</p>
          </section>
        </div>
      </section>
    </main>
  )
}

export default CollectionStatusPage
