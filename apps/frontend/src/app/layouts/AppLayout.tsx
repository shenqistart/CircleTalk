import { MessageSquare, PanelLeftClose, PanelLeftOpen, Users } from 'lucide-react'
import { type ComponentType, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { NavLink, Outlet } from 'react-router-dom'
import { type AppLanguage, useAppLanguage } from '@/app/i18n'

const languageOptions: Array<{ label: string; value: AppLanguage }> = [
  { label: '中文', value: 'zh' },
  { label: 'English', value: 'en' },
]

export function AppLayout() {
  const { t } = useTranslation()
  const { language, setLanguage } = useAppLanguage()
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  const navItems: Array<{ icon: ComponentType<{ className?: string }>; label: string; to: string }> = [
    { icon: MessageSquare, label: t('app.nav.roundtable'), to: '/roundtable' },
    { icon: Users, label: t('app.nav.users'), to: '/users' },
  ]
  const sidebarToggleLabel = isSidebarCollapsed ? t('app.sidebar.expand') : t('app.sidebar.collapse')

  return (
    <div className="flex h-screen w-full overflow-hidden bg-zinc-50 text-zinc-950">
      <aside
        className={`hidden shrink-0 flex-col border-r border-zinc-200 bg-white py-5 transition-[width] duration-200 md:flex ${
          isSidebarCollapsed ? 'w-20 px-3' : 'w-64 px-4'
        }`}
      >
        <div className={`mb-6 flex items-start gap-3 px-2 ${isSidebarCollapsed ? 'justify-center' : 'justify-between'}`}>
          {isSidebarCollapsed ? null : (
            <div>
              <h1 className="text-xl font-semibold tracking-tight">{t('app.subtitle')}</h1>
            </div>
          )}
          <button
            aria-label={sidebarToggleLabel}
            aria-expanded={!isSidebarCollapsed}
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg border border-zinc-200 text-zinc-600 transition hover:bg-zinc-100 hover:text-zinc-950"
            title={sidebarToggleLabel}
            type="button"
            onClick={() => setIsSidebarCollapsed((current) => !current)}
          >
            {isSidebarCollapsed ? <PanelLeftOpen className="size-4" /> : <PanelLeftClose className="size-4" />}
          </button>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                aria-label={item.label}
                className={({ isActive }) =>
                  `flex items-center rounded-lg px-3 py-2 text-sm font-medium transition ${
                    isSidebarCollapsed ? 'justify-center' : 'gap-3'
                  } ${
                    isActive ? 'bg-zinc-950 text-white shadow-sm' : 'text-zinc-600 hover:bg-zinc-100 hover:text-zinc-950'
                  }`
                }
                key={item.to}
                title={isSidebarCollapsed ? item.label : undefined}
                to={item.to}
              >
                <Icon className="size-4 shrink-0" />
                {isSidebarCollapsed ? null : <span>{item.label}</span>}
              </NavLink>
            )
          })}
        </nav>
      </aside>
      <main className="flex min-w-0 flex-1 flex-col overflow-hidden">
        <header className="flex min-w-0 items-center justify-between border-b border-zinc-200 bg-white px-4 py-3">
          <div className="md:hidden">
            <h1 className="text-base font-semibold tracking-tight">Bedrock</h1>
            <p className="text-xs text-zinc-500">{t('app.subtitle')}</p>
          </div>
          <div className="ml-auto">
            <label className="sr-only" htmlFor="app-language">
              {t('app.language')}
            </label>
            <select
              aria-label={t('app.language')}
              className="rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-700 outline-none transition focus:border-zinc-950 focus:ring-2 focus:ring-zinc-100"
              id="app-language"
              value={language}
              onChange={(event) => setLanguage(event.target.value as AppLanguage)}
            >
              {languageOptions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </div>
        </header>
        <div className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
