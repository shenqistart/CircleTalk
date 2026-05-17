import { config } from "wasp/client";
import { useAuth } from "wasp/client/auth";
import {
  createRoundtableSession,
  getRoundtablePersonas,
  getRoundtableSession,
  getRoundtableSessions,
  recommendRoundtablePersonas,
  startRoundtableDiscussion,
  submitRoundtableFollowUp,
  useQuery,
} from "wasp/client/operations";
import { Link as WaspRouterLink, routes } from "wasp/client/router";
import { AlertCircle, BadgeDollarSign } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../client/components/ui/button";
import {
  DecisionArtifacts,
  DiscussionPanel,
  PersonaPicker,
  PromptPanel,
  RoundtableHeader,
  type RoundtableStep,
  type RoundtableStepId,
  RoundtableStepper,
  SessionList,
  type StreamPurpose,
  SummaryPanel,
} from "./RoundtableComponents";
import type { RoundtableLanguage, RoundtableSessionView } from "./server/types";

type WorkerStreamEvent = {
  eventType?: string;
  sessionId?: string;
  error?: { message?: string };
};

export default function RoundtablePage() {
  const auth = useAuth();
  const user = auth.data;
  const sessionsQuery = useQuery(getRoundtableSessions, { limit: 20 });
  const personasQuery = useQuery(getRoundtablePersonas);
  const [activeStep, setActiveStep] = useState<RoundtableStepId>("prompt");
  const [decisionPrompt, setDecisionPrompt] = useState("");
  const [language, setLanguage] = useState<RoundtableLanguage>("zh");
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);
  const [recommendedPersonaIds, setRecommendedPersonaIds] = useState<string[]>(
    [],
  );
  const [session, setSession] = useState<RoundtableSessionView | null>(null);
  const [followUpQuestion, setFollowUpQuestion] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRecommending, setIsRecommending] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [streamState, setStreamState] = useState<{
    purpose: StreamPurpose;
    status: "idle" | "streaming";
  }>({ purpose: "discussion", status: "idle" });
  const abortRef = useRef<AbortController | null>(null);

  const personas = personasQuery.data ?? [];
  const sessions = sessionsQuery.data ?? [];
  const isStreaming = streamState.status === "streaming";
  const selectedPersonas = useMemo(() => {
    if (session?.selectedPersonas.length) return session.selectedPersonas;
    return personas.filter((persona) =>
      selectedPersonaIds.includes(persona.id),
    );
  }, [personas, selectedPersonaIds, session?.selectedPersonas]);
  const steps = useMemo<RoundtableStep[]>(
    () =>
      getRoundtableSteps({
        hasArtifact: Boolean(session?.artifact),
        hasSession: Boolean(session),
        promptLength: decisionPrompt.trim().length,
        selectedPersonaCount: selectedPersonaIds.length,
      }),
    [decisionPrompt, selectedPersonaIds.length, session, session?.artifact],
  );
  const canStartDiscussion =
    Boolean(session) && !isStreaming && session?.status !== "completed";

  const refreshSession = useCallback(async (sessionId: string) => {
    const restored = await getRoundtableSession({ sessionId });
    setSession(restored);
    setDecisionPrompt((current) => current || restored.decisionPrompt);
    setLanguage(normalizeRoundtableLanguage(restored.language));
    setSelectedPersonaIds(
      restored.selectedPersonas.map((persona) => persona.id),
    );
    return restored;
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const sessionId = params.get("session");
    if (!sessionId) return;
    void refreshSession(sessionId)
      .then((restored) => {
        setActiveStep(restored.artifact ? "artifacts" : "discussion");
      })
      .catch((error: unknown) => {
        setErrorMessage(getErrorMessage(error));
      });
  }, [refreshSession]);

  async function handleRecommend() {
    const prompt = decisionPrompt.trim();
    if (!prompt) return;
    setErrorMessage(null);
    setIsRecommending(true);
    try {
      const recommendations = await recommendRoundtablePersonas({
        decisionPrompt: prompt,
        language,
      });
      const recommendedIds = recommendations.map((persona) => persona.id);
      setRecommendedPersonaIds(recommendedIds);
      setSelectedPersonaIds(recommendedIds);
      setActiveStep("personas");
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsRecommending(false);
    }
  }

  async function handleCreateSession() {
    const prompt = decisionPrompt.trim();
    if (!prompt) return;
    setErrorMessage(null);
    setIsCreating(true);
    try {
      const created = await createRoundtableSession({
        decisionPrompt: prompt,
        language,
        personaIds: selectedPersonaIds,
      });
      setSession(created);
      setSelectedPersonaIds(
        created.selectedPersonas.map((persona) => persona.id),
      );
      setActiveStep("discussion");
      await sessionsQuery.refetch();
      window.history.replaceState(
        null,
        "",
        `/roundtable?session=${created.id}`,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsCreating(false);
    }
  }

  async function handleRestoreSession(sessionId: string) {
    setErrorMessage(null);
    try {
      const restored = await refreshSession(sessionId);
      setActiveStep(restored.artifact ? "artifacts" : "discussion");
      window.history.replaceState(
        null,
        "",
        `/roundtable?session=${restored.id}`,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    }
  }

  async function handleStartDiscussion() {
    if (!session || !canStartDiscussion) return;
    setErrorMessage(null);
    try {
      const bootstrap = await startRoundtableDiscussion({
        idempotencyKey: makeIdempotencyKey("discussion"),
        sessionId: session.id,
      });
      await consumeRoundtableStream(
        bootstrap.streamPath,
        session.id,
        "discussion",
      );
      await Promise.all([
        refreshSession(session.id),
        auth.refetch(),
        sessionsQuery.refetch(),
      ]);
      setActiveStep("artifacts");
    } catch (error) {
      if (!isAbortError(error)) {
        setErrorMessage(getErrorMessage(error));
      }
    }
  }

  async function handleSubmitFollowUp() {
    const question = followUpQuestion.trim();
    if (!session || !question || isStreaming) return;
    setErrorMessage(null);
    try {
      const bootstrap = await submitRoundtableFollowUp({
        idempotencyKey: makeIdempotencyKey("follow-up"),
        language,
        question,
        sessionId: session.id,
      });
      setFollowUpQuestion("");
      setActiveStep("discussion");
      await consumeRoundtableStream(
        bootstrap.streamPath,
        session.id,
        "follow_up",
      );
      await Promise.all([
        refreshSession(session.id),
        auth.refetch(),
        sessionsQuery.refetch(),
      ]);
    } catch (error) {
      if (!isAbortError(error)) {
        setErrorMessage(getErrorMessage(error));
      }
    }
  }

  function handleStepChange(stepId: RoundtableStepId) {
    if (steps.find((step) => step.id === stepId)?.isAvailable) {
      setActiveStep(stepId);
    }
  }

  function handleAbortStream() {
    abortRef.current?.abort();
  }

  function togglePersona(personaId: string) {
    setSelectedPersonaIds((current) =>
      current.includes(personaId)
        ? current.filter((id) => id !== personaId)
        : [...current, personaId],
    );
  }

  async function consumeRoundtableStream(
    streamPath: string,
    sessionId: string,
    purpose: StreamPurpose,
  ) {
    const controller = new AbortController();
    abortRef.current = controller;
    setStreamState({ purpose, status: "streaming" });
    try {
      const response = await fetch(`${config.apiUrl}${streamPath}`, {
        method: "GET",
        signal: controller.signal,
      });
      if (!response.ok) {
        throw new Error(`Roundtable stream failed with ${response.status}.`);
      }
      if (!response.body) {
        throw new Error("Roundtable stream returned an empty body.");
      }
      await readSseStream(response.body, async (event) => {
        if (event.sessionId !== sessionId) return;
        if (event.eventType === "roundtable.worker.v1.error") {
          throw new Error(event.error?.message ?? "Roundtable worker failed.");
        }
        if (
          event.eventType === "roundtable.worker.v1.message.completed" ||
          event.eventType === "roundtable.worker.v1.artifact.updated" ||
          event.eventType === "roundtable.worker.v1.completed"
        ) {
          await refreshSession(sessionId);
        }
      });
    } finally {
      abortRef.current = null;
      setStreamState({ purpose, status: "idle" });
    }
  }

  return (
    <main className="mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:px-8">
      <section className="min-w-0 space-y-5">
        <RoundtableHeader
          credits={user?.credits ?? 0}
          email={user?.email}
          personaCount={selectedPersonaIds.length}
          session={session}
        />

        {errorMessage ? <RoundtableErrorBanner message={errorMessage} /> : null}

        <RoundtableStepper
          activeStep={activeStep}
          steps={steps}
          onStepChange={handleStepChange}
        />

        {activeStep === "prompt" ? (
          <PromptPanel
            decisionPrompt={decisionPrompt}
            isBusy={isCreating || isRecommending || isStreaming}
            language={language}
            onCreate={handleCreateSession}
            onDecisionPromptChange={setDecisionPrompt}
            onLanguageChange={setLanguage}
            onRecommend={handleRecommend}
          />
        ) : null}

        {activeStep === "personas" ? (
          <PersonaPicker
            isBusy={isCreating || isStreaming}
            isLoading={personasQuery.isLoading || isRecommending}
            personas={personas}
            recommendedPersonaIds={recommendedPersonaIds}
            selectedPersonaIds={selectedPersonaIds}
            onClear={() => setSelectedPersonaIds([])}
            onCreate={handleCreateSession}
            onSelectAll={() =>
              setSelectedPersonaIds(personas.map((persona) => persona.id))
            }
            onToggle={togglePersona}
          />
        ) : null}

        {activeStep === "discussion" ? (
          <DiscussionPanel
            canStartDiscussion={canStartDiscussion}
            followUpQuestion={followUpQuestion}
            isStreaming={isStreaming}
            selectedPersonas={selectedPersonas}
            session={session}
            streamPurpose={streamState.purpose}
            onAbortStream={handleAbortStream}
            onFollowUpQuestionChange={setFollowUpQuestion}
            onStartDiscussion={handleStartDiscussion}
            onSubmitFollowUp={handleSubmitFollowUp}
          />
        ) : null}

        {activeStep === "artifacts" ? (
          <DecisionArtifacts artifact={session?.artifact ?? null} />
        ) : null}
      </section>

      <aside className="min-w-0 space-y-4">
        <SessionList
          activeSessionId={session?.id ?? null}
          isLoading={sessionsQuery.isLoading}
          sessions={sessions}
          onRestore={handleRestoreSession}
        />
        <SummaryPanel
          activeStep={activeStep}
          isStreaming={isStreaming}
          personas={selectedPersonas}
          session={session}
        />
      </aside>
    </main>
  );
}

function RoundtableErrorBanner({ message }: { message: string }) {
  const shouldShowPricingLink =
    message.includes("402") ||
    /credits|subscription|out of credits/i.test(message);

  return (
    <div className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
      <AlertCircle className="mt-0.5 size-4 shrink-0" />
      <div className="min-w-0">
        <p className="font-medium">Circle 操作失败</p>
        <p className="mt-1 break-words">{message}</p>
        {shouldShowPricingLink ? (
          <Button asChild className="mt-3" size="sm">
            <WaspRouterLink to={routes.PricingPageRoute.to}>
              <BadgeDollarSign className="mr-2 size-4" />
              查看计费方案
            </WaspRouterLink>
          </Button>
        ) : null}
      </div>
    </div>
  );
}

function getRoundtableSteps({
  hasArtifact,
  hasSession,
  promptLength,
  selectedPersonaCount,
}: {
  hasArtifact: boolean;
  hasSession: boolean;
  promptLength: number;
  selectedPersonaCount: number;
}): RoundtableStep[] {
  const hasPrompt = promptLength > 0;
  const hasSelectedPersona = selectedPersonaCount > 0;

  return [
    { id: "prompt", isAvailable: true, isComplete: hasPrompt || hasSession },
    {
      id: "personas",
      isAvailable: hasPrompt || hasSession,
      isComplete: hasSession || hasSelectedPersona,
    },
    {
      id: "discussion",
      isAvailable: hasSession,
      isComplete: hasArtifact,
    },
    {
      id: "artifacts",
      isAvailable: hasArtifact,
      isComplete: hasArtifact,
    },
  ];
}

async function readSseStream(
  body: ReadableStream<Uint8Array>,
  onEvent: (event: WorkerStreamEvent) => Promise<void>,
) {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    while (buffer.includes("\n\n")) {
      const boundary = buffer.indexOf("\n\n");
      const frame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);
      const data = frame
        .split("\n")
        .find((line) => line.startsWith("data: "))
        ?.slice("data: ".length);
      if (!data) continue;
      await onEvent(JSON.parse(data) as WorkerStreamEvent);
    }
  }
}

function makeIdempotencyKey(prefix: string) {
  const suffix =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${suffix}`;
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Unknown error";
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function normalizeRoundtableLanguage(language: string | null | undefined) {
  return language === "en" ? "en" : "zh";
}
