import { Database } from 'lucide-react'
import { useTranslation } from 'react-i18next'

export function DeploymentStatusBanner() {
  const { t } = useTranslation()
  return (
    <div className="grid min-w-0 gap-3 md:grid-cols-2">
      <div className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-700">
        <div className="flex min-w-0 items-start gap-3">
          <Database className="mt-0.5 size-4 shrink-0 text-zinc-500" />
          <div className="min-w-0">
            <p className="font-semibold text-zinc-950">{t('roundtable.status.persistence')}</p>
            <p className="mt-1 break-words">{t('roundtable.status.persistenceDescription')}</p>
          </div>
        </div>
      </div>
    </div>
  )
}
