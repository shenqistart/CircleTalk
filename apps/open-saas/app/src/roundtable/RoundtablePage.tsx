import { useAuth } from "wasp/client/auth";
import { config } from "wasp/client";
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
import {
  AlertCircle,
  BadgeDollarSign,
  Check,
  CheckCircle2,
  FileText,
  Loader2,
  Map,
  MessageSquare,
  PauseCircle,
  Play,
  Radio,
  RotateCcw,
  Send,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Button } from "../client/components/ui/button";
import { Textarea } from "../client/components/ui/textarea";
import { cn } from "../client/utils";
import type {
  RoundtableArtifactView,
  RoundtableMessageView,
  RoundtablePersonaView,
  RoundtableSessionSummary,
  RoundtableSessionView,
} from "./server/types";

type RoundtableLanguage = "zh" | "en";
type RoundtableStep = "prompt" | "personas" | "discussion" | "artifacts";
type StreamPurpose = "discussion" | "follow_up";

type WorkerStreamEvent = {
  eventType?: string;
  sessionId?: string;
  error?: { message?: string };
};

const ROUND_LABELS: Record<string, string> = {
  opening: "开场",
  rebuttal: "交锋",
  closing: "收束",
  synthesis: "综合",
  follow_up: "追问",
  system: "系统",
};

export default function RoundtablePage() {
  const auth = useAuth();
  const user = auth.data;
  const sessionsQuery = useQuery(getRoundtableSessions, { limit: 20 });
  const personasQuery = useQuery(getRoundtablePersonas);
  const [activeStep, setActiveStep] = useState<RoundtableStep>("prompt");
  const [decisionPrompt, setDecisionPrompt] = useState("");
  const [language, setLanguage] = useState<RoundtableLanguage>("zh");
  const [selectedPersonaIds, setSelectedPersonaIds] = useState<string[]>([]);
  const [recommendedPersonaIds, setRecommendedPersonaIds] = useState<string[]>([]);
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
  const selectedPersonas = useMemo(
    () => personas.filter((persona) => selectedPersonaIds.includes(persona.id)),
    [personas, selectedPersonaIds],
  );
  const canStartDiscussion =
    Boolean(session) && !isStreaming && session?.status !== "completed";

  const refreshSession = useCallback(async (sessionId: string) => {
    const restored = await getRoundtableSession({ sessionId });
    setSession(restored);
    setDecisionPrompt((current) => current || restored.decisionPrompt);
    setSelectedPersonaIds(restored.selectedPersonas.map((persona) => persona.id));
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
      setRecommendedPersonaIds(recommendations.map((persona) => persona.id));
      setSelectedPersonaIds(recommendations.map((persona) => persona.id));
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
      setSelectedPersonaIds(created.selectedPersonas.map((persona) => persona.id));
      setActiveStep("discussion");
      await sessionsQuery.refetch();
      window.history.replaceState(null, "", `/roundtable?session=${created.id}`);
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
      window.history.replaceState(null, "", `/roundtable?session=${restored.id}`);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    }
  }

  async function handleStartDiscussion() {
    if (!session || !canStartDiscussion) return;
    setErrorMessage(null);
    try {
      const bootstrap = await startRoundtableDiscussion({
        sessionId: session.id,
        idempotencyKey: makeIdempotencyKey("discussion"),
      });
      await consumeRoundtableStream(bootstrap.streamPath, session.id, "discussion");
      await Promise.all([refreshSession(session.id), auth.refetch(), sessionsQuery.refetch()]);
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
        sessionId: session.id,
        idempotencyKey: makeIdempotencyKey("follow-up"),
        question,
        language,
      });
      setFollowUpQuestion("");
      setActiveStep("discussion");
      await consumeRoundtableStream(bootstrap.streamPath, session.id, "follow_up");
      await Promise.all([refreshSession(session.id), auth.refetch(), sessionsQuery.refetch()]);
    } catch (error) {
      if (!isAbortError(error)) {
        setErrorMessage(getErrorMessage(error));
      }
    }
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

  return (
    <main className="mx-auto grid min-h-[calc(100vh-5rem)] w-full max-w-7xl gap-6 px-4 py-6 lg:grid-cols-[minmax(0,1fr)_22rem] lg:px-8">
      <section className="min-w-0 space-y-5">
        <div className="flex flex-col gap-4 border-b pb-5 md:flex-row md:items-end md:justify-between">
          <div className="min-w-0">
            <p className="text-sm font-medium text-muted-foreground">
              {user?.email}
            </p>
            <h1 className="mt-2 text-3xl font-semibold tracking-normal text-foreground">
              Circle Roundtable
            </h1>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              登录后的私有圆桌会议工作台。创建 Circle、启动 AI 讨论，并在完成后自动结算 credits。
            </p>
          </div>
          <div className="grid grid-cols-3 overflow-hidden rounded-lg border bg-card text-center shadow-sm">
            <StatusMetric label="Credits" value={user?.credits ?? 0} />
            <StatusMetric
              label="Plan"
              value={user?.subscriptionStatus ?? "trial"}
            />
            <StatusMetric label="Session" value={session?.status ?? "idle"} />
          </div>
        </div>

        {errorMessage ? (
          <div className="flex items-start gap-3 rounded-lg border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 size-4 shrink-0" />
            <div className="min-w-0">
              <p className="font-medium">Circle 操作失败</p>
              <p className="mt-1 break-words">{errorMessage}</p>
              {errorMessage.includes("402") || errorMessage.includes("credits") ? (
                <Button asChild className="mt-3" size="sm">
                  <WaspRouterLink to={routes.PricingPageRoute.to}>
                    <BadgeDollarSign className="mr-2 size-4" />
                    查看计费方案
                  </WaspRouterLink>
                </Button>
              ) : null}
            </div>
          </div>
        ) : null}

        <RoundtableStepper activeStep={activeStep} onStepChange={setActiveStep} />

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
          <PersonasPanel
            isBusy={isCreating || isStreaming}
            isLoading={personasQuery.isLoading || isRecommending}
            personas={personas}
            recommendedPersonaIds={recommendedPersonaIds}
            selectedPersonaIds={selectedPersonaIds}
            onClear={() => setSelectedPersonaIds([])}
            onCreate={handleCreateSession}
            onSelectAll={() => setSelectedPersonaIds(personas.map((persona) => persona.id))}
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
          <ArtifactsPanel artifact={session?.artifact ?? null} />
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
          personas={session?.selectedPersonas ?? selectedPersonas}
          session={session}
        />
      </aside>
    </main>
  );
}

function StatusMetric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0 border-r px-4 py-3 last:border-r-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-foreground">{value}</p>
    </div>
  );
}

function RoundtableStepper({
  activeStep,
  onStepChange,
}: {
  activeStep: RoundtableStep;
  onStepChange: (step: RoundtableStep) => void;
}) {
  const steps: Array<{ id: RoundtableStep; label: string; icon: typeof MessageSquare }> = [
    { id: "prompt", label: "决策题", icon: MessageSquare },
    { id: "personas", label: "角色", icon: Users },
    { id: "discussion", label: "讨论", icon: Radio },
    { id: "artifacts", label: "结论", icon: FileText },
  ];
  return (
    <nav className="grid gap-2 rounded-lg border bg-card p-2 sm:grid-cols-4">
      {steps.map((step) => {
        const Icon = step.icon;
        const isActive = activeStep === step.id;
        return (
          <button
            className={cn(
              "inline-flex items-center justify-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition",
              isActive
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:bg-muted hover:text-foreground",
            )}
            key={step.id}
            type="button"
            onClick={() => onStepChange(step.id)}
          >
            <Icon className="size-4" />
            {step.label}
          </button>
        );
      })}
    </nav>
  );
}

function PromptPanel({
  decisionPrompt,
  isBusy,
  language,
  onCreate,
  onDecisionPromptChange,
  onLanguageChange,
  onRecommend,
}: {
  decisionPrompt: string;
  isBusy: boolean;
  language: RoundtableLanguage;
  onCreate: () => Promise<void>;
  onDecisionPromptChange: (value: string) => void;
  onLanguageChange: (value: RoundtableLanguage) => void;
  onRecommend: () => Promise<void>;
}) {
  const canSubmit = decisionPrompt.trim().length > 0 && !isBusy;
  return (
    <section className="rounded-lg border bg-card p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">创建 Circle</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            写下需要圆桌讨论的决策问题，系统会推荐角色并创建私有 session。
          </p>
        </div>
        <div className="inline-flex rounded-lg border p-1">
          {(["zh", "en"] as const).map((item) => (
            <button
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium",
                language === item ? "bg-primary text-primary-foreground" : "text-muted-foreground",
              )}
              key={item}
              type="button"
              onClick={() => onLanguageChange(item)}
            >
              {item === "zh" ? "中文" : "English"}
            </button>
          ))}
        </div>
      </div>
      <Textarea
        className="mt-4 min-h-40 resize-y leading-6"
        maxLength={4000}
        placeholder="例如：我是否应该启动一个新的付费功能，并如何控制风险？"
        value={decisionPrompt}
        onChange={(event) => onDecisionPromptChange(event.currentTarget.value)}
      />
      <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
        <p className="text-xs text-muted-foreground">
          {decisionPrompt.trim().length}/4000
        </p>
        <div className="flex flex-wrap gap-3">
          <Button
            disabled={!canSubmit}
            type="button"
            variant="outline"
            onClick={() => void onRecommend()}
          >
            {isBusy ? <Loader2 className="mr-2 size-4 animate-spin" /> : <Sparkles className="mr-2 size-4" />}
            推荐角色
          </Button>
          <Button
            disabled={!canSubmit}
            type="button"
            onClick={() => void onCreate()}
          >
            <Users className="mr-2 size-4" />
            直接创建
          </Button>
        </div>
      </div>
    </section>
  );
}

function PersonasPanel({
  isBusy,
  isLoading,
  onClear,
  onCreate,
  onSelectAll,
  onToggle,
  personas,
  recommendedPersonaIds,
  selectedPersonaIds,
}: {
  isBusy: boolean;
  isLoading: boolean;
  personas: RoundtablePersonaView[];
  recommendedPersonaIds: string[];
  selectedPersonaIds: string[];
  onClear: () => void;
  onCreate: () => Promise<void>;
  onSelectAll: () => void;
  onToggle: (personaId: string) => void;
}) {
  return (
    <section className="rounded-lg border bg-card p-5 shadow-sm">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-foreground">选择圆桌角色</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            已选 {selectedPersonaIds.length} 位。为空时后端会根据问题自动选择。
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" type="button" variant="outline" onClick={onSelectAll}>
            全选
          </Button>
          <Button size="sm" type="button" variant="outline" onClick={onClear}>
            清空
          </Button>
          <Button
            disabled={isBusy}
            size="sm"
            type="button"
            onClick={() => void onCreate()}
          >
            {isBusy ? <Loader2 className="mr-2 size-4 animate-spin" /> : <CheckCircle2 className="mr-2 size-4" />}
            创建 session
          </Button>
        </div>
      </div>
      {isLoading ? (
        <div className="mt-4 flex items-center gap-2 rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          正在加载角色
        </div>
      ) : null}
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {personas.map((persona) => {
          const checked = selectedPersonaIds.includes(persona.id);
          const recommended = recommendedPersonaIds.includes(persona.id);
          return (
            <label
              className={cn(
                "min-w-0 cursor-pointer rounded-lg border p-4 transition",
                checked ? "border-primary bg-primary/5 shadow-sm" : "bg-background hover:bg-muted/40",
              )}
              key={persona.id}
            >
              <input
                checked={checked}
                className="sr-only"
                type="checkbox"
                onChange={() => onToggle(persona.id)}
              />
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <h3 className="break-words font-semibold text-foreground">
                    {persona.displayName}
                  </h3>
                  <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">
                    {persona.summary}
                  </p>
                  {persona.selectionReason ? (
                    <p className="mt-2 break-words text-xs leading-5 text-primary">
                      {persona.selectionReason}
                    </p>
                  ) : null}
                </div>
                <div className="flex shrink-0 flex-col items-end gap-2">
                  {recommended ? (
                    <span className="rounded-full bg-amber-100 px-2 py-1 text-xs text-amber-800">
                      推荐
                    </span>
                  ) : null}
                  {checked ? (
                    <span className="inline-flex size-6 items-center justify-center rounded-full bg-primary text-primary-foreground">
                      <Check className="size-4" />
                    </span>
                  ) : null}
                </div>
              </div>
            </label>
          );
        })}
      </div>
    </section>
  );
}

function DiscussionPanel({
  canStartDiscussion,
  followUpQuestion,
  isStreaming,
  onAbortStream,
  onFollowUpQuestionChange,
  onStartDiscussion,
  onSubmitFollowUp,
  selectedPersonas,
  session,
  streamPurpose,
}: {
  canStartDiscussion: boolean;
  followUpQuestion: string;
  isStreaming: boolean;
  selectedPersonas: RoundtablePersonaView[];
  session: RoundtableSessionView | null;
  streamPurpose: StreamPurpose;
  onAbortStream: () => void;
  onFollowUpQuestionChange: (value: string) => void;
  onStartDiscussion: () => Promise<void>;
  onSubmitFollowUp: () => Promise<void>;
}) {
  if (!session) {
    return (
      <section className="rounded-lg border border-dashed bg-card p-8 text-center text-sm text-muted-foreground">
        先创建或恢复一个 Circle session。
      </section>
    );
  }

  return (
    <div className="space-y-5">
      <section className="rounded-lg border bg-card p-5 shadow-sm">
        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0">
            <p className="text-xs font-semibold uppercase text-primary">Session</p>
            <h2 className="mt-1 break-all font-mono text-sm text-foreground">
              {session.id}
            </h2>
            <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">
              {session.decisionPrompt}
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              角色：{getPersonaNames(selectedPersonas)}
            </p>
          </div>
          <span className="shrink-0 rounded-full bg-muted px-3 py-1 text-xs font-medium text-muted-foreground">
            {session.status}
          </span>
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <Button
            disabled={!canStartDiscussion}
            type="button"
            onClick={() => void onStartDiscussion()}
          >
            {isStreaming && streamPurpose === "discussion" ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Play className="mr-2 size-4" />
            )}
            启动讨论并结算
          </Button>
          <Button
            disabled={!isStreaming}
            type="button"
            variant="outline"
            onClick={onAbortStream}
          >
            <PauseCircle className="mr-2 size-4" />
            中止 stream
          </Button>
        </div>
        <div className="mt-5 border-t pt-4">
          <label
            className="inline-flex items-center gap-2 text-sm font-medium text-foreground"
            htmlFor="follow-up-question"
          >
            <MessageSquare className="size-4" />
            追问
          </label>
          <Textarea
            className="mt-2 min-h-24 resize-y leading-6"
            disabled={isStreaming}
            id="follow-up-question"
            placeholder="继续追问这个 Circle，例如：给我一个更保守的迁移步骤。"
            value={followUpQuestion}
            onChange={(event) => onFollowUpQuestionChange(event.currentTarget.value)}
          />
          <Button
            className="mt-3"
            disabled={isStreaming || !followUpQuestion.trim()}
            type="button"
            onClick={() => void onSubmitFollowUp()}
          >
            {isStreaming && streamPurpose === "follow_up" ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <Send className="mr-2 size-4" />
            )}
            提交追问
          </Button>
        </div>
      </section>
      <Timeline messages={session.transcript} isStreaming={isStreaming} />
    </div>
  );
}

function Timeline({
  isStreaming,
  messages,
}: {
  isStreaming: boolean;
  messages: RoundtableMessageView[];
}) {
  return (
    <section className="rounded-lg border bg-card p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-foreground">讨论记录</h2>
        <span
          className={cn(
            "inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
            isStreaming ? "bg-emerald-100 text-emerald-800" : "bg-muted text-muted-foreground",
          )}
        >
          <Radio className={cn("size-3.5", isStreaming ? "animate-pulse" : "")} />
          {isStreaming ? "streaming" : `${messages.length} 条`}
        </span>
      </div>
      <div className="space-y-3">
        {messages.map((message) => (
          <article className="rounded-lg border bg-background p-4" key={message.id}>
            <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
              <span className="rounded-full bg-muted px-2 py-1 font-medium">
                {ROUND_LABELS[message.roundName] ?? message.roundName}
              </span>
              <span>{message.personaName ?? message.role}</span>
              <span>#{message.sequence}</span>
            </div>
            <p className="whitespace-pre-wrap break-words text-sm leading-6 text-foreground">
              {message.content}
            </p>
          </article>
        ))}
        {!messages.length && !isStreaming ? (
          <div className="rounded-lg border border-dashed p-6 text-center text-sm text-muted-foreground">
            还没有讨论记录。启动讨论后，Wasp 会通过私有 worker stream 持久化 transcript。
          </div>
        ) : null}
        {isStreaming ? (
          <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800">
            <Radio className="size-3.5 animate-pulse" />
            正在接收 worker 事件，完成消息会自动刷新
          </div>
        ) : null}
      </div>
    </section>
  );
}

function ArtifactsPanel({ artifact }: { artifact: RoundtableArtifactView | null }) {
  const reasons = asStringArray(artifact?.reasonsJson);
  const debateMap = asDebateMap(artifact?.debateMapJson);
  if (!artifact) {
    return (
      <section className="rounded-lg border border-dashed bg-card p-8 text-center text-sm text-muted-foreground">
        讨论完成后，这里会显示 memo、推荐结论、理由和争议地图。
      </section>
    );
  }
  return (
    <section className="rounded-lg border bg-card p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-foreground">Circle 结论</h2>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <ArtifactBlock icon={FileText} title="Memo" value={artifact.memo} />
        <ArtifactBlock icon={Target} title="Recommendation" value={artifact.recommendation} />
        <div className="rounded-lg border bg-background p-4">
          <h3 className="font-semibold text-foreground">Reasons</h3>
          <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
            {reasons.map((reason) => (
              <li className="flex gap-2" key={reason}>
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                <span className="break-words">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mt-4 rounded-lg border bg-background p-4">
        <h3 className="inline-flex items-center gap-2 font-semibold text-foreground">
          <Map className="size-4 text-primary" />
          Debate map
        </h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {debateMap.map((item) => (
            <div className="rounded-lg border bg-card p-3 text-sm" key={`${item.personaName}-${item.position}`}>
              <p className="break-words font-medium text-foreground">{item.personaName}</p>
              <p className="mt-1 break-words leading-6 text-muted-foreground">{item.position}</p>
              <p className="mt-1 break-words text-xs leading-5 text-muted-foreground">{item.keyConcern}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ArtifactBlock({
  icon: Icon,
  title,
  value,
}: {
  icon: typeof FileText;
  title: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border bg-background p-4">
      <h3 className="inline-flex items-center gap-2 font-semibold text-foreground">
        <Icon className="size-4 text-primary" />
        {title}
      </h3>
      <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">{value}</p>
    </div>
  );
}

function SessionList({
  activeSessionId,
  isLoading,
  onRestore,
  sessions,
}: {
  activeSessionId: string | null;
  isLoading: boolean;
  sessions: RoundtableSessionSummary[];
  onRestore: (sessionId: string) => Promise<void>;
}) {
  return (
    <section className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="font-semibold text-foreground">My Circle sessions</h2>
        {isLoading ? <Loader2 className="size-4 animate-spin text-muted-foreground" /> : null}
      </div>
      <div className="space-y-2">
        {sessions.map((item) => (
          <button
            className={cn(
              "w-full rounded-lg border p-3 text-left text-sm transition",
              activeSessionId === item.id ? "border-primary bg-primary/5" : "bg-background hover:bg-muted/40",
            )}
            key={item.id}
            type="button"
            onClick={() => void onRestore(item.id)}
          >
            <div className="flex items-center justify-between gap-3">
              <span className="truncate font-medium text-foreground">
                {item.decisionPrompt}
              </span>
              <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {item.status}
              </span>
            </div>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{item.id}</p>
          </button>
        ))}
        {!sessions.length && !isLoading ? (
          <div className="rounded-lg border border-dashed p-4 text-sm text-muted-foreground">
            还没有 session。
          </div>
        ) : null}
      </div>
    </section>
  );
}

function SummaryPanel({
  activeStep,
  isStreaming,
  personas,
  session,
}: {
  activeStep: RoundtableStep;
  isStreaming: boolean;
  personas: RoundtablePersonaView[];
  session: RoundtableSessionView | null;
}) {
  return (
    <section className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="size-4 text-primary" />
        <h2 className="font-semibold text-foreground">Flow summary</h2>
      </div>
      <dl className="mt-4 space-y-3 text-sm">
        <SummaryRow label="Step" value={activeStep} />
        <SummaryRow label="Status" value={session?.status ?? "idle"} />
        <SummaryRow label="Messages" value={session?.transcript.length ?? 0} />
        <SummaryRow label="Personas" value={personas.length} />
        <SummaryRow label="Billing" value={isStreaming ? "reserved" : "settled on complete"} />
      </dl>
    </section>
  );
}

function SummaryRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium text-foreground">{value}</dd>
    </div>
  );
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

function getPersonaNames(personas: RoundtablePersonaView[]) {
  return personas.map((persona) => persona.displayName).join("、") || "后端自动选择";
}

function getErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Unknown error";
}

function isAbortError(error: unknown) {
  return error instanceof DOMException && error.name === "AbortError";
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function asDebateMap(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const record = item as Record<string, unknown>;
      return {
        personaName: String(record.personaName ?? ""),
        position: String(record.position ?? ""),
        keyConcern: String(record.keyConcern ?? ""),
      };
    })
    .filter((item): item is { personaName: string; position: string; keyConcern: string } => Boolean(item));
}
