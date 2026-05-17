import { FileText, Map, Target } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { DecisionArtifact } from '@/features/roundtable/types'

interface DecisionArtifactsProps {
  artifact?: DecisionArtifact
}

export function DecisionArtifacts({ artifact }: DecisionArtifactsProps) {
  const { t } = useTranslation()
  if (!artifact) {
    return (
      <section className="rounded-lg border border-dashed border-zinc-300 bg-white p-6 text-center text-sm text-zinc-500">
        {t('roundtable.artifact.empty')}
      </section>
    )
  }

  return (
    <section className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-4">
        <h2 className="mt-1 text-lg font-semibold text-zinc-950">{t('roundtable.artifact.title')}</h2>
      </div>
      <div className="grid min-w-0 gap-4 lg:grid-cols-3">
        <div className="min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h3 className="inline-flex items-center gap-2 font-semibold text-zinc-950">
            <FileText className="size-4 text-emerald-700" />
            {t('roundtable.artifact.memo')}
          </h3>
          <p className="mt-2 break-words text-sm leading-6 text-zinc-700">{artifact.memo}</p>
        </div>
        <div className="min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h3 className="inline-flex items-center gap-2 font-semibold text-zinc-950">
            <Target className="size-4 text-emerald-700" />
            {t('roundtable.artifact.recommendation')}
          </h3>
          <p className="mt-2 break-words text-sm leading-6 text-zinc-700">{artifact.recommendation}</p>
        </div>
        <div className="min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
          <h3 className="font-semibold text-zinc-950">{t('roundtable.artifact.reasons')}</h3>
          <ul className="mt-2 space-y-2 text-sm text-zinc-700">
            {artifact.reasons.map((reason) => (
              <li className="flex gap-2" key={reason}>
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-emerald-600" />
                <span className="min-w-0 break-words">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mt-4 min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4">
        <h3 className="inline-flex items-center gap-2 font-semibold text-zinc-950">
          <Map className="size-4 text-emerald-700" />
          {t('roundtable.artifact.debateMap')}
        </h3>
        <div className="mt-3 grid min-w-0 gap-3 md:grid-cols-2">
          {artifact.debateMap.map((item) => (
            <div className="min-w-0 rounded-lg border border-zinc-200 bg-white p-3 text-sm" key={`${item.personaName}-${item.position}`}>
              <p className="break-words font-medium text-zinc-950">{item.personaName}</p>
              <p className="mt-1 break-words leading-6 text-zinc-700">{item.position}</p>
              <p className="mt-1 break-words text-xs leading-5 text-zinc-500">{item.keyConcern}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
