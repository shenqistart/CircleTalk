import type { RoundtableMessage } from '@/features/roundtable/types'

export function RoundtableTimeline({ messages, streamText }: { messages: RoundtableMessage[]; streamText: string }) {
  return (
    <section className="rounded-2xl border bg-white p-5 shadow-sm">
      <h2 className="font-semibold">多轮圆桌</h2>
      <div className="mt-4 space-y-3">
        {messages.map((message) => (
          <article key={message.id} className="rounded-xl bg-gray-50 p-3">
            <div className="text-xs uppercase tracking-wide text-gray-400">{message.roundName} · {message.personaName ?? message.role}</div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-gray-800">{message.content}</p>
          </article>
        ))}
        {streamText && (
          <article className="rounded-xl border border-dashed p-3">
            <div className="text-xs uppercase tracking-wide text-gray-400">streaming text</div>
            <p className="mt-1 whitespace-pre-wrap text-sm text-gray-800">{streamText}</p>
          </article>
        )}
      </div>
    </section>
  )
}
