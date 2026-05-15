import { createHash } from "node:crypto";
import { HttpError, prisma } from "wasp/server";
import type { RoundtableStream } from "wasp/server/api";
import {
  buildDiscussionWorkerRequest,
  buildFollowUpWorkerRequest,
  openRoundtableWorkerStream,
  parseWorkerStreamData,
  type WorkerStreamEvent,
} from "./workerClient";
import type { RoundtableLanguage, RoundtableSessionView } from "./types";
import { verifyRoundtableStreamToken } from "./streamToken";

type ReservedUsage = {
  id: string;
  userId: string;
  sessionId: string;
  operation: string;
  status: string;
  workerRequestId: string | null;
  creditDebitAmount: number;
  metadataJson: unknown;
};

export const roundtableStream: RoundtableStream = async (
  request,
  response,
  context,
) => {
  const userId = requireUserId(context);
  const token = getQueryString(request.query.token);
  if (!token) {
    throw new HttpError(401, "Roundtable stream token is required.");
  }

  const claims = verifyRoundtableStreamToken(token);
  if (claims.userId !== userId) {
    throw new HttpError(401, "Roundtable stream token user mismatch.");
  }

  const { usage, session } = await consumeStreamToken(claims);
  if (usage.operation !== claims.purpose) {
    throw new HttpError(401, "Roundtable stream token purpose mismatch.");
  }

  const abortController = new AbortController();
  let completed = false;
  request.on("close", () => {
    if (!completed) {
      abortController.abort();
      void markUsageCancelled(usage.id, session.id);
    }
  });

  response.setHeader("Content-Type", "text/event-stream");
  response.setHeader("Cache-Control", "no-cache, no-transform");
  response.setHeader("Connection", "keep-alive");
  response.flushHeaders?.();

  try {
    await prisma.roundtableSession.update({
      where: { id: session.id },
      data: { status: "streaming" },
    });
    const workerResponse = await openRoundtableWorkerStream(
      usage.operation === "follow_up"
        ? "/internal/roundtable/follow-up/stream"
        : "/internal/roundtable/discussions/stream",
      buildWorkerRequest(usage, session, userId),
      abortController.signal,
    );
    await proxyAndPersistWorkerStream(workerResponse, response, usage, session.id);
    completed = true;
    response.end();
  } catch (error) {
    if (!abortController.signal.aborted) {
      await markUsageError(usage.id, session.id, getErrorMessage(error));
      response.write(
        `event: roundtable.worker.v1.error\ndata: ${JSON.stringify({
          contractVersion: "roundtable.worker.v1",
          requestId: usage.workerRequestId ?? usage.id,
          sessionId: session.id,
          eventType: "roundtable.worker.v1.error",
          error: {
            contractVersion: "roundtable.worker.v1",
            requestId: usage.workerRequestId ?? usage.id,
            code: "wasp_stream_proxy_error",
            message: getErrorMessage(error),
            retryable: true,
          },
        })}\n\n`,
      );
    }
    completed = true;
    response.end();
  }
};

async function proxyAndPersistWorkerStream(
  workerResponse: Response,
  response: Parameters<RoundtableStream>[1],
  usage: ReservedUsage,
  sessionId: string,
) {
  const reader = workerResponse.body?.getReader();
  if (!reader) {
    throw new Error("Roundtable worker response body is empty.");
  }
  const decoder = new TextDecoder();
  let buffer = "";
  let sawTerminalEvent = false;

  while (true) {
    const { done, value } = await reader.read();
    if (done) {
      break;
    }
    const chunk = decoder.decode(value, { stream: true });
    response.write(chunk);
    buffer += chunk;
    const parsed = await drainSseFrames(buffer, usage, sessionId);
    buffer = parsed.remaining;
    sawTerminalEvent ||= parsed.sawTerminalEvent;
  }

  if (!sawTerminalEvent) {
    throw new Error("Roundtable worker stream ended without a terminal event.");
  }
}

async function drainSseFrames(
  buffer: string,
  usage: ReservedUsage,
  sessionId: string,
) {
  let remaining = buffer;
  let sawTerminalEvent = false;
  while (remaining.includes("\n\n")) {
    const boundary = remaining.indexOf("\n\n");
    const frame = remaining.slice(0, boundary);
    remaining = remaining.slice(boundary + 2);
    const data = frame
      .split("\n")
      .find((line) => line.startsWith("data: "))
      ?.slice("data: ".length);
    if (!data) {
      continue;
    }
    const event = parseWorkerStreamData(data);
    await persistWorkerEvent(event, usage);
    sawTerminalEvent ||=
      event.eventType === "roundtable.worker.v1.completed" ||
      event.eventType === "roundtable.worker.v1.error";
  }
  return { remaining, sawTerminalEvent };
}

async function persistWorkerEvent(
  event: WorkerStreamEvent,
  usage: ReservedUsage,
) {
  switch (event.eventType) {
    case "roundtable.worker.v1.message.completed":
      await prisma.roundtableMessage.create({
        data: {
          session: { connect: { id: event.sessionId } },
          persona: event.personaId
            ? { connect: { id: event.personaId } }
            : undefined,
          role: event.role,
          roundName: event.roundName,
          content: event.content,
          sequence: event.sequence,
        },
      });
      return;
    case "roundtable.worker.v1.artifact.updated":
      await prisma.roundtableArtifact.create({
        data: {
          session: { connect: { id: event.sessionId } },
          memo: event.payload.memo,
          recommendation: event.payload.recommendation,
          reasonsJson: event.payload.reasons,
          debateMapJson: event.payload.debateMap,
          metadataJson: { isFinal: event.isFinal },
        },
      });
      return;
    case "roundtable.worker.v1.completed":
      await completeUsage(usage.id);
      return;
    case "roundtable.worker.v1.error":
      await markUsageError(usage.id, event.sessionId, event.error.message);
      return;
    default:
      return;
  }
}

async function completeUsage(usageId: string) {
  await prisma.$transaction(async (tx) => {
    const usage = await tx.roundtableUsage.findUniqueOrThrow({
      where: { id: usageId },
    });
    await tx.roundtableUsage.update({
      where: { id: usageId },
      data: {
        status: "completed",
        completedAt: new Date(),
        errorMessage: null,
      },
    });
    await tx.roundtableSession.update({
      where: { id: usage.sessionId },
      data: { status: "completed" },
    });
    if (usage.creditDebitAmount > 0) {
      await tx.user.update({
        where: { id: usage.userId },
        data: { credits: { decrement: usage.creditDebitAmount } },
      });
    }
  });
}

async function markUsageError(
  usageId: string,
  sessionId: string,
  errorMessage: string,
) {
  await prisma.$transaction([
    prisma.roundtableUsage.updateMany({
      where: { id: usageId, status: { in: ["pending", "reserved"] } },
      data: {
        status: "error",
        errorAt: new Date(),
        errorMessage,
      },
    }),
    prisma.roundtableSession.update({
      where: { id: sessionId },
      data: { status: "error" },
    }),
  ]);
}

async function markUsageCancelled(usageId: string, sessionId: string) {
  await prisma.$transaction([
    prisma.roundtableUsage.updateMany({
      where: { id: usageId, status: { in: ["pending", "reserved"] } },
      data: {
        status: "cancelled",
        cancelledAt: new Date(),
      },
    }),
    prisma.roundtableSession.update({
      where: { id: sessionId },
      data: { status: "cancelled" },
    }),
  ]);
}

async function consumeStreamToken(
  claims: ReturnType<typeof verifyRoundtableStreamToken>,
) {
  const updated = await prisma.roundtableUsage.updateMany({
    where: {
      id: claims.usageId,
      userId: claims.userId,
      sessionId: claims.sessionId,
      status: "reserved",
      streamTokenNonce: claims.nonce,
    },
    data: { streamTokenNonce: null },
  });
  if (updated.count !== 1) {
    throw new HttpError(401, "Roundtable stream token has already been used.");
  }

  const usage = await prisma.roundtableUsage.findUniqueOrThrow({
    where: { id: claims.usageId },
  });
  const session = await prisma.roundtableSession.findFirst({
    where: { id: claims.sessionId, userId: claims.userId },
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
  return { usage, session: toSessionView(session) };
}

function buildWorkerRequest(
  usage: ReservedUsage,
  session: RoundtableSessionView,
  userId: string,
) {
  const requestId = usage.workerRequestId ?? usage.id;
  if (usage.operation === "follow_up") {
    const metadata = usage.metadataJson as { question?: string; language?: string };
    return buildFollowUpWorkerRequest({
      requestId,
      sessionId: session.id,
      userIdHash: hashUserId(userId),
      question: metadata.question ?? "",
      language: normalizeLanguage(metadata.language ?? session.language),
      personas: session.selectedPersonas,
      messages: session.transcript,
      artifact: session.artifact,
    });
  }
  return buildDiscussionWorkerRequest({
    requestId,
    sessionId: session.id,
    userIdHash: hashUserId(userId),
    decisionPrompt: session.decisionPrompt,
    language: normalizeLanguage(session.language),
    personas: session.selectedPersonas,
    priorMessages: session.transcript,
    artifact: session.artifact,
  });
}

function toSessionView(session: any): RoundtableSessionView {
  return {
    id: session.id,
    decisionPrompt: session.decisionPrompt,
    language: normalizeLanguage(session.language),
    status: session.status,
    createdAt: session.createdAt,
    updatedAt: session.updatedAt,
    selectedPersonas: session.selectedPersonas.map((item: any) => ({
      id: item.persona.id,
      skillName: item.persona.skillName,
      displayName: item.persona.displayName,
      sourceUrl: item.persona.sourceUrl,
      summary: item.persona.summary,
      selectionSource: item.selectionSource,
      selectionReason: item.selectionReason,
      sequence: item.sequence,
    })),
    transcript: session.messages.map((message: any) => ({
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

function requireUserId(context: { user?: { id: string } | null }) {
  if (!context.user) {
    throw new HttpError(401, "Only authenticated users can stream Roundtable.");
  }
  return context.user.id;
}

function getQueryString(value: unknown) {
  if (Array.isArray(value)) {
    return typeof value[0] === "string" ? value[0] : null;
  }
  return typeof value === "string" ? value : null;
}

function hashUserId(userId: string) {
  return createHash("sha256").update(userId).digest("hex");
}

function normalizeLanguage(value: string): RoundtableLanguage {
  return value === "en" ? "en" : "zh";
}

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : "Roundtable stream failed.";
}
