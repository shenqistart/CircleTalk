-- CreateTable
CREATE TABLE "RoundtablePersona" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "skillName" TEXT NOT NULL,
    "displayName" TEXT NOT NULL,
    "sourceUrl" TEXT,
    "summary" TEXT NOT NULL,
    "promptJson" JSONB NOT NULL,
    "metadataJson" JSONB NOT NULL,

    CONSTRAINT "RoundtablePersona_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundtableSession" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,
    "decisionPrompt" TEXT NOT NULL,
    "language" TEXT NOT NULL DEFAULT 'zh',
    "status" TEXT NOT NULL DEFAULT 'ready',
    "metadataJson" JSONB NOT NULL,
    "expiresAt" TIMESTAMP(3),

    CONSTRAINT "RoundtableSession_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundtableSessionPersona" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sessionId" TEXT NOT NULL,
    "personaId" TEXT NOT NULL,
    "selectionSource" TEXT NOT NULL,
    "selectionReason" TEXT,
    "sequence" INTEGER NOT NULL,

    CONSTRAINT "RoundtableSessionPersona_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundtableMessage" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "sessionId" TEXT NOT NULL,
    "personaId" TEXT,
    "role" TEXT NOT NULL,
    "roundName" TEXT NOT NULL,
    "parentMessageId" TEXT,
    "content" TEXT NOT NULL,
    "sequence" INTEGER NOT NULL,

    CONSTRAINT "RoundtableMessage_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundtableArtifact" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "sessionId" TEXT NOT NULL,
    "memo" TEXT NOT NULL,
    "recommendation" TEXT NOT NULL,
    "reasonsJson" JSONB NOT NULL,
    "debateMapJson" JSONB NOT NULL,
    "metadataJson" JSONB NOT NULL,

    CONSTRAINT "RoundtableArtifact_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RoundtableUsage" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "userId" TEXT NOT NULL,
    "sessionId" TEXT NOT NULL,
    "operation" TEXT NOT NULL,
    "idempotencyKey" TEXT NOT NULL,
    "status" TEXT NOT NULL,
    "reservedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "cancelledAt" TIMESTAMP(3),
    "errorAt" TIMESTAMP(3),
    "recoveryAfter" TIMESTAMP(3),
    "workerRequestId" TEXT,
    "streamTokenNonce" TEXT,
    "creditDebitAmount" INTEGER NOT NULL DEFAULT 0,
    "errorMessage" TEXT,
    "metadataJson" JSONB NOT NULL,

    CONSTRAINT "RoundtableUsage_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "RoundtablePersona_displayName_idx" ON "RoundtablePersona"("displayName");

-- CreateIndex
CREATE INDEX "RoundtableSession_userId_createdAt_idx" ON "RoundtableSession"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "RoundtableSession_userId_status_idx" ON "RoundtableSession"("userId", "status");

-- CreateIndex
CREATE INDEX "RoundtableSessionPersona_sessionId_sequence_idx" ON "RoundtableSessionPersona"("sessionId", "sequence");

-- CreateIndex
CREATE UNIQUE INDEX "RoundtableSessionPersona_sessionId_personaId_key" ON "RoundtableSessionPersona"("sessionId", "personaId");

-- CreateIndex
CREATE INDEX "RoundtableMessage_sessionId_sequence_idx" ON "RoundtableMessage"("sessionId", "sequence");

-- CreateIndex
CREATE INDEX "RoundtableArtifact_sessionId_createdAt_idx" ON "RoundtableArtifact"("sessionId", "createdAt");

-- CreateIndex
CREATE UNIQUE INDEX "RoundtableUsage_idempotencyKey_key" ON "RoundtableUsage"("idempotencyKey");

-- CreateIndex
CREATE INDEX "RoundtableUsage_status_recoveryAfter_idx" ON "RoundtableUsage"("status", "recoveryAfter");

-- CreateIndex
CREATE INDEX "RoundtableUsage_sessionId_status_idx" ON "RoundtableUsage"("sessionId", "status");

-- CreateIndex
CREATE INDEX "RoundtableUsage_userId_createdAt_idx" ON "RoundtableUsage"("userId", "createdAt");

-- CreateIndex
CREATE INDEX "RoundtableUsage_workerRequestId_idx" ON "RoundtableUsage"("workerRequestId");

-- AddForeignKey
ALTER TABLE "RoundtableSession" ADD CONSTRAINT "RoundtableSession_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableSessionPersona" ADD CONSTRAINT "RoundtableSessionPersona_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "RoundtableSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableSessionPersona" ADD CONSTRAINT "RoundtableSessionPersona_personaId_fkey" FOREIGN KEY ("personaId") REFERENCES "RoundtablePersona"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableMessage" ADD CONSTRAINT "RoundtableMessage_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "RoundtableSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableMessage" ADD CONSTRAINT "RoundtableMessage_personaId_fkey" FOREIGN KEY ("personaId") REFERENCES "RoundtablePersona"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableArtifact" ADD CONSTRAINT "RoundtableArtifact_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "RoundtableSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableUsage" ADD CONSTRAINT "RoundtableUsage_userId_fkey" FOREIGN KEY ("userId") REFERENCES "User"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RoundtableUsage" ADD CONSTRAINT "RoundtableUsage_sessionId_fkey" FOREIGN KEY ("sessionId") REFERENCES "RoundtableSession"("id") ON DELETE CASCADE ON UPDATE CASCADE;
