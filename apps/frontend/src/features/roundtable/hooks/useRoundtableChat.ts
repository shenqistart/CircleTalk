import { useCallback, useEffect, useState } from 'react'
import { getRoundtableStreamUrl, roundtableApi } from '@/features/roundtable/api/roundtableApi'
import type { AppLanguage, CreateRoundtableSessionInput, RoundtableSession } from '@/features/roundtable/types'

export const AI_SDK_TEXT_STREAM_PROTOCOL = 'text'

export function useRoundtableChat(language: AppLanguage) {
  const [session, setSession] = useState<RoundtableSession | null>(null)
  const [isStreaming, setIsStreaming] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [followUpQuestion, setFollowUpQuestion] = useState('')
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  const refreshSession = useCallback(async (sessionId: string) => {
    const restored = await roundtableApi.getSession(sessionId, language)
    setSession(restored)
    return restored
  }, [language])

  const createSession = useCallback(async (input: CreateRoundtableSessionInput) => {
    setErrorMessage(null)
    const result = await roundtableApi.createSession({ ...input, language })
    setSession(result.session)
    window.history.replaceState(null, '', `/roundtable?session=${result.session.id}`)
    return result.session
  }, [language])

  const consumeTextStream = useCallback(async (url: string, sessionId: string, init?: RequestInit) => {
    const controller = new AbortController()
    let refreshInFlight = false
    let isStreamActive = true
    const refreshDuringStream = async () => {
      if (refreshInFlight) return
      refreshInFlight = true
      try {
        const restored = await roundtableApi.getSession(sessionId, language)
        if (isStreamActive) {
          setSession(restored)
        }
      } catch {
        // Streaming can outlive a transient refresh failure; the final refresh still reports errors.
      } finally {
        refreshInFlight = false
      }
    }
    const refreshInterval = window.setInterval(() => {
      void refreshDuringStream()
    }, 900)

    setAbortController(controller)
    setIsStreaming(true)
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...init,
      })
      if (!response.ok) {
        throw new Error(`Discussion generation failed: ${response.status}`)
      }
      if (!response.body) {
        throw new Error('Discussion response body is empty')
      }
      const reader = response.body.getReader()
      let isComplete = false
      while (!isComplete) {
        const { done, value } = await reader.read()
        isComplete = done
        if (value) {
          void refreshDuringStream()
        }
      }
    } finally {
      window.clearInterval(refreshInterval)
      isStreamActive = false
      setAbortController(null)
      setIsStreaming(false)
    }
  }, [language])

  const startDiscussion = useCallback(async () => {
    if (!session) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id), session.id, { body: JSON.stringify({ language }) })
      return await refreshSession(session.id)
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        setErrorMessage(error instanceof Error ? error.message : 'Roundtable discussion failed')
      }
      return undefined
    }
  }, [consumeTextStream, language, refreshSession, session])

  const submitFollowUp = useCallback(async () => {
    if (!session || !followUpQuestion.trim()) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id, true), session.id, { body: JSON.stringify({ language, question: followUpQuestion.trim() }) })
      setFollowUpQuestion('')
      return await refreshSession(session.id)
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        setErrorMessage(error instanceof Error ? error.message : 'Follow-up failed')
      }
      return undefined
    }
  }, [consumeTextStream, followUpQuestion, language, refreshSession, session])

  const abort = useCallback(() => {
    abortController?.abort()
  }, [abortController])

  useEffect(() => {
    const sessionId = new URLSearchParams(window.location.search).get('session')
    if (sessionId) void refreshSession(sessionId).catch(() => undefined)
  }, [refreshSession])

  return {
    abort,
    createSession,
    errorMessage,
    followUpQuestion,
    isStreaming,
    refreshSession,
    session,
    setFollowUpQuestion,
    startDiscussion,
    submitFollowUp,
  }
}
