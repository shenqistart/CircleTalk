import { Radio, UserRound } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { RoundtableMessage } from '@/features/roundtable/types'

interface RoundtableTimelineProps {
  isStreaming: boolean
  messages: RoundtableMessage[]
  streamText: string
}

export function RoundtableTimeline({ isStreaming, messages, streamText }: RoundtableTimelineProps) {
  const { t } = useTranslation()
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-semibold uppercase text-emerald-700">{t('roundtable.timeline.step')}</p>
          <h2 className="mt-1 text-lg font-semibold text-zinc-950">{t('roundtable.timeline.title')}</h2>
        </div>
        <span
          className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${
            isStreaming ? 'bg-emerald-100 text-emerald-800' : 'bg-zinc-100 text-zinc-600'
          }`}
        >
          <Radio className={`size-3.5 ${isStreaming ? 'animate-pulse' : ''}`} />
          {isStreaming ? t('roundtable.timeline.streaming') : t('roundtable.timeline.messageCount', { count: messages.length })}
        </span>
      </div>
      <div className="space-y-3">
        {messages.map((message) => (
          <article className="min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4" key={message.id}>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
              <span className="rounded-full bg-white px-2 py-1 font-semibold text-zinc-700 shadow-sm">{t(`roundtable.round.${message.roundName}`)}</span>
              <span className="inline-flex min-w-0 items-center gap-1">
                <UserRound className="size-3.5 shrink-0" />
                {message.personaName ?? message.role}
              </span>
              <span>#{message.sequence}</span>
            </div>
            <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-800">{message.content}</p>
          </article>
        ))}
        {streamText ? (
          <article className="min-w-0 rounded-lg border border-emerald-200 bg-emerald-50 p-4">
            <div className="mb-2 inline-flex items-center gap-2 text-xs font-semibold text-emerald-800">
              <Radio className="size-3.5 animate-pulse" />
              {t('roundtable.timeline.live')}
            </div>
            <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-800">{streamText}</p>
          </article>
        ) : null}
        {!messages.length && !streamText ? (
          <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-6 text-center text-sm text-zinc-500">{t('roundtable.timeline.empty')}</div>
        ) : null}
      </div>
    </section>
  )
}
