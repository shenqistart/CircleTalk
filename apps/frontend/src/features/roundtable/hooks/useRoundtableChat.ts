import { useCallback, useRef, useState } from 'react'
import { getRoundtableStreamUrl, roundtableApi } from '@/features/roundtable/api/roundtableApi'
import type { CreateRoundtableSessionInput, RoundtableSession } from '@/features/roundtable/types'

export const AI_SDK_TEXT_STREAM_PROTOCOL = 'text' as const

async function readTextStream(response: Response, onText: (text: string) => void): Promise<void> {
  if (!response.ok) {
    throw new Error(`Text Stream request failed: ${response.status}`)
  }
  const reader = response.body?.getReader()
  if (!reader) {
    return
  }
  const decoder = new TextDecoder()
  let done = false
  while (!done) {
    const result = await reader.read()
    done = result.done
    if (result.value) {
      onText(decoder.decode(result.value, { stream: !done }))
    }
  }
}

export function useRoundtableChat() {
  const [session, setSession] = useState<RoundtableSession | null>(null)
  const [streamText, setStreamText] = useState('')
  const [followUpQuestion, setFollowUpQuestion] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

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
    window.history.replaceState(null, '', `/roundtable?session=${encodeURIComponent(result.session.id)}`)
    return result
  }, [])

  const startDiscussion = useCallback(async () => {
    if (!session) {
      return
    }
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller
    setIsStreaming(true)
    setErrorMessage(null)
    setStreamText('')
    try {
      await readTextStream(
        await fetch(getRoundtableStreamUrl(session.id), {
          method: 'POST',
          headers: {
            Accept: 'text/plain',
            'X-AI-SDK-Stream-Protocol': AI_SDK_TEXT_STREAM_PROTOCOL,
          },
          signal: controller.signal,
        }),
        (chunk) => setStreamText((current) => `${current}${chunk}`),
      )
      await refreshSession(session.id)
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setErrorMessage(error instanceof Error ? error.message : '圆桌流式生成失败')
        await refreshSession(session.id)
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsStreaming(false)
      }
    }
  }, [refreshSession, session])

  const submitFollowUp = useCallback(async () => {
    if (!session || !followUpQuestion.trim()) {
      return
    }
    const controller = new AbortController()
    abortRef.current = controller
    setIsStreaming(true)
    setErrorMessage(null)
    setStreamText('')
    try {
      await readTextStream(
        await fetch(getRoundtableStreamUrl(session.id, true), {
          method: 'POST',
          headers: {
            Accept: 'text/plain',
            'Content-Type': 'application/json',
            'X-AI-SDK-Stream-Protocol': AI_SDK_TEXT_STREAM_PROTOCOL,
          },
          body: JSON.stringify({ question: followUpQuestion }),
          signal: controller.signal,
        }),
        (chunk) => setStreamText((current) => `${current}${chunk}`),
      )
      setFollowUpQuestion('')
      await refreshSession(session.id)
    } catch (error: unknown) {
      if (!controller.signal.aborted) {
        setErrorMessage(error instanceof Error ? error.message : '追问失败')
      }
    } finally {
      if (!controller.signal.aborted) {
        setIsStreaming(false)
      }
    }
  }, [followUpQuestion, refreshSession, session])

  const abort = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
  }, [])

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
