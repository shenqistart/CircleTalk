import * as z from "zod";
import { requireNodeEnvVar } from "../../server/utils";
import type {
  RoundtableArtifactView,
  RoundtableLanguage,
  RoundtableMessageView,
  SelectedRoundtablePersonaView,
} from "./types";

export const WORKER_CONTRACT_VERSION = "roundtable.worker.v1";

const workerArtifactSchema = z.object({
  memo: z.string(),
  recommendation: z.string(),
  reasons: z.array(z.string()).default([]),
  debateMap: z.array(z.record(z.string())).default([]),
});

const workerErrorSchema = z.object({
  contractVersion: z.literal(WORKER_CONTRACT_VERSION),
  requestId: z.string(),
  code: z.string(),
  message: z.string(),
  retryable: z.boolean(),
  details: z.record(z.unknown()).optional().nullable(),
});

const workerBaseEventSchema = z.object({
  contractVersion: z.literal(WORKER_CONTRACT_VERSION),
  requestId: z.string(),
  sessionId: z.string(),
});

export const workerStreamEventSchema = z.discriminatedUnion("eventType", [
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.started"),
    startedAt: z.string(),
  }),
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.message.delta"),
    messageId: z.string(),
    personaId: z.string().nullable().optional(),
    sequence: z.number().int().positive(),
    textDelta: z.string(),
  }),
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.message.completed"),
    messageId: z.string(),
    personaId: z.string().nullable().optional(),
    role: z.enum(["moderator", "persona", "user", "system"]),
    roundName: z.enum([
      "opening",
      "rebuttal",
      "closing",
      "synthesis",
      "follow_up",
      "system",
    ]),
    sequence: z.number().int().positive(),
    content: z.string(),
  }),
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.artifact.updated"),
    artifactType: z.literal("decision_artifact"),
    payload: workerArtifactSchema,
    isFinal: z.boolean(),
  }),
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.completed"),
    usage: z.record(z.unknown()).default({}),
    completedAt: z.string(),
  }),
  workerBaseEventSchema.extend({
    eventType: z.literal("roundtable.worker.v1.error"),
    error: workerErrorSchema,
  }),
]);

export type WorkerStreamEvent = z.infer<typeof workerStreamEventSchema>;

export function buildDiscussionWorkerRequest(input: {
  requestId: string;
  sessionId: string;
  userIdHash: string;
  decisionPrompt: string;
  language: RoundtableLanguage;
  personas: SelectedRoundtablePersonaView[];
  priorMessages: RoundtableMessageView[];
  artifact: RoundtableArtifactView | null;
}) {
  return {
    contractVersion: WORKER_CONTRACT_VERSION,
    requestId: input.requestId,
    sessionId: input.sessionId,
    userIdHash: input.userIdHash,
    decisionPrompt: input.decisionPrompt,
    language: input.language,
    personas: input.personas.map((persona) =>
      toWorkerPersona(persona, input.language),
    ),
    priorMessages: input.priorMessages.map(toWorkerMessage),
    artifact: input.artifact ? toWorkerArtifact(input.artifact) : undefined,
  };
}

export function buildFollowUpWorkerRequest(input: {
  requestId: string;
  sessionId: string;
  userIdHash: string;
  question: string;
  language: RoundtableLanguage;
  personas: SelectedRoundtablePersonaView[];
  messages: RoundtableMessageView[];
  artifact: RoundtableArtifactView | null;
}) {
  return {
    contractVersion: WORKER_CONTRACT_VERSION,
    requestId: input.requestId,
    sessionId: input.sessionId,
    userIdHash: input.userIdHash,
    question: input.question,
    language: input.language,
    personas: input.personas.map((persona) =>
      toWorkerPersona(persona, input.language),
    ),
    messages: input.messages.map(toWorkerMessage),
    artifact: input.artifact ? toWorkerArtifact(input.artifact) : undefined,
  };
}

export async function openRoundtableWorkerStream(
  path: "/internal/roundtable/discussions/stream" | "/internal/roundtable/follow-up/stream",
  payload: unknown,
  signal: AbortSignal,
) {
  const workerSecret = requireNonEmptyNodeEnvVar("AI_WORKER_SHARED_SECRET");
  const response = await fetch(`${workerBaseUrl()}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-AI-Worker-Secret": workerSecret,
    },
    body: JSON.stringify(payload),
    signal,
  });
  if (!response.ok || !response.body) {
    throw new Error(`Roundtable worker returned ${response.status}`);
  }
  return response;
}

export function parseWorkerStreamData(data: string): WorkerStreamEvent {
  return workerStreamEventSchema.parse(JSON.parse(data));
}

function toWorkerPersona(
  persona: SelectedRoundtablePersonaView,
  language: RoundtableLanguage,
) {
  return {
    id: persona.id,
    name: persona.displayName,
    title: persona.skillName,
    description: persona.summary,
    expertise: [],
    language,
    metadata: { sourceUrl: persona.sourceUrl },
    selectionSource: persona.selectionSource,
    selectionReason: persona.selectionReason,
    sequence: persona.sequence,
  };
}

function toWorkerMessage(message: RoundtableMessageView) {
  return {
    role: message.role,
    content: message.content,
    roundName: message.roundName,
    personaId: message.personaId,
    personaName: message.personaName,
    sequence: message.sequence,
  };
}

function toWorkerArtifact(artifact: RoundtableArtifactView) {
  return {
    memo: artifact.memo,
    recommendation: artifact.recommendation,
    reasons: artifact.reasonsJson,
    debateMap: artifact.debateMapJson,
  };
}

function workerBaseUrl() {
  return requireNonEmptyNodeEnvVar("AI_WORKER_URL").replace(/\/$/, "");
}

function requireNonEmptyNodeEnvVar(name: string) {
  const value = requireNodeEnvVar(name).trim();
  if (!value) {
    throw new Error(`Env var ${name} is empty`);
  }
  return value;
}
