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
  const recommendedIds = new Set(recommendedPersonas.map((persona) => persona.id))
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-blue-700">Step 2 · 人物选择</p>
          <h2 className="text-xl font-bold text-slate-950">可手选 1 个到全部；不选则后端自动推荐</h2>
        </div>
        <div className="flex gap-2">
          <button className="rounded-lg border px-3 py-1.5 text-xs" type="button" onClick={() => onSelectAll()}>
            全选
          </button>
          <button className="rounded-lg border px-3 py-1.5 text-xs" type="button" onClick={() => onClear()}>
            清空
          </button>
        </div>
      </div>
      {isLoading ? <p className="text-sm text-slate-500">人物加载中...</p> : null}
      <div className="grid gap-3 md:grid-cols-2">
        {personas.map((persona) => {
          const checked = selectedPersonaIds.includes(persona.id)
          return (
            <label
              className={`cursor-pointer rounded-xl border p-4 transition ${checked ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'}`}
              key={persona.id}
            >
              <input checked={checked} className="sr-only" type="checkbox" onChange={() => onToggle(persona.id)} />
              <div className="flex items-center justify-between gap-3">
                <h3 className="font-semibold text-slate-950">{persona.displayName}</h3>
                {recommendedIds.has(persona.id) ? <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800">推荐</span> : null}
              </div>
              <p className="mt-2 text-sm text-slate-600">{persona.summary}</p>
              {persona.selectionReason ? <p className="mt-2 text-xs text-blue-700">{persona.selectionReason}</p> : null}
            </label>
          )
        })}
      </div>
    </section>
  )
}
