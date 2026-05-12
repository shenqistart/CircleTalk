import { useCallback, useEffect, useState } from 'react'
import { getRoundtableStreamUrl, roundtableApi } from '@/features/roundtable/api/roundtableApi'
import type { CreateRoundtableSessionInput, RoundtableSession } from '@/features/roundtable/types'

export const AI_SDK_TEXT_STREAM_PROTOCOL = 'text'

export function useRoundtableChat() {
  const [session, setSession] = useState<RoundtableSession | null>(null)
  const [streamText, setStreamText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [followUpQuestion, setFollowUpQuestion] = useState('')
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  const refreshSession = useCallback(async (sessionId: string) => {
    const restored = await roundtableApi.getSession(sessionId)
    setSession(restored)
    return restored
  }, [])

  const createSession = useCallback(async (input: CreateRoundtableSessionInput) => {
    setErrorMessage(null)
    setStreamText('')
    const result = await roundtableApi.createSession(input)
    setSession(result.session)
    window.history.replaceState(null, '', `/roundtable?session=${result.session.id}`)
    return result.session
  }, [])

  const consumeTextStream = useCallback(async (url: string, init?: RequestInit) => {
    const controller = new AbortController()
    setAbortController(controller)
    setIsStreaming(true)
    setStreamText('')
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        signal: controller.signal,
        ...init,
      })
      if (!response.ok) {
        throw new Error(`Text Stream failed: ${response.status}`)
      }
      if (!response.body) {
        throw new Error('Text Stream response body is empty')
      }
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let isComplete = false
      while (!isComplete) {
        const { done, value } = await reader.read()
        isComplete = done
        if (value) {
          setStreamText((current) => current + decoder.decode(value, { stream: true }))
        }
      }
    } finally {
      setAbortController(null)
      setIsStreaming(false)
    }
  }, [])

  const startDiscussion = useCallback(async () => {
    if (!session) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id))
      await refreshSession(session.id)
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        setErrorMessage(error instanceof Error ? error.message : '圆桌讨论失败')
      }
    }
  }, [consumeTextStream, refreshSession, session])

  const submitFollowUp = useCallback(async () => {
    if (!session || !followUpQuestion.trim()) return
    try {
      await consumeTextStream(getRoundtableStreamUrl(session.id, true), { body: JSON.stringify({ question: followUpQuestion.trim() }) })
      setFollowUpQuestion('')
      await refreshSession(session.id)
    } catch (error) {
      if (!(error instanceof DOMException && error.name === 'AbortError')) {
        setErrorMessage(error instanceof Error ? error.message : '追问失败')
      }
    }
  }, [consumeTextStream, followUpQuestion, refreshSession, session])

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
    streamText,
    submitFollowUp,
  }
}
