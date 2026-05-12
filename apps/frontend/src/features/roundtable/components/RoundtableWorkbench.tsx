import { useEffect, useState } from 'react'
import { roundtableApi } from '@/features/roundtable/api/roundtableApi'
import { DecisionArtifacts } from '@/features/roundtable/components/DecisionArtifacts'
import { DecisionPromptForm } from '@/features/roundtable/components/DecisionPromptForm'
import { DeploymentStatusBanner } from '@/features/roundtable/components/DeploymentStatusBanner'
import { PersonaPicker } from '@/features/roundtable/components/PersonaPicker'
import { RoundtableTimeline } from '@/features/roundtable/components/RoundtableTimeline'
import { usePersonaSelection } from '@/features/roundtable/hooks/usePersonaSelection'
import { useRoundtableChat } from '@/features/roundtable/hooks/useRoundtableChat'
import type { RoundtablePersona } from '@/features/roundtable/types'

export default function RoundtableWorkbench() {
  const [personas, setPersonas] = useState<RoundtablePersona[]>([])
  const [followUp, setFollowUp] = useState('')
  const selection = usePersonaSelection(personas)
  const chat = useRoundtableChat()

  useEffect(() => {
    void roundtableApi.getPersonas().then(setPersonas)
  }, [])

  return (
    <div className="mx-auto max-w-6xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold">圆桌对话决策参谋</h1>
        <p className="mt-1 text-sm text-gray-500">输入决策题，选择或自动推荐人物，生成 Opening / Rebuttal / Closing 与三件套。</p>
      </div>
      <DeploymentStatusBanner />
      <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
        <div className="space-y-5">
          <DecisionPromptForm onSubmit={(prompt) => void chat.createSession(prompt, selection.selectedPersonaIds)} disabled={chat.isStreaming} />
          <PersonaPicker personas={personas} selectedIds={selection.selectedPersonaIds} onToggle={selection.togglePersona} onSelectAll={selection.selectAll} onClear={selection.clearSelection} />
          {chat.session && (
            <button type="button" onClick={() => void chat.startDiscussion()} disabled={chat.isStreaming} className="w-full rounded-xl bg-gray-900 px-4 py-3 text-sm font-medium text-white disabled:opacity-50">
              {chat.isStreaming ? '讨论生成中...' : '开始多轮讨论'}
            </button>
          )}
        </div>
        <div className="space-y-5">
          {chat.error && <div className="rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700">{chat.error}</div>}
          {chat.session && (
            <section className="rounded-2xl border bg-white p-5 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="font-semibold">Session {chat.session.id}</h2>
                  <p className="text-sm text-gray-500">状态：{chat.session.status}</p>
                </div>
                <div className="text-right text-sm text-gray-500">{chat.session.selectedPersonas.map((persona) => persona.displayName).join('、')}</div>
              </div>
            </section>
          )}
          <RoundtableTimeline messages={chat.session?.transcript ?? []} streamText={chat.streamText} />
          <DecisionArtifacts artifact={chat.session?.artifacts} />
          {chat.session?.artifacts && (
            <form
              onSubmit={(event) => {
                event.preventDefault()
                if (followUp.trim()) void chat.sendFollowUp(followUp.trim()).then(() => setFollowUp(''))
              }}
              className="rounded-2xl border bg-white p-5 shadow-sm"
            >
              <label className="text-sm font-semibold">继续追问</label>
              <div className="mt-2 flex gap-2">
                <input value={followUp} onChange={(event) => setFollowUp(event.target.value)} className="flex-1 rounded-xl border px-3 py-2 text-sm" placeholder="基于已有 transcript 和三件套继续提问" />
                <button className="rounded-xl bg-gray-900 px-4 py-2 text-sm text-white">发送</button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
