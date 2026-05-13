import { Sparkles, Users } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'

interface DecisionPromptFormProps {
  isBusy: boolean
  onCreate: (decisionPrompt: string) => Promise<void>
  onRecommend: (decisionPrompt: string) => Promise<void>
}

export function DecisionPromptForm({ isBusy, onCreate, onRecommend }: DecisionPromptFormProps) {
  const { t } = useTranslation()
  const [decisionPrompt, setDecisionPrompt] = useState('')
  const trimmedPrompt = decisionPrompt.trim()
  const canSubmit = trimmedPrompt.length > 0 && !isBusy

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canSubmit) return
    void onCreate(trimmedPrompt)
  }

  return (
    <form className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm" onSubmit={handleSubmit}>
      <div className="mb-4 flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase text-emerald-700">{t('roundtable.form.step')}</p>
          <h2 className="mt-1 text-lg font-semibold text-zinc-950">{t('roundtable.form.title')}</h2>
        </div>
        <span className="shrink-0 rounded-full bg-zinc-100 px-2.5 py-1 text-xs font-medium text-zinc-600">{trimmedPrompt.length}/4000</span>
      </div>
      <textarea
        className="min-h-36 w-full resize-y rounded-lg border border-zinc-300 bg-zinc-50 p-3 text-sm leading-6 text-zinc-900 outline-none transition placeholder:text-zinc-400 focus:border-emerald-600 focus:bg-white focus:ring-2 focus:ring-emerald-100"
        maxLength={4000}
        placeholder={t('roundtable.form.promptPlaceholder')}
        value={decisionPrompt}
        onChange={(event) => setDecisionPrompt(event.target.value)}
      />
      <div className="mt-3 flex flex-wrap gap-3">
        <button
          className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 bg-white px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={!canSubmit}
          type="button"
          onClick={() => void onRecommend(trimmedPrompt)}
        >
          <Sparkles className="size-4" />
          {t('roundtable.form.recommend')}
        </button>
        <button
          className="inline-flex items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40"
          disabled={!canSubmit}
          type="submit"
        >
          <Users className="size-4" />
          {t('roundtable.form.create')}
        </button>
      </div>
    </form>
  )
}
