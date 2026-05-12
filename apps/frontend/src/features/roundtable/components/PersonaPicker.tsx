import type { RoundtablePersona } from '@/features/roundtable/types'

export function PersonaPicker({ personas, selectedIds, onToggle, onSelectAll, onClear }: {
  personas: RoundtablePersona[]
  selectedIds: string[]
  onToggle: (id: string) => void
  onSelectAll: () => void
  onClear: () => void
}) {
  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold">人物选择</h2>
          <p className="text-sm text-gray-500">不选择时系统自动推荐 3-5 位；手动选择会优先保留。</p>
        </div>
        <div className="flex gap-2 text-sm">
          <button type="button" onClick={onSelectAll} className="rounded-lg border px-3 py-1">全选</button>
          <button type="button" onClick={onClear} className="rounded-lg border px-3 py-1">自动推荐</button>
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {personas.map((persona) => {
          const checked = selectedIds.includes(persona.id)
          return (
            <button
              key={persona.id}
              type="button"
              onClick={() => onToggle(persona.id)}
              className={`rounded-xl border p-4 text-left transition ${checked ? 'border-gray-900 bg-gray-900 text-white' : 'bg-white hover:bg-gray-50'}`}
            >
              <div className="font-medium">{persona.displayName}</div>
              <div className={`mt-1 text-sm ${checked ? 'text-gray-200' : 'text-gray-500'}`}>{persona.summary}</div>
              {persona.selectionReason && <div className={`mt-2 text-xs ${checked ? 'text-gray-300' : 'text-gray-400'}`}>{persona.selectionReason}</div>}
            </button>
          )
        })}
      </div>
    </section>
  )
}
