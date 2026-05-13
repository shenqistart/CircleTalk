import { MessageSquare, PauseCircle, Play, Send } from 'lucide-react'
import { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppLanguage } from '@/app/i18n'
import { DecisionArtifacts } from '@/features/roundtable/components/DecisionArtifacts'
import { DecisionPromptForm } from '@/features/roundtable/components/DecisionPromptForm'
import { PersonaPicker } from '@/features/roundtable/components/PersonaPicker'
import { RoundtableTimeline } from '@/features/roundtable/components/RoundtableTimeline'
import { usePersonaSelection } from '@/features/roundtable/hooks/usePersonaSelection'
import { useRoundtableChat } from '@/features/roundtable/hooks/useRoundtableChat'

export default function RoundtableWorkbench() {
  const { t } = useTranslation()
  const { language } = useAppLanguage()
  const personaSelection = usePersonaSelection(language)
  const chat = useRoundtableChat(language)
  const { refreshSession } = chat
  const selectedNamesText = chat.session?.selectedPersonas.map((persona) => persona.displayName).join('、')
  const selectedNames = selectedNamesText && selectedNamesText.length > 0 ? selectedNamesText : t('roundtable.session.waiting')

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session')
    if (sessionId) {
      void refreshSession(sessionId)
    }
  }, [refreshSession])

  async function handleRecommend(decisionPrompt: string): Promise<void> {
    await personaSelection.recommend(decisionPrompt)
  }

  async function handleCreate(decisionPrompt: string): Promise<void> {
    const personaIds = personaSelection.selectedPersonaIds.length > 0 ? personaSelection.selectedPersonaIds : undefined
    await chat.createSession({ decisionPrompt, personaIds })
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 md:px-6">
      <div className="flex flex-col gap-4 border-b border-zinc-200 pb-5 lg:flex-row lg:items-end lg:justify-between">
        <div className="min-w-0">
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-zinc-950">{t('roundtable.hero.title')}</h1>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-zinc-600">
            {t('roundtable.hero.description')}
          </p>
        </div>
        <div className="grid shrink-0 grid-cols-3 overflow-hidden rounded-lg border border-zinc-200 bg-white text-center shadow-sm">
          <div className="px-4 py-3">
            <p className="text-xs text-zinc-500">{t('roundtable.session.status')}</p>
            <p className="mt-1 text-sm font-semibold text-zinc-950">{chat.session?.status ?? 'idle'}</p>
          </div>
          <div className="border-x border-zinc-200 px-4 py-3">
            <p className="text-xs text-zinc-500">{t('roundtable.session.messages')}</p>
            <p className="mt-1 text-sm font-semibold text-zinc-950">{chat.session?.transcript.length ?? 0}</p>
          </div>
          <div className="px-4 py-3">
            <p className="text-xs text-zinc-500">{t('roundtable.session.personas')}</p>
            <p className="mt-1 text-sm font-semibold text-zinc-950">{chat.session?.selectedPersonas.length ?? personaSelection.selectedPersonaIds.length}</p>
          </div>
        </div>
      </div>
      {/* <DeploymentStatusBanner /> */}
      {personaSelection.errorMessage ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{personaSelection.errorMessage}</div> : null}
      {chat.errorMessage ? <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{chat.errorMessage}</div> : null}
      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="min-w-0 space-y-6">
          <DecisionPromptForm isBusy={chat.isStreaming} onCreate={handleCreate} onRecommend={handleRecommend} />
          <PersonaPicker
            isLoading={personaSelection.isLoading}
            onClear={personaSelection.clearSelection}
            onSelectAll={personaSelection.selectAll}
            onToggle={personaSelection.togglePersona}
            personas={personaSelection.personas}
            recommendedPersonas={personaSelection.recommendedPersonas}
            selectedPersonaIds={personaSelection.selectedPersonaIds}
          />
          {chat.session ? (
            <section className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0">
                  <p className="text-xs font-semibold uppercase text-emerald-700">{t('roundtable.session.title')}</p>
                  <h2 className="mt-1 break-all font-mono text-sm text-zinc-900">{chat.session.id}</h2>
                  <p className="mt-2 break-words text-sm text-zinc-600">{t('roundtable.session.selectedPersonas', { names: selectedNames })}</p>
                </div>
                <span className="shrink-0 rounded-full bg-zinc-100 px-3 py-1 text-xs font-medium text-zinc-700">{chat.session.status}</span>
              </div>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="inline-flex items-center gap-2 rounded-lg bg-emerald-700 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={chat.isStreaming}
                  type="button"
                  onClick={() => void chat.startDiscussion()}
                >
                  <Play className="size-4" />
                  {t('roundtable.session.startStream')}
                </button>
                <button
                  className="inline-flex items-center gap-2 rounded-lg border border-zinc-300 px-4 py-2 text-sm font-medium text-zinc-700 transition hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={!chat.isStreaming}
                  type="button"
                  onClick={chat.abort}
                >
                  <PauseCircle className="size-4" />
                  {t('roundtable.session.cancelStream')}
                </button>
              </div>
              <div className="mt-5 border-t border-zinc-200 pt-4">
                <label className="inline-flex items-center gap-2 text-sm font-medium text-zinc-700" htmlFor="follow-up-question">
                  <MessageSquare className="size-4" />
                  {t('roundtable.followUp.label')}
                </label>
                <textarea
                  className="mt-2 min-h-24 w-full resize-y rounded-lg border border-zinc-300 bg-zinc-50 p-3 text-sm leading-6 outline-none transition focus:border-emerald-600 focus:bg-white focus:ring-2 focus:ring-emerald-100"
                  id="follow-up-question"
                  placeholder={t('roundtable.followUp.placeholder')}
                  value={chat.followUpQuestion}
                  onChange={(event) => chat.setFollowUpQuestion(event.target.value)}
                />
                <button
                  className="mt-3 inline-flex items-center gap-2 rounded-lg bg-zinc-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={chat.isStreaming || !chat.followUpQuestion.trim()}
                  type="button"
                  onClick={() => void chat.submitFollowUp()}
                >
                  <Send className="size-4" />
                  {t('roundtable.followUp.submit')}
                </button>
              </div>
            </section>
          ) : null}
        </div>
        <div className="min-w-0 space-y-6">
          <RoundtableTimeline isStreaming={chat.isStreaming} messages={chat.session?.transcript ?? []} streamText={chat.streamText} />
          <DecisionArtifacts artifact={chat.session?.artifacts} />
        </div>
      </div>
    </div>
  )
}
