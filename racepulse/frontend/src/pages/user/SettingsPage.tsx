import { useEffect } from 'react'

import Layout from '../../components/layout/Layout'
import { useNotifications, usePreferences, useUpdateNotification, useUpdatePreferences } from '../../hooks/useUser'

function SettingsPage() {
  const notificationsQuery = useNotifications()
  const preferencesQuery = usePreferences()
  const updateNotification = useUpdateNotification()
  const updatePreferences = useUpdatePreferences()
  const theme = preferencesQuery.data?.theme ?? 'dark'

  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light')
  }, [theme])

  return (
    <Layout>
      <main className="mx-auto max-w-5xl px-4 py-10 sm:px-6 lg:px-8">
        <h1 className="font-heading text-4xl text-white">설정</h1>
        <section className="mt-6 rounded-lg border border-white/10 bg-white/[0.04] p-6">
          <h2 className="font-heading text-2xl text-brand-gold-400">알림 설정</h2>
          <div className="mt-4 space-y-3">
            {(notificationsQuery.data ?? []).map((setting) => (
              <label key={setting.type} className="flex items-center justify-between rounded-lg bg-white/6 p-4">
                <span className="font-semibold text-white">{setting.typeLabel}</span>
                <input
                  type="checkbox"
                  checked={setting.enabled}
                  onChange={(event) => updateNotification.mutate({ type: setting.type, enabled: event.target.checked })}
                  className="h-5 w-5 accent-[var(--color-brand-gold-400)]"
                />
              </label>
            ))}
          </div>
        </section>
        <section className="mt-5 rounded-lg border border-white/10 bg-white/[0.04] p-6">
          <h2 className="font-heading text-2xl text-brand-gold-400">화면 설정</h2>
          <button type="button" onClick={() => updatePreferences.mutate({ theme: theme === 'dark' ? 'light' : 'dark' })} className="mt-4 rounded-full bg-brand-gold-400 px-4 py-2 font-semibold text-brand-navy-950">
            {theme === 'dark' ? '라이트 모드로 전환' : '다크 모드로 전환'}
          </button>
        </section>
      </main>
    </Layout>
  )
}

export default SettingsPage
