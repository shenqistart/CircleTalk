import type {
  CreateRoundtableSessionInput,
  CreateRoundtableSessionResult,
  DecisionArtifact,
  RecommendPersonasInput,
  RoundtableApiClient,
  RoundtableMessage,
  RoundtablePersona,
  RoundtableSession,
  SelectedPersona,
} from '@/features/roundtable/types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

const demoPersonas: RoundtablePersona[] = [
  {
    id: 'zeng-guofan',
    displayName: '曾国藩',
    skillName: 'nuwa-skill/zeng-guofan',
    summary: '重视长期主义、组织纪律与风险收敛。',
    selectionReason: '适合评估复杂选择中的耐心、节奏与组织代价。',
  },
  {
    id: 'socrates',
    displayName: '苏格拉底',
    skillName: 'nuwa-skill/socrates',
    summary: '通过追问拆解前提，避免被表象答案误导。',
    selectionReason: '适合识别决策题中的隐含假设。',
  },
  {
    id: 'drucker',
    displayName: '彼得·德鲁克',
    skillName: 'nuwa-skill/drucker',
    summary: '关注目标、责任、组织绩效与可执行管理动作。',
    selectionReason: '适合把讨论收敛到责任人与下一步。',
  },
  {
    id: 'munger',
    displayName: '查理·芒格',
    skillName: 'nuwa-skill/munger',
    summary: '强调反向思考、激励机制与跨学科模型。',
    selectionReason: '适合发现明显但容易忽略的失败路径。',
  },
]

function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(apiUrl(path), {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`Roundtable API request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

function toSelectedPersona(persona: RoundtablePersona, sequence: number, selectionSource: 'auto' | 'manual'): SelectedPersona {
  return { ...persona, sequence, selectionSource }
}

function createDemoMessages(sessionId: string, decisionPrompt: string, selectedPersonas: SelectedPersona[]): RoundtableMessage[] {
  const now = new Date().toISOString()
  const personas = selectedPersonas.length > 0 ? selectedPersonas : demoPersonas.slice(0, 3).map((persona, index) => toSelectedPersona(persona, index + 1, 'auto'))

  return [
    {
      id: `${sessionId}-user`,
      role: 'user',
      content: decisionPrompt,
      roundName: 'system',
      sequence: 1,
      createdAt: now,
    },
    ...personas.map((persona, index) => ({
      id: `${sessionId}-opening-${persona.id}`,
      role: 'persona' as const,
      personaId: persona.id,
      personaName: persona.displayName,
      content: `${persona.displayName}：先明确目标、约束与不可承受风险，再决定是否推进。`,
      roundName: 'opening' as const,
      sequence: index + 2,
      createdAt: now,
    })),
    {
      id: `${sessionId}-synthesis`,
      role: 'moderator',
      content: '主持人：请先启动讨论流。完成后系统会拉取三件套与完整 transcript。',
      roundName: 'synthesis',
      sequence: personas.length + 2,
      createdAt: now,
    },
  ]
}

function createDemoArtifact(selectedPersonas: SelectedPersona[]): DecisionArtifact {
  const debateMap = selectedPersonas.map((persona) => ({
    personaName: persona.displayName,
    position: '支持先做小规模验证，再投入完整资源。',
    keyConcern: persona.selectionReason ?? persona.summary,
  }))

  return {
    memo: '先用最小可逆实验验证关键假设，避免在目标、资源、风险未澄清时过早承诺。',
    recommendation: '建议推进一个两周试点，并设置清晰的停止条件。',
    reasons: ['保留选择权', '尽早暴露风险', '用真实反馈替代抽象争论'],
    debateMap,
  }
}

function createMockSession(input: CreateRoundtableSessionInput): CreateRoundtableSessionResult {
  const selectedPersonas = (input.personaIds?.length ? demoPersonas.filter((persona) => input.personaIds?.includes(persona.id)) : demoPersonas.slice(0, 3)).map(
    (persona, index) => toSelectedPersona(persona, index + 1, input.personaIds?.length ? 'manual' : 'auto'),
  )
  const now = new Date().toISOString()
  const session: RoundtableSession = {
    id: `mock-${Date.now()}`,
    decisionPrompt: input.decisionPrompt,
    status: 'ready',
    selectedPersonas,
    transcript: createDemoMessages(`mock-${Date.now()}`, input.decisionPrompt, selectedPersonas),
    artifacts: createDemoArtifact(selectedPersonas),
    createdAt: now,
    updatedAt: now,
  }

  return { session, recommendedPersonas: selectedPersonas }
}

export const roundtableApi: RoundtableApiClient = {
  async getPersonas() {
    try {
      return await fetchJson<RoundtablePersona[]>('/roundtable/personas')
    } catch {
      return demoPersonas
    }
  },

  async recommendPersonas(input: RecommendPersonasInput) {
    try {
      return await fetchJson<RoundtablePersona[]>('/roundtable/personas/recommend', {
        method: 'POST',
        body: JSON.stringify(input),
      })
    } catch {
      return demoPersonas.slice(0, 3)
    }
  },

  async createSession(input: CreateRoundtableSessionInput) {
    try {
      return await fetchJson<CreateRoundtableSessionResult>('/roundtable/sessions', {
        method: 'POST',
        body: JSON.stringify(input),
      })
    } catch {
      return createMockSession(input)
    }
  },

  async getSession(sessionId: string) {
    if (sessionId.startsWith('mock-')) {
      const fallback = createMockSession({ decisionPrompt: '本地演示会话' })
      return { ...fallback.session, id: sessionId }
    }

    return fetchJson<RoundtableSession>(`/roundtable/sessions/${sessionId}`)
  },
}

export function getRoundtableStreamUrl(sessionId: string, followUp = false): string {
  const suffix = followUp ? '/follow-up/stream' : '/stream'
  return apiUrl(`/roundtable/sessions/${sessionId}${suffix}`)
}
