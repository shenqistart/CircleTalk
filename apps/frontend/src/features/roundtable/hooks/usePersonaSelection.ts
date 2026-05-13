import { useCallback, useEffect, useMemo, useState } from 'react'
import { roundtableApi } from '@/features/roundtable/api/roundtableApi'
import type { AppLanguage, RoundtablePersona } from '@/features/roundtable/types'

export function usePersonaSelection(language: AppLanguage) {
  const [personas, setPersonas] = useState<RoundtablePersona[]>([])
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([])
  const [recommendedPersonas, setRecommendedPersonas] = useState<RoundtablePersona[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  useEffect(() => {
    let isMounted = true
    roundtableApi
      .getPersonas(language)
      .then((items) => {
        if (isMounted) {
          setPersonas(items)
          setRecommendedPersonas([])
          setErrorMessage(null)
        }
      })
      .catch((error: unknown) => {
        if (isMounted) {
          setErrorMessage(error instanceof Error ? error.message : 'Persona loading failed')
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false)
        }
      })
    return () => {
      isMounted = false
    }
  }, [language])

  const selectedPersonas = useMemo(
    () => personas.filter((persona) => selectedPersonaIds.includes(persona.id)),
    [personas, selectedPersonaIds],
  )

  const togglePersona = useCallback((personaId: string) => {
    setSelectedPersonaIds((current) =>
      current.includes(personaId) ? current.filter((id) => id !== personaId) : [...current, personaId],
    )
  }, [])

  const selectAll = useCallback(() => {
    setSelectedPersonaIds(personas.map((persona) => persona.id))
  }, [personas])

  const clearSelection = useCallback(() => {
    setSelectedPersonaIds([])
  }, [])

  const recommend = useCallback(async (decisionPrompt: string) => {
    const items = await roundtableApi.recommendPersonas({ decisionPrompt, language })
    setRecommendedPersonas(items)
    return items
  }, [language])

  return {
    clearSelection,
    errorMessage,
    isLoading,
    personas,
    recommend,
    recommendedPersonas,
    selectAll,
    selectedPersonaIds,
    selectedPersonas,
    togglePersona,
  }
}
