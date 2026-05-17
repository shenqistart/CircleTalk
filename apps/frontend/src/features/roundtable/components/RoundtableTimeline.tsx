import { useEffect, useState } from 'react'
import { Radio, UserRound } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { RoundtableMessage } from '@/features/roundtable/types'

interface RoundtableTimelineProps {
  isStreaming: boolean
  messages: RoundtableMessage[]
}

export function RoundtableTimeline({ isStreaming, messages }: RoundtableTimelineProps) {
  const { t } = useTranslation()
  const firstMessageId = messages[0]?.id ?? ''

  return (
    <section className="min-w-0 overflow-hidden rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="min-w-0">
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
      <TimelineMessageList isStreaming={isStreaming} key={firstMessageId} messages={messages} />
    </section>
  )
}

interface TimelineMessageListProps {
  isStreaming: boolean
  messages: RoundtableMessage[]
}

function TimelineMessageList({ isStreaming, messages }: TimelineMessageListProps) {
  const { t } = useTranslation()
  const [visibleCount, setVisibleCount] = useState(0)
  const effectiveVisibleCount = isStreaming ? visibleCount : messages.length
  const visibleMessages = messages.slice(0, effectiveVisibleCount)

  useEffect(() => {
    if (!isStreaming || visibleCount >= messages.length) return undefined

    const timer = window.setTimeout(
      () => {
        setVisibleCount((current) => Math.min(current + 1, messages.length))
      },
      visibleCount === 0 ? 120 : 360,
    )

    return () => window.clearTimeout(timer)
  }, [isStreaming, messages.length, visibleCount])

  return (
    <div className="space-y-3">
      {visibleMessages.map((message, index) => (
        <TimelineMessageCard
          key={`${message.id}:${message.content}`}
          animationDelay={Math.min(index, 4) * 40}
          isStreaming={isStreaming}
          message={message}
        />
      ))}
      {isStreaming && visibleCount < messages.length ? (
        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800">
          <Radio className="size-3.5 animate-pulse" />
          {t('roundtable.timeline.revealing')}
        </div>
      ) : null}
      {isStreaming && visibleCount === messages.length ? (
        <div className="min-w-0 rounded-lg border border-dashed border-emerald-200 bg-emerald-50 p-4">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-800">
            <Radio className="size-3.5 animate-pulse" />
            {t('roundtable.timeline.waiting')}
          </div>
        </div>
      ) : null}
      {!messages.length && !isStreaming ? (
        <div className="rounded-lg border border-dashed border-zinc-300 bg-zinc-50 p-6 text-center text-sm text-zinc-500">{t('roundtable.timeline.empty')}</div>
      ) : null}
    </div>
  )
}

interface TimelineMessageCardProps {
  animationDelay: number
  isStreaming: boolean
  message: RoundtableMessage
}

function TimelineMessageCard({ animationDelay, isStreaming, message }: TimelineMessageCardProps) {
  const { t } = useTranslation()
  const prefersReducedMotion = usePrefersReducedMotion()
  const [revealedLength, setRevealedLength] = useState(0)
  const shouldType = isStreaming && !prefersReducedMotion
  const isTyping = shouldType && revealedLength < message.content.length
  const visibleContent = shouldType ? message.content.slice(0, revealedLength) : message.content

  useEffect(() => {
    if (!shouldType || revealedLength >= message.content.length) return undefined

    const charactersPerTick = getTypewriterStep(message.content.length)
    const timer = window.setTimeout(() => {
      setRevealedLength((current) => Math.min(current + charactersPerTick, message.content.length))
    }, 18)

    return () => window.clearTimeout(timer)
  }, [message.content.length, revealedLength, shouldType])

  return (
    <article
      className="roundtable-timeline-item min-w-0 rounded-lg border border-zinc-200 bg-zinc-50 p-4 shadow-sm"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-zinc-500">
        <span className="rounded-full bg-white px-2 py-1 font-semibold text-zinc-700 shadow-sm">{t(`roundtable.round.${message.roundName}`)}</span>
        <span className="inline-flex min-w-0 items-center gap-1">
          <UserRound className="size-3.5 shrink-0" />
          {message.personaName ?? message.role}
        </span>
        <span>#{message.sequence}</span>
      </div>
      <p className="whitespace-pre-wrap break-words text-sm leading-6 text-zinc-800">
        {visibleContent}
        {isTyping ? <span aria-hidden="true" className="ml-0.5 inline-block h-4 border-r border-zinc-500 align-[-0.125rem]" /> : null}
      </p>
    </article>
  )
}

function getTypewriterStep(contentLength: number): number {
  if (contentLength > 240) return 5
  if (contentLength > 120) return 3
  return 2
}

function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(() => getPrefersReducedMotion())

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    const handleChange = () => {
      setPrefersReducedMotion(mediaQuery.matches)
    }

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return prefersReducedMotion
}

function getPrefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}
