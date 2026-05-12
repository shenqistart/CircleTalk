import { useCallback, useEffect, useState } from 'react'
import { getRoundtableStreamUrl, roundtableApi } from '@/features/roundtable/api/roundtableApi'
import type { RoundtableSession } from '@/features/roundtable/types'

export function useRoundtableChat() {
  const [session, setSession] = useState<RoundtableSession | null>(null)
  const [streamText, setStreamText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const restoreSession = useCallback(async (sessionId: string) => {
    const restored = await roundtableApi.getSession(sessionId)
    setSession(restored)
    return restored
  }, [])

  const createSession = useCallback(async (decisionPrompt: string, personaIds: string[]) => {
    setError(null)
    setStreamText('')
    const result = await roundtableApi.createSession({ decisionPrompt, personaIds: personaIds.length ? personaIds : undefined })
    setSession(result.session)
    window.history.replaceState(null, '', `/roundtable?session=${result.session.id}`)
    return result.session
  }, [])

  const consumeTextStream = useCallback(async (url: string, init?: RequestInit) => {
    setIsStreaming(true)
    setStreamText('')
    try {
      const response = await fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, ...init })
      if (!response.ok || !response.body) {
        throw new Error(`Text Stream failed: ${response.status}`)
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        setStreamText((current) => current + decoder.decode(value, { stream: true }))
      }
    } finally {
      setIsStreaming(false)
    }
  }, [])

  const startDiscussion = useCallback(async () => {
    if (!session) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id))
      await restoreSession(session.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : '圆桌讨论失败')
    }
  }, [consumeTextStream, restoreSession, session])

  const sendFollowUp = useCallback(async (question: string) => {
    if (!session) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id, true), { body: JSON.stringify({ question }) })
      await restoreSession(session.id)
    } catch (e) {
      setError(e instanceof Error ? e.message : '追问失败')
    }
  }, [consumeTextStream, restoreSession, session])

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get('session')
    if (sessionId) void restoreSession(sessionId).catch(() => undefined)
  }, [restoreSession])

  return { session, streamText, isStreaming, error, createSession, startDiscussion, sendFollowUp, restoreSession }
}
