import type {
  RoundtableArtifact,
  RoundtableMessage,
  RoundtablePersona,
  RoundtableSession,
  RoundtableSessionPersona,
  RoundtableUsage,
} from "wasp/entities";

export type RoundtableLanguage = "zh" | "en";
export type RoundtableSessionStatus =
  | "draft"
  | "ready"
  | "streaming"
  | "completed"
  | "error"
  | "cancelled";
export type RoundtableUsageStatus =
  | "pending"
  | "reserved"
  | "completed"
  | "error"
  | "cancelled";

export type RoundtablePersonaView = Pick<
  RoundtablePersona,
  "id" | "skillName" | "displayName" | "sourceUrl" | "summary"
> & {
  selectionReason?: string | null;
};

export type SelectedRoundtablePersonaView = RoundtablePersonaView &
  Pick<RoundtableSessionPersona, "selectionSource" | "selectionReason" | "sequence">;

export type RoundtableMessageView = Pick<
  RoundtableMessage,
  | "id"
  | "role"
  | "roundName"
  | "content"
  | "sequence"
  | "personaId"
  | "parentMessageId"
  | "createdAt"
> & {
  personaName?: string | null;
};

export type RoundtableArtifactView = Pick<
  RoundtableArtifact,
  | "id"
  | "memo"
  | "recommendation"
  | "reasonsJson"
  | "debateMapJson"
  | "metadataJson"
  | "createdAt"
  | "updatedAt"
>;

export type RoundtableSessionSummary = Pick<
  RoundtableSession,
  "id" | "decisionPrompt" | "language" | "status" | "createdAt" | "updatedAt"
>;

export type RoundtableSessionView = RoundtableSessionSummary & {
  selectedPersonas: SelectedRoundtablePersonaView[];
  transcript: RoundtableMessageView[];
  artifact: RoundtableArtifactView | null;
};

export type RoundtableUsageView = Pick<
  RoundtableUsage,
  | "id"
  | "operation"
  | "idempotencyKey"
  | "status"
  | "reservedAt"
  | "completedAt"
  | "cancelledAt"
  | "errorAt"
  | "recoveryAfter"
  | "workerRequestId"
  | "streamTokenNonce"
  | "creditDebitAmount"
  | "errorMessage"
  | "createdAt"
  | "updatedAt"
>;
