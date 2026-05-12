import type { RoundtableMessage } from '@/features/roundtable/types'

const roundLabels: Record<RoundtableMessage['roundName'], string> = {
  closing: 'Closing',
  follow_up: 'Follow-up',
  opening: 'Opening',
  rebuttal: 'Rebuttal',
  synthesis: 'Moderator synthesis',
  system: 'System',
}

interface RoundtableTimelineProps {
  isStreaming: boolean
  messages: RoundtableMessage[]
  streamText: string
}

export function RoundtableTimeline({ isStreaming, messages, streamText }: RoundtableTimelineProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-blue-700">Step 3 · 多轮圆桌</p>
          <h2 className="text-xl font-bold text-slate-950">Opening / Rebuttal / Closing / Synthesis</h2>
        </div>
        {isStreaming ? <span className="rounded-full bg-green-100 px-3 py-1 text-xs font-medium text-green-700">Text Stream 中</span> : null}
      </div>
      <div className="space-y-3">
        {messages.map((message) => (
          <article className="rounded-xl border border-slate-100 bg-slate-50 p-4" key={message.id}>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-500">
              <span className="rounded-full bg-white px-2 py-1 font-semibold text-slate-700">{roundLabels[message.roundName]}</span>
              <span>{message.personaName ?? message.role}</span>
              <span>#{message.sequence}</span>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{message.content}</p>
          </article>
        ))}
        {streamText ? (
          <article className="rounded-xl border border-blue-100 bg-blue-50 p-4">
            <div className="mb-2 text-xs font-semibold text-blue-700">实时文本流</div>
            <p className="whitespace-pre-wrap text-sm leading-6 text-slate-800">{streamText}</p>
          </article>
        ) : null}
      </div>
    </section>
  )
}
