import { useMemo, useState } from 'react'
import type { RoundtablePersona } from '@/features/roundtable/types'

export function usePersonaSelection(personas: RoundtablePersona[]) {
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([])

  const selectedPersonas = useMemo(
    () => personas.filter((persona) => selectedPersonaIds.includes(persona.id)),
    [personas, selectedPersonaIds],
  )

  function togglePersona(personaId: string) {
    setSelectedPersonaIds((current) =>
      current.includes(personaId) ? current.filter((id) => id !== personaId) : [...current, personaId],
    )
  }

  function selectAll() {
    setSelectedPersonaIds(personas.map((persona) => persona.id))
  }

  function clearSelection() {
    setSelectedPersonaIds([])
  }

  return { selectedPersonaIds, selectedPersonas, togglePersona, selectAll, clearSelection }
}
