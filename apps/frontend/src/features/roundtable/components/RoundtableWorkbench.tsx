import { CheckCircle2, MessageSquare, PauseCircle, Play, Send, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useAppLanguage } from '@/app/i18n'
import { DecisionArtifacts } from '@/features/roundtable/components/DecisionArtifacts'
import { DecisionPromptForm } from '@/features/roundtable/components/DecisionPromptForm'
import { PersonaPicker } from '@/features/roundtable/components/PersonaPicker'
import { type RoundtableStep, type RoundtableStepId, RoundtableStepper } from '@/features/roundtable/components/RoundtableStepper'
import { RoundtableTimeline } from '@/features/roundtable/components/RoundtableTimeline'
import { usePersonaSelection } from '@/features/roundtable/hooks/usePersonaSelection'
import { useRoundtableChat } from '@/features/roundtable/hooks/useRoundtableChat'
import type { RoundtableSession, SelectedPersona } from '@/features/roundtable/types'

export default function RoundtableWorkbench() {
  const { t } = useTranslation()
  const { language } = useAppLanguage()
  const [activeStep, setActiveStep] = useState<RoundtableStepId>('prompt')
  const [decisionPrompt, setDecisionPrompt] = useState('')
  const personaSelection = usePersonaSelection(language)
  const chat = useRoundtableChat(language)
  const { refreshSession } = chat
  const selectedNames = getSelectedNames(chat.session?.selectedPersonas, t('roundtable.session.waiting'))
  const trimmedPrompt = decisionPrompt.trim()
  const hasSession = Boolean(chat.session)
  const isArtifactsReady = isSessionArtifactsReady(chat.session)
  const steps = useMemo<RoundtableStep[]>(
    () => getRoundtableSteps({
      hasSession,
      isArtifactsReady,
      promptLength: trimmedPrompt.length,
      selectedPersonaCount: personaSelection.selectedPersonaIds.length,
    }),
    [hasSession, isArtifactsReady, personaSelection.selectedPersonaIds.length, trimmedPrompt.length],
  )

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const sessionId = params.get('session')
    if (sessionId) {
      void refreshSession(sessionId).then((session) => {
        setDecisionPrompt((current) => current || session.decisionPrompt)
        setActiveStep(getRestoredStep(session))
      })
    }
  }, [refreshSession])

  async function handleRecommend(decisionPrompt: string): Promise<void> {
    await personaSelection.recommend(decisionPrompt)
    setActiveStep('personas')
  }

  async function handleCreate(decisionPrompt: string): Promise<void> {
    const personaIds = personaSelection.selectedPersonaIds.length > 0 ? personaSelection.selectedPersonaIds : undefined
    await chat.createSession({ decisionPrompt, personaIds })
    setActiveStep('discussion')
  }

  async function handleStartDiscussion(): Promise<void> {
    await chat.startDiscussion()
  }

  async function handleSubmitFollowUp(): Promise<void> {
    await chat.submitFollowUp()
    setActiveStep('discussion')
  }

  function handleStepChange(stepId: RoundtableStepId): void {
    if (steps.find((step) => step.id === stepId)?.isAvailable) {
      setActiveStep(stepId)
    }
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
      <RoundtableStepper activeStep={activeStep} steps={steps} onStepChange={handleStepChange} />
      <div className="grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="min-w-0">
          <RoundtableStepPanel
            activeStep={activeStep}
            chat={chat}
            decisionPrompt={decisionPrompt}
            personaSelection={personaSelection}
            selectedNames={selectedNames}
            trimmedPrompt={trimmedPrompt}
            onCreate={handleCreate}
            onDecisionPromptChange={setDecisionPrompt}
            onRecommend={handleRecommend}
            onStartDiscussion={handleStartDiscussion}
            onSubmitFollowUp={handleSubmitFollowUp}
          />
        </div>
        <div className="min-w-0 space-y-4">
          <section className="rounded-lg border border-zinc-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="size-4 text-emerald-700" />
              <h2 className="text-sm font-semibold text-zinc-950">{t('roundtable.summary.title')}</h2>
            </div>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex items-center justify-between gap-4">
                <dt className="text-zinc-500">{t('roundtable.summary.currentStep')}</dt>
                <dd className="font-medium text-zinc-900">{t(`roundtable.stepper.steps.${activeStep}.title`)}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-zinc-500">{t('roundtable.session.status')}</dt>
                <dd className="font-medium text-zinc-900">{chat.session?.status ?? 'idle'}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-zinc-500">{t('roundtable.session.messages')}</dt>
                <dd className="font-medium text-zinc-900">{chat.session?.transcript.length ?? 0}</dd>
              </div>
              <div className="flex items-center justify-between gap-4">
                <dt className="text-zinc-500">{t('roundtable.session.personas')}</dt>
                <dd className="font-medium text-zinc-900">{chat.session?.selectedPersonas.length ?? personaSelection.selectedPersonaIds.length}</dd>
              </div>
            </dl>
          </section>
        </div>
      </div>
    </div>
  )
}

function getSelectedNames(selectedPersonas: SelectedPersona[] | undefined, fallback: string): string {
  const selectedNamesText = selectedPersonas?.map((persona) => persona.displayName).join('、')
  return selectedNamesText && selectedNamesText.length > 0 ? selectedNamesText : fallback
}

function isSessionArtifactsReady(session: RoundtableSession | null): boolean {
  return Boolean(session?.artifacts && session.status === 'completed')
}

function getRestoredStep(session: RoundtableSession): RoundtableStepId {
  return isSessionArtifactsReady(session) ? 'artifacts' : 'discussion'
}

function getRoundtableSteps({
  hasSession,
  isArtifactsReady,
  promptLength,
  selectedPersonaCount,
}: {
  hasSession: boolean
  isArtifactsReady: boolean
  promptLength: number
  selectedPersonaCount: number
}): RoundtableStep[] {
  const hasPrompt = promptLength > 0
  const hasSelectedPersona = selectedPersonaCount > 0

  return [
    { id: 'prompt', isAvailable: true, isComplete: hasPrompt || hasSession },
    { id: 'personas', isAvailable: hasPrompt || hasSession, isComplete: hasSession || hasSelectedPersona },
    { id: 'discussion', isAvailable: hasSession, isComplete: isArtifactsReady },
    { id: 'artifacts', isAvailable: isArtifactsReady, isComplete: isArtifactsReady },
  ]
}

type PersonaSelectionState = ReturnType<typeof usePersonaSelection>
type RoundtableChatState = ReturnType<typeof useRoundtableChat>

interface RoundtableStepPanelProps {
  activeStep: RoundtableStepId
  chat: RoundtableChatState
  decisionPrompt: string
  personaSelection: PersonaSelectionState
  selectedNames: string
  trimmedPrompt: string
  onCreate: (decisionPrompt: string) => Promise<void>
  onDecisionPromptChange: (value: string) => void
  onRecommend: (decisionPrompt: string) => Promise<void>
  onStartDiscussion: () => Promise<void>
  onSubmitFollowUp: () => Promise<void>
}

function RoundtableStepPanel({
  activeStep,
  chat,
  decisionPrompt,
  onCreate,
  onDecisionPromptChange,
  onRecommend,
  onStartDiscussion,
  onSubmitFollowUp,
  personaSelection,
  selectedNames,
  trimmedPrompt,
}: RoundtableStepPanelProps) {
  const { t } = useTranslation()

  if (activeStep === 'prompt') {
    return (
      <DecisionPromptForm
        decisionPrompt={decisionPrompt}
        isBusy={chat.isStreaming}
        onCreate={onCreate}
        onDecisionPromptChange={onDecisionPromptChange}
        onRecommend={onRecommend}
      />
    )
  }

  if (activeStep === 'personas') {
    return (
      <div className="space-y-4">
        <PersonaPicker
          isLoading={personaSelection.isLoading}
          onClear={personaSelection.clearSelection}
          onSelectAll={personaSelection.selectAll}
          onToggle={personaSelection.togglePersona}
          personas={personaSelection.personas}
          recommendedPersonas={personaSelection.recommendedPersonas}
          selectedPersonaIds={personaSelection.selectedPersonaIds}
        />
        <div className="flex flex-col gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-zinc-600">{t('roundtable.picker.emptyAuto')}</p>
          <button
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-950 px-4 py-2 text-sm font-semibold text-white transition hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!trimmedPrompt || chat.isStreaming}
            type="button"
            onClick={() => void onCreate(trimmedPrompt)}
          >
            <Users className="size-4" />
            {t('roundtable.form.create')}
          </button>
        </div>
      </div>
    )
  }

  if (activeStep === 'discussion') {
    return (
      <div className="space-y-6">
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
                onClick={() => void onStartDiscussion()}
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
                onClick={() => void onSubmitFollowUp()}
              >
                <Send className="size-4" />
                {t('roundtable.followUp.submit')}
              </button>
            </div>
          </section>
        ) : (
          <section className="rounded-lg border border-dashed border-zinc-300 bg-white p-6 text-center text-sm text-zinc-500">
            {t('roundtable.session.empty')}
          </section>
        )}
        <RoundtableTimeline isStreaming={chat.isStreaming} messages={chat.session?.transcript ?? []} />
      </div>
    )
  }

  return <DecisionArtifacts artifact={chat.session?.artifacts} />
}
