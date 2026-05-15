import type { Prisma } from "@prisma/client";
import { randomUUID } from "node:crypto";
import { HttpError, prisma } from "wasp/server";
import type {
  CreateRoundtableSession,
  GetRoundtablePersonas,
  GetRoundtableSession,
  GetRoundtableSessions,
  RecommendRoundtablePersonas,
  StartRoundtableDiscussion,
  SubmitRoundtableFollowUp,
} from "wasp/server/operations";
import * as z from "zod";
import { assertCanReserveRoundtableUsage } from "../../payment/entitlements";
import { ensureArgsSchemaOrThrowHttpError } from "../../server/validation";
import { defaultRoundtablePersonas } from "./personaCatalog";
import {
  createStreamTokenNonce,
  signRoundtableStreamToken,
  type RoundtableStreamPurpose,
} from "./streamToken";
import type {
  RoundtableLanguage,
  RoundtablePersonaView,
  RoundtableSessionSummary,
  RoundtableSessionView,
  RoundtableUsageView,
} from "./types";

const languageSchema = z.enum(["zh", "en"]).default("zh");

const recommendPersonasInputSchema = z.object({
  decisionPrompt: z.string().min(1).max(4000),
  language: languageSchema,
});

const createSessionInputSchema = recommendPersonasInputSchema.extend({
  personaIds: z.array(z.string().min(1)).default([]),
});

const sessionByIdInputSchema = z.object({
  sessionId: z.string().min(1),
});

const listSessionsInputSchema = z
  .object({
    limit: z.number().int().min(1).max(100).default(20),
  })
  .default({ limit: 20 });

const usageInputSchema = z.object({
  sessionId: z.string().min(1),
  idempotencyKey: z.string().min(16).max(160),
});

const followUpInputSchema = usageInputSchema.extend({
  question: z.string().min(1).max(4000),
  language: languageSchema,
});

export const getRoundtablePersonas: GetRoundtablePersonas<
  void,
  RoundtablePersonaView[]
> = async (_args, context) => {
  requireUserId(context);
  await syncDefaultPersonas();
  const personas = await context.entities.RoundtablePersona.findMany({
    orderBy: { displayName: "asc" },
  });
  return personas.map(toPersonaView);
};

export const recommendRoundtablePersonas: RecommendRoundtablePersonas<
  z.infer<typeof recommendPersonasInputSchema>,
  RoundtablePersonaView[]
> = async (rawArgs, context) => {
  requireUserId(context);
  const { decisionPrompt } = ensureArgsSchemaOrThrowHttpError(
    recommendPersonasInputSchema,
    rawArgs,
  );
  await syncDefaultPersonas();
  const personas = await context.entities.RoundtablePersona.findMany();
  return recommendPersonas(decisionPrompt, personas.map(toPersonaView));
};

export const createRoundtableSession: CreateRoundtableSession<
  z.infer<typeof createSessionInputSchema>,
  RoundtableSessionView
> = async (rawArgs, context) => {
  const userId = requireUserId(context);
  const { decisionPrompt, language, personaIds } =
    ensureArgsSchemaOrThrowHttpError(createSessionInputSchema, rawArgs);

  await syncDefaultPersonas();
  const selectedPersonas = await selectPersonas(decisionPrompt, personaIds);

  const session = await context.entities.RoundtableSession.create({
    data: {
      user: { connect: { id: userId } },
      decisionPrompt,
      language,
      status: "ready",
      metadataJson: {},
      selectedPersonas: {
        create: selectedPersonas.map((persona, index) => ({
          persona: { connect: { id: persona.id } },
          selectionSource: persona.selectionReason ? "auto" : "manual",
          selectionReason: persona.selectionReason,
          sequence: index + 1,
        })),
      },
      messages: {
        create: {
          role: "user",
          roundName: "system",
          content: decisionPrompt,
          sequence: 1,
        },
      },
    },
  });

  return getOwnedSessionOrThrow(context, session.id, userId);
};

export const getRoundtableSessions: GetRoundtableSessions<
  z.infer<typeof listSessionsInputSchema>,
  RoundtableSessionSummary[]
> = async (rawArgs, context) => {
  const userId = requireUserId(context);
  const { limit } = ensureArgsSchemaOrThrowHttpError(
    listSessionsInputSchema,
    rawArgs ?? {},
  );
  return context.entities.RoundtableSession.findMany({
    where: { userId },
    orderBy: { createdAt: "desc" },
    take: limit,
    select: {
      id: true,
      decisionPrompt: true,
      language: true,
      status: true,
      createdAt: true,
      updatedAt: true,
    },
  });
};

export const getRoundtableSession: GetRoundtableSession<
  z.infer<typeof sessionByIdInputSchema>,
  RoundtableSessionView
> = async (rawArgs, context) => {
  const userId = requireUserId(context);
  const { sessionId } = ensureArgsSchemaOrThrowHttpError(
    sessionByIdInputSchema,
    rawArgs,
  );
  return getOwnedSessionOrThrow(context, sessionId, userId);
};

export const startRoundtableDiscussion: StartRoundtableDiscussion<
  z.infer<typeof usageInputSchema>,
  { usage: RoundtableUsageView; streamPath: string; streamToken: string | null }
> = async (rawArgs, context) => {
  const userId = requireUserId(context);
  const { sessionId, idempotencyKey } = ensureArgsSchemaOrThrowHttpError(
    usageInputSchema,
    rawArgs,
  );
  await assertOwnsSession(context, sessionId, userId);
  const usage = await reservePendingUsage({
    userId,
    sessionId,
    operation: "discussion",
    idempotencyKey,
    requestedCredits: 1,
  });
  const streamToken = issueStreamToken(userId, sessionId, usage, "discussion");
  return {
    usage: toUsageView(usage),
    streamPath: streamToken
      ? `/roundtable/stream?token=${encodeURIComponent(streamToken)}`
      : `/roundtable/stream?usageId=${usage.id}`,
    streamToken,
  };
};

export const submitRoundtableFollowUp: SubmitRoundtableFollowUp<
  z.infer<typeof followUpInputSchema>,
  { usage: RoundtableUsageView; streamPath: string; streamToken: string | null }
> = async (rawArgs, context) => {
  const userId = requireUserId(context);
  const { sessionId, idempotencyKey, question, language } =
    ensureArgsSchemaOrThrowHttpError(followUpInputSchema, rawArgs);
  await assertOwnsSession(context, sessionId, userId);
  const usage = await reservePendingUsage({
    userId,
    sessionId,
    operation: "follow_up",
    idempotencyKey,
    requestedCredits: 0,
    metadataJson: { question, language },
  });
  const streamToken = issueStreamToken(userId, sessionId, usage, "follow_up");
  return {
    usage: toUsageView(usage),
    streamPath: streamToken
      ? `/roundtable/stream?token=${encodeURIComponent(streamToken)}`
      : `/roundtable/stream?usageId=${usage.id}`,
    streamToken,
  };
};

function requireUserId(context: { user?: { id: string } | null }): string {
  if (!context.user) {
    throw new HttpError(401, "Only authenticated users can access Roundtable.");
  }
  return context.user.id;
}

async function syncDefaultPersonas() {
  await prisma.$transaction(
    defaultRoundtablePersonas.map((persona) =>
      prisma.roundtablePersona.upsert({
        where: { id: persona.id },
        create: {
          id: persona.id,
          skillName: persona.skillName,
          displayName: persona.displayName,
          sourceUrl: persona.sourceUrl,
          summary: persona.summary,
          promptJson: { system: persona.prompt },
          metadataJson: { perspectiveTags: persona.perspectiveTags },
        },
        update: {
          skillName: persona.skillName,
          displayName: persona.displayName,
          sourceUrl: persona.sourceUrl,
          summary: persona.summary,
          promptJson: { system: persona.prompt },
          metadataJson: { perspectiveTags: persona.perspectiveTags },
        },
      }),
    ),
  );
}

function recommendPersonas(
  decisionPrompt: string,
  personas: RoundtablePersonaView[],
): RoundtablePersonaView[] {
  const normalizedPrompt = decisionPrompt.toLowerCase();
  const scored = personas.map((persona) => {
    const haystack = `${persona.displayName} ${persona.summary}`.toLowerCase();
    const score = normalizedPrompt
      .split(/\s+|，|。|、|；|：/)
      .filter(Boolean)
      .reduce((total, token) => total + (haystack.includes(token) ? 1 : 0), 0);
    return { persona, score };
  });

  return scored
    .sort((left, right) => right.score - left.score)
    .slice(0, 3)
    .map(({ persona }) => ({
      ...persona,
      selectionReason: "Recommended for the decision context.",
    }));
}

async function selectPersonas(decisionPrompt: string, personaIds: string[]) {
  if (personaIds.length > 0) {
    const personas = await prisma.roundtablePersona.findMany({
      where: { id: { in: personaIds } },
    });
    const byId = new Map(personas.map((persona) => [persona.id, persona]));
    return personaIds
      .map((id) => byId.get(id))
      .filter((persona): persona is NonNullable<typeof persona> => !!persona)
      .map((persona) => ({ ...toPersonaView(persona), selectionReason: null }));
  }

  const personas = await prisma.roundtablePersona.findMany();
  return recommendPersonas(decisionPrompt, personas.map(toPersonaView));
}

async function getOwnedSessionOrThrow(
  context: {
    entities: {
      RoundtableSession: typeof prisma.roundtableSession;
    };
  },
  sessionId: string,
  userId: string,
): Promise<RoundtableSessionView> {
  const session = await context.entities.RoundtableSession.findFirst({
    where: { id: sessionId, userId },
    include: {
      selectedPersonas: {
        include: { persona: true },
        orderBy: { sequence: "asc" },
      },
      messages: {
        include: { persona: true },
        orderBy: [{ sequence: "asc" }, { createdAt: "asc" }],
      },
      artifacts: {
        orderBy: { createdAt: "desc" },
        take: 1,
      },
    },
  });
  if (!session) {
    throw new HttpError(404, "Roundtable session not found.");
  }
  return {
    id: session.id,
    decisionPrompt: session.decisionPrompt,
    language: session.language,
    status: session.status,
    createdAt: session.createdAt,
    updatedAt: session.updatedAt,
    selectedPersonas: session.selectedPersonas.map((item) => ({
      ...toPersonaView(item.persona),
      selectionSource: item.selectionSource,
      selectionReason: item.selectionReason,
      sequence: item.sequence,
    })),
    transcript: session.messages.map((message) => ({
      id: message.id,
      role: message.role,
      roundName: message.roundName,
      content: message.content,
      sequence: message.sequence,
      personaId: message.personaId,
      parentMessageId: message.parentMessageId,
      createdAt: message.createdAt,
      personaName: message.persona?.displayName ?? null,
    })),
    artifact: session.artifacts[0] ?? null,
  };
}

async function assertOwnsSession(
  context: {
    entities: {
      RoundtableSession: typeof prisma.roundtableSession;
    };
  },
  sessionId: string,
  userId: string,
) {
  const session = await context.entities.RoundtableSession.findFirst({
    where: { id: sessionId, userId },
    select: { id: true },
  });
  if (!session) {
    throw new HttpError(404, "Roundtable session not found.");
  }
}

async function reservePendingUsage({
  userId,
  sessionId,
  operation,
  idempotencyKey,
  requestedCredits,
  metadataJson = {},
}: {
  userId: string;
  sessionId: string;
  operation: string;
  idempotencyKey: string;
  requestedCredits: number;
  metadataJson?: Prisma.InputJsonObject;
}) {
  return prisma.$transaction(async (tx) => {
    const existing = await tx.roundtableUsage.findUnique({
      where: { idempotencyKey },
    });
    if (existing) {
      if (existing.userId !== userId || existing.sessionId !== sessionId) {
        throw new HttpError(409, "Idempotency key belongs to another request.");
      }
      return existing;
    }

    const activeUsage = await tx.roundtableUsage.findFirst({
      where: {
        sessionId,
        operation,
        status: { in: ["pending", "reserved"] },
      },
    });
    if (activeUsage) {
      throw new HttpError(409, "Roundtable session already has active work.");
    }

    const user = await tx.user.findUniqueOrThrow({ where: { id: userId } });
    const outstanding = await tx.roundtableUsage.aggregate({
      where: { userId, status: { in: ["pending", "reserved"] } },
      _sum: { creditDebitAmount: true },
    });
    const creditDebitAmount = assertCanReserveRoundtableUsage(
      user,
      requestedCredits,
      outstanding._sum.creditDebitAmount ?? 0,
    );
    const now = new Date();
    return tx.roundtableUsage.create({
      data: {
        user: { connect: { id: userId } },
        session: { connect: { id: sessionId } },
        operation,
        idempotencyKey,
        status: "reserved",
        reservedAt: now,
        recoveryAfter: new Date(now.getTime() + 15 * 60 * 1000),
        workerRequestId: randomUUID(),
        streamTokenNonce: createStreamTokenNonce(),
        creditDebitAmount,
        metadataJson: metadataJson as Prisma.InputJsonValue,
      },
    });
  });
}

function issueStreamToken(
  userId: string,
  sessionId: string,
  usage: {
    id: string;
    status: string;
    streamTokenNonce: string | null;
  },
  purpose: RoundtableStreamPurpose,
) {
  if (usage.status !== "reserved" || !usage.streamTokenNonce) {
    return null;
  }
  return signRoundtableStreamToken({
    userId,
    sessionId,
    usageId: usage.id,
    purpose,
    nonce: usage.streamTokenNonce,
    expiresAt: Date.now() + 5 * 60 * 1000,
  });
}

function toPersonaView(persona: {
  id: string;
  skillName: string;
  displayName: string;
  sourceUrl: string | null;
  summary: string;
}): RoundtablePersonaView {
  return {
    id: persona.id,
    skillName: persona.skillName,
    displayName: persona.displayName,
    sourceUrl: persona.sourceUrl,
    summary: persona.summary,
  };
}

function toUsageView(usage: {
  id: string;
  operation: string;
  idempotencyKey: string;
  status: string;
  reservedAt: Date | null;
  completedAt: Date | null;
  cancelledAt: Date | null;
  errorAt: Date | null;
  recoveryAfter: Date | null;
  workerRequestId: string | null;
  streamTokenNonce: string | null;
  creditDebitAmount: number;
  errorMessage: string | null;
  createdAt: Date;
  updatedAt: Date;
}): RoundtableUsageView {
  return usage;
}
