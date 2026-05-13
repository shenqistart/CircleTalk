import type {
  AppLanguage,
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

const API_BASE_URL = String(import.meta.env.VITE_API_BASE_URL ?? '/api').replace(/\/$/, '')

const demoPersonasByLanguage: Record<AppLanguage, RoundtablePersona[]> = {
  en: [
    {
      id: 'zeng-guofan',
      displayName: 'Zeng Guofan',
      skillName: 'nuwa-skill/zeng-guofan',
      summary: 'Long-termism, organizational discipline, risk reduction, and gradual execution.',
      selectionReason: 'Useful for evaluating patience, cadence, and organizational cost in complex decisions.',
    },
    {
      id: 'socrates',
      displayName: 'Socrates',
      skillName: 'nuwa-skill/socrates',
      summary: 'Uses questions to unpack concepts, assumptions, and unstated premises.',
      selectionReason: 'Useful for identifying hidden assumptions inside the decision prompt.',
    },
    {
      id: 'drucker',
      displayName: 'Peter Drucker',
      skillName: 'nuwa-skill/drucker',
      summary: 'Goals, accountability, organizational performance, customer value, and executable management actions.',
      selectionReason: 'Useful for converging discussion into ownership and next steps.',
    },
    {
      id: 'munger',
      displayName: 'Charlie Munger',
      skillName: 'nuwa-skill/munger',
      summary: 'Inversion, incentives, opportunity cost, and multidisciplinary models.',
      selectionReason: 'Useful for finding obvious but easily missed failure paths.',
    },
  ],
  zh: [
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
  ],
}

function normalizedLanguage(language?: AppLanguage): AppLanguage {
  return language === 'en' ? 'en' : 'zh'
}

function demoPersonas(language?: AppLanguage): RoundtablePersona[] {
  return demoPersonasByLanguage[normalizedLanguage(language)]
}

function apiUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
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

function createDemoMessages(sessionId: string, decisionPrompt: string, selectedPersonas: SelectedPersona[], language?: AppLanguage): RoundtableMessage[] {
  const now = new Date().toISOString()
  const currentLanguage = normalizedLanguage(language)
  const personas = selectedPersonas.length > 0 ? selectedPersonas : demoPersonas(currentLanguage).slice(0, 3).map((persona, index) => toSelectedPersona(persona, index + 1, 'auto'))
  const personaLine = currentLanguage === 'en'
    ? (persona: SelectedPersona) => `${persona.displayName}: clarify goals, constraints, and unacceptable risks before deciding whether to proceed.`
    : (persona: SelectedPersona) => `${persona.displayName}：先明确目标、约束与不可承受风险，再决定是否推进。`
  const moderatorPending = currentLanguage === 'en'
    ? 'Moderator: start the discussion stream first. The full transcript and artifacts will refresh when it finishes.'
    : '主持人：请先启动讨论流。完成后系统会拉取三件套与完整记录。'

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
      content: personaLine(persona),
      roundName: 'opening' as const,
      sequence: index + 2,
      createdAt: now,
    })),
    {
      id: `${sessionId}-synthesis`,
      role: 'moderator',
      content: moderatorPending,
      roundName: 'synthesis',
      sequence: personas.length + 2,
      createdAt: now,
    },
  ]
}

function createDemoArtifact(selectedPersonas: SelectedPersona[], language?: AppLanguage): DecisionArtifact {
  const currentLanguage = normalizedLanguage(language)
  const debateMap = selectedPersonas.map((persona) => ({
    personaName: persona.displayName,
    position: currentLanguage === 'en' ? 'Supports validating with a small pilot before committing full resources.' : '支持先做小规模验证，再投入完整资源。',
    keyConcern: persona.selectionReason ?? persona.summary,
  }))

  return currentLanguage === 'en'
    ? {
        memo: 'Use a small reversible experiment to test the key assumptions before committing resources.',
        recommendation: 'Run a two-week pilot and define clear stop conditions.',
        reasons: ['Preserve options', 'Expose risks early', 'Replace abstract debate with real feedback'],
        debateMap,
      }
    : {
        memo: '先用最小可逆实验验证关键假设，避免在目标、资源、风险未澄清时过早承诺。',
        recommendation: '建议推进一个两周试点，并设置清晰的停止条件。',
        reasons: ['保留选择权', '尽早暴露风险', '用真实反馈替代抽象争论'],
        debateMap,
      }
}

function createMockSession(input: CreateRoundtableSessionInput): CreateRoundtableSessionResult {
  const hasManualSelection = Boolean(input.personaIds?.length)
  const personas = demoPersonas(input.language)
  const selectedPersonas = (hasManualSelection ? personas.filter((persona) => input.personaIds?.includes(persona.id)) : personas.slice(0, 3)).map(
    (persona, index) => toSelectedPersona(persona, index + 1, hasManualSelection ? 'manual' : 'auto'),
  )
  const now = new Date().toISOString()
  const sessionId = `mock-${Date.now()}`
  const session: RoundtableSession = {
    id: sessionId,
    decisionPrompt: input.decisionPrompt,
    status: 'ready',
    selectedPersonas,
    transcript: createDemoMessages(sessionId, input.decisionPrompt, selectedPersonas, input.language),
    artifacts: createDemoArtifact(selectedPersonas, input.language),
    createdAt: now,
    updatedAt: now,
  }

  return { session, recommendedPersonas: selectedPersonas }
}

export const roundtableApi: RoundtableApiClient = {
  async getPersonas(language) {
    try {
      return await fetchJson<RoundtablePersona[]>(`/roundtable/personas?language=${normalizedLanguage(language)}`)
    } catch {
      return demoPersonas(language)
    }
  },

  async recommendPersonas(input: RecommendPersonasInput) {
    try {
      return await fetchJson<RoundtablePersona[]>('/roundtable/personas/recommend', {
        method: 'POST',
        body: JSON.stringify(input),
      })
    } catch {
      return demoPersonas(input.language).slice(0, 3)
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

  getSession(sessionId: string, language?: AppLanguage) {
    if (sessionId.startsWith('mock-')) {
      const fallback = createMockSession({ decisionPrompt: language === 'en' ? 'Local demo session' : '本地演示会话', language })
      return Promise.resolve({ ...fallback.session, id: sessionId })
    }

    return fetchJson<RoundtableSession>(`/roundtable/sessions/${sessionId}`)
  },
}

export function getRoundtableStreamUrl(sessionId: string, followUp = false): string {
  const suffix = followUp ? '/follow-up/stream' : '/stream'
  return apiUrl(`/roundtable/sessions/${sessionId}${suffix}`)
}
