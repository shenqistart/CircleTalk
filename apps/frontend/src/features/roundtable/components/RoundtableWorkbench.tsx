import { useEffect } from 'react'
import { DecisionArtifacts } from '@/features/roundtable/components/DecisionArtifacts'
import { DecisionPromptForm } from '@/features/roundtable/components/DecisionPromptForm'
import { DeploymentStatusBanner } from '@/features/roundtable/components/DeploymentStatusBanner'
import { PersonaPicker } from '@/features/roundtable/components/PersonaPicker'
import { RoundtableTimeline } from '@/features/roundtable/components/RoundtableTimeline'
import { usePersonaSelection } from '@/features/roundtable/hooks/usePersonaSelection'
import { useRoundtableChat } from '@/features/roundtable/hooks/useRoundtableChat'

export default function RoundtableWorkbench() {
  const personaSelection = usePersonaSelection()
  const chat = useRoundtableChat()
  const { refreshSession } = chat

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
    <div className="mx-auto max-w-7xl space-y-6">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-700">Roundtable decision advisor</p>
        <h1 className="mt-2 text-3xl font-bold text-slate-950">圆桌对话决策参谋</h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          输入一个决策题，系统可自动推荐 3-5 位人物，或保留你的手动选择优先级；后端按 Opening / Rebuttal / Closing 编排圆桌并持久化 transcript、三件套和追问。
        </p>
      </div>
      <DeploymentStatusBanner />
      {personaSelection.errorMessage ? <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{personaSelection.errorMessage}</div> : null}
      {chat.errorMessage ? <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700">{chat.errorMessage}</div> : null}
      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="space-y-6">
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
            <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className="text-sm text-slate-500">Session</p>
              <h2 className="mt-1 break-all font-mono text-sm text-slate-900">{chat.session.id}</h2>
              <p className="mt-2 text-sm text-slate-600">状态：{chat.session.status}</p>
              <p className="mt-2 text-sm text-slate-600">
                已选人物：{chat.session.selectedPersonas.map((persona) => persona.displayName).join('、') || '等待自动推荐'}
              </p>
              <div className="mt-4 flex flex-wrap gap-3">
                <button
                  className="rounded-lg bg-green-700 px-4 py-2 text-sm font-semibold text-white hover:bg-green-800 disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={chat.isStreaming}
                  type="button"
                  onClick={() => void chat.startDiscussion()}
                >
                  开始讨论流
                </button>
                <button className="rounded-lg border px-4 py-2 text-sm" disabled={!chat.isStreaming} type="button" onClick={chat.abort}>
                  取消流
                </button>
              </div>
              <div className="mt-5 border-t pt-4">
                <label className="text-sm font-medium text-slate-700" htmlFor="follow-up-question">
                  继续追问
                </label>
                <textarea
                  className="mt-2 min-h-20 w-full rounded-xl border border-slate-300 p-3 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
                  id="follow-up-question"
                  placeholder="基于刚才结论，我下一步该先问谁要资源？"
                  value={chat.followUpQuestion}
                  onChange={(event) => chat.setFollowUpQuestion(event.target.value)}
                />
                <button
                  className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
                  disabled={chat.isStreaming || !chat.followUpQuestion.trim()}
                  type="button"
                  onClick={() => void chat.submitFollowUp()}
                >
                  提交追问
                </button>
              </div>
            </section>
          ) : null}
        </div>
        <div className="space-y-6">
          <RoundtableTimeline isStreaming={chat.isStreaming} messages={chat.session?.transcript ?? []} streamText={chat.streamText} />
          <DecisionArtifacts artifact={chat.session?.artifacts} />
        </div>
      </div>
    </div>
  )
}
