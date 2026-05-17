import { Check, Eraser, Loader2, Users } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { RoundtablePersona } from '@/features/roundtable/types'

interface PersonaPickerProps {
  isLoading: boolean
  personas: RoundtablePersona[]
  recommendedPersonas: RoundtablePersona[]
  selectedPersonaIds: string[]
  onClear: () => void
  onSelectAll: () => void
  onToggle: (personaId: string) => void
}

export function PersonaPicker({
  isLoading,
  onClear,
  onSelectAll,
  onToggle,
  personas,
  recommendedPersonas,
  selectedPersonaIds,
}: PersonaPickerProps) {
  const { t } = useTranslation()
  const recommendedIds = new Set(recommendedPersonas.map((persona) => persona.id))
  const selectedCount = selectedPersonaIds.length
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="mt-1 text-lg font-semibold text-zinc-950">{t('roundtable.picker.title')}</h2>
          <p className="mt-1 text-xs text-zinc-500">{t('roundtable.picker.selectedCount', { count: selectedCount })}</p>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50"
            type="button"
            onClick={() => onSelectAll()}
          >
            <Users className="size-3.5" />
            {t('roundtable.picker.selectAll')}
          </button>
          <button
            className="inline-flex items-center gap-1.5 rounded-lg border border-zinc-300 px-3 py-1.5 text-xs font-medium text-zinc-700 transition hover:bg-zinc-50"
            type="button"
            onClick={() => onClear()}
          >
            <Eraser className="size-3.5" />
            {t('roundtable.picker.clear')}
          </button>
        </div>
      </div>
      {isLoading ? (
        <div className="flex items-center gap-2 rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-4 text-sm text-zinc-500">
          <Loader2 className="size-4 animate-spin" />
          {t('roundtable.picker.loading')}
        </div>
      ) : null}
      <div className="grid min-w-0 gap-3 md:grid-cols-2">
        {personas.map((persona) => {
          const checked = selectedPersonaIds.includes(persona.id)
          return (
            <label
              className={`min-w-0 cursor-pointer rounded-lg border p-4 transition ${
                checked ? 'border-emerald-600 bg-emerald-50 shadow-sm' : 'border-zinc-200 bg-white hover:border-zinc-300 hover:bg-zinc-50'
              }`}
              key={persona.id}
            >
              <input checked={checked} className="sr-only" type="checkbox" onChange={() => onToggle(persona.id)} />
              <div className="flex items-center justify-between gap-3">
                <h3 className="min-w-0 break-words font-semibold text-zinc-950">{persona.displayName}</h3>
                <div className="flex shrink-0 items-center gap-2">
                  {recommendedIds.has(persona.id) ? <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800">{t('roundtable.picker.recommended')}</span> : null}
                  {checked ? (
                    <span className="inline-flex size-6 items-center justify-center rounded-full bg-emerald-600 text-white">
                      <Check className="size-3.5" />
                    </span>
                  ) : null}
                </div>
              </div>
              <p className="mt-2 break-words text-sm leading-6 text-zinc-600">{persona.summary}</p>
              {persona.selectionReason ? <p className="mt-2 break-words text-xs leading-5 text-emerald-700">{persona.selectionReason}</p> : null}
            </label>
          )
        })}
      </div>
    </section>
  )
}
