export type RoundtableSessionStatus = 'draft' | 'ready' | 'streaming' | 'completed' | 'error' | 'cancelled'

export type PersonaSelectionSource = 'auto' | 'manual'

export interface RoundtablePersona {
  id: string
  displayName: string
  skillName: string
  summary: string
  selectionReason?: string
}

export interface SelectedPersona extends RoundtablePersona {
  selectionSource: PersonaSelectionSource
  sequence: number
}

export interface RoundtableMessage {
  id: string
  role: 'moderator' | 'persona' | 'user' | 'system'
  content: string
  personaId?: string
  personaName?: string
  roundName: 'opening' | 'rebuttal' | 'closing' | 'synthesis' | 'follow_up' | 'system'
  sequence: number
  createdAt: string
}

export interface DecisionArtifact {
  memo: string
  recommendation: string
  reasons: string[]
  debateMap: Array<{
    personaName: string
    position: string
    keyConcern: string
  }>
}

export interface RoundtableSession {
  id: string
  decisionPrompt: string
  status: RoundtableSessionStatus
  selectedPersonas: SelectedPersona[]
  transcript: RoundtableMessage[]
  artifacts?: DecisionArtifact
  createdAt: string
  updatedAt: string
}

export interface CreateRoundtableSessionInput {
  decisionPrompt: string
  personaIds?: string[]
}

export interface CreateRoundtableSessionResult {
  session: RoundtableSession
  recommendedPersonas: RoundtablePersona[]
}

export interface RecommendPersonasInput {
  decisionPrompt: string
}

export interface RoundtableApiClient {
  getPersonas(): Promise<RoundtablePersona[]>
  recommendPersonas(input: RecommendPersonasInput): Promise<RoundtablePersona[]>
  createSession(input: CreateRoundtableSessionInput): Promise<CreateRoundtableSessionResult>
  getSession(sessionId: string): Promise<RoundtableSession>
}
