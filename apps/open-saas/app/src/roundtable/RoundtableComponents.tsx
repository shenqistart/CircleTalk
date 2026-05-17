import {
  Check,
  CheckCircle2,
  Circle,
  Eraser,
  FileText,
  Loader2,
  Lock,
  Map,
  MessageSquare,
  PauseCircle,
  Play,
  Radio,
  Send,
  Sparkles,
  Target,
  UserRound,
  Users,
} from "lucide-react";
import { useEffect, useState } from "react";
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

export type RoundtableStepId =
  | "prompt"
  | "personas"
  | "discussion"
  | "artifacts";
export type StreamPurpose = "discussion" | "follow_up";

export interface RoundtableStep {
  id: RoundtableStepId;
  isAvailable: boolean;
  isComplete: boolean;
}

const STEP_COPY: Record<
  RoundtableStepId,
  { description: string; title: string }
> = {
  prompt: { description: "框定问题", title: "决策题" },
  personas: { description: "选择视角", title: "角色" },
  discussion: { description: "生成讨论", title: "讨论" },
  artifacts: { description: "查看结论", title: "结论" },
};

const ROUND_LABELS: Record<string, string> = {
  closing: "总结",
  follow_up: "追问",
  opening: "开场",
  rebuttal: "交锋",
  synthesis: "主持人综合",
  system: "系统",
};

export function RoundtableHeader({
  credits,
  email,
  personaCount,
  session,
}: {
  credits: number;
  email?: string | null;
  personaCount: number;
  session: RoundtableSessionView | null;
}) {
  return (
    <div className="flex flex-col gap-4 border-b pb-5 lg:flex-row lg:items-end lg:justify-between">
      <div className="min-w-0">
        {email ? (
          <p className="text-sm font-medium text-muted-foreground">{email}</p>
        ) : null}
        <h1 className="mt-2 text-3xl font-semibold tracking-normal text-foreground">
          圆桌对话决策参谋
        </h1>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
          输入问题，选择人物，生成开场、交锋、总结与主持人结论。
        </p>
      </div>
      <div className="grid shrink-0 grid-cols-3 overflow-hidden rounded-lg border bg-card text-center shadow-sm">
        <StatusMetric label="Credits" value={credits} />
        <StatusMetric label="Session" value={session?.status ?? "idle"} />
        <StatusMetric
          label="Personas"
          value={session?.selectedPersonas.length ?? personaCount}
        />
      </div>
    </div>
  );
}

export function RoundtableStepper({
  activeStep,
  onStepChange,
  steps,
}: {
  activeStep: RoundtableStepId;
  onStepChange: (stepId: RoundtableStepId) => void;
  steps: RoundtableStep[];
}) {
  return (
    <nav
      aria-label="圆桌进度"
      className="rounded-lg border bg-card p-3 shadow-sm"
    >
      <ol className="grid gap-2 lg:grid-cols-4">
        {steps.map((step, index) => {
          const isActive = step.id === activeStep;
          const isLocked = !step.isAvailable;
          const StepIcon = getStepIcon(step);
          const copy = STEP_COPY[step.id];

          return (
            <li key={step.id}>
              <button
                aria-current={isActive ? "step" : undefined}
                className={cn(
                  "flex h-full w-full items-center gap-3 rounded-lg border px-3 py-3 text-left transition",
                  isActive &&
                    "border-primary bg-primary/10 text-foreground shadow-sm",
                  !isActive &&
                    step.isComplete &&
                    "border-border bg-card text-foreground hover:border-primary/50 hover:bg-primary/5",
                  !isActive &&
                    !step.isComplete &&
                    !isLocked &&
                    "border-border bg-card text-muted-foreground hover:bg-muted",
                  isLocked &&
                    "cursor-not-allowed border-border/70 bg-muted/40 text-muted-foreground/70",
                )}
                disabled={isLocked}
                type="button"
                onClick={() => onStepChange(step.id)}
              >
                <span
                  className={cn(
                    "inline-flex size-8 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                    isActive &&
                      "border-primary bg-primary text-primary-foreground",
                    !isActive &&
                      step.isComplete &&
                      "border-primary/20 bg-primary/10 text-primary",
                    !isActive &&
                      !step.isComplete &&
                      !isLocked &&
                      "border-border bg-muted text-muted-foreground",
                    isLocked &&
                      "border-border bg-card text-muted-foreground/70",
                  )}
                >
                  {getStepIndicator({
                    StepIcon,
                    index,
                    isComplete: step.isComplete,
                    isLocked,
                  })}
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">
                    {copy.title}
                  </span>
                  <span className="mt-0.5 block truncate text-xs opacity-75">
                    {copy.description}
                  </span>
                </span>
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

export function PromptPanel({
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
  language: "zh" | "en";
  onCreate: () => Promise<void>;
  onDecisionPromptChange: (value: string) => void;
  onLanguageChange: (value: "zh" | "en") => void;
  onRecommend: () => Promise<void>;
}) {
  const trimmedPrompt = decisionPrompt.trim();
  const canSubmit = trimmedPrompt.length > 0 && !isBusy;

  return (
    <form
      className="min-w-0 overflow-hidden rounded-lg border bg-card p-5 shadow-sm"
      onSubmit={(event) => {
        event.preventDefault();
        if (canSubmit) void onCreate();
      }}
    >
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-foreground">问题</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            写下需要圆桌讨论的决策题，系统会推荐角色并创建私有 session。
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-3">
          <span className="rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
            {trimmedPrompt.length}/4000
          </span>
          <div className="inline-flex rounded-lg border p-1">
            {(["zh", "en"] as const).map((item) => (
              <button
                className={cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition",
                  language === item
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted",
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
      </div>
      <Textarea
        className="min-h-40 resize-y leading-6"
        maxLength={4000}
        placeholder="例如：我是否应该在今年把团队从外包交付转成自研产品？"
        value={decisionPrompt}
        onChange={(event) => onDecisionPromptChange(event.currentTarget.value)}
      />
      <div className="mt-3 flex flex-wrap gap-3">
        <Button
          disabled={!canSubmit}
          type="button"
          variant="outline"
          onClick={() => void onRecommend()}
        >
          {isBusy ? (
            <Loader2 className="mr-2 size-4 animate-spin" />
          ) : (
            <Sparkles className="mr-2 size-4" />
          )}
          推荐人物
        </Button>
        <Button disabled={!canSubmit} type="submit">
          <Users className="mr-2 size-4" />
          创建圆桌会话
        </Button>
      </div>
    </form>
  );
}

export function PersonaPicker({
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
  const selectedCount = selectedPersonaIds.length;
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border bg-card p-5 shadow-sm">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-foreground">人物选择</h2>
          <p className="mt-1 text-xs text-muted-foreground">
            已选 {selectedCount} 人，不选则自动推荐。
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          <Button
            size="sm"
            type="button"
            variant="outline"
            onClick={onSelectAll}
          >
            <Users className="mr-1.5 size-3.5" />
            全选
          </Button>
          <Button size="sm" type="button" variant="outline" onClick={onClear}>
            <Eraser className="mr-1.5 size-3.5" />
            清空
          </Button>
          <Button
            disabled={isBusy}
            size="sm"
            type="button"
            onClick={() => void onCreate()}
          >
            {isBusy ? (
              <Loader2 className="mr-2 size-4 animate-spin" />
            ) : (
              <CheckCircle2 className="mr-2 size-4" />
            )}
            创建 session
          </Button>
        </div>
      </div>
      {isLoading ? (
        <div className="mb-4 flex items-center gap-2 rounded-lg border border-dashed bg-muted/40 p-4 text-sm text-muted-foreground">
          <Loader2 className="size-4 animate-spin" />
          人物加载中...
        </div>
      ) : null}
      <div className="grid min-w-0 gap-3 md:grid-cols-2">
        {personas.map((persona) => {
          const checked = selectedPersonaIds.includes(persona.id);
          const recommended = recommendedPersonaIds.includes(persona.id);
          return (
            <label
              className={cn(
                "min-w-0 cursor-pointer rounded-lg border p-4 transition",
                checked
                  ? "border-primary bg-primary/5 shadow-sm"
                  : "bg-background hover:bg-muted/40",
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
                      <Check className="size-3.5" />
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

export function DiscussionPanel({
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
            <p className="text-xs font-semibold uppercase text-primary">
              Session
            </p>
            <h2 className="mt-1 break-all font-mono text-sm text-foreground">
              {session.id}
            </h2>
            <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">
              {session.decisionPrompt}
            </p>
            <p className="mt-2 break-words text-sm text-muted-foreground">
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
            继续追问
          </label>
          <Textarea
            className="mt-2 min-h-24 resize-y leading-6"
            disabled={isStreaming}
            id="follow-up-question"
            placeholder="基于刚才结论，我下一步该先问谁要资源？"
            value={followUpQuestion}
            onChange={(event) =>
              onFollowUpQuestionChange(event.currentTarget.value)
            }
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
      <RoundtableTimeline
        isStreaming={isStreaming}
        messages={session.transcript}
      />
    </div>
  );
}

export function RoundtableTimeline({
  isStreaming,
  messages,
}: {
  isStreaming: boolean;
  messages: RoundtableMessageView[];
}) {
  const firstMessageId = messages[0]?.id ?? "";
  return (
    <section className="min-w-0 overflow-hidden rounded-lg border bg-card p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-lg font-semibold text-foreground">讨论记录</h2>
        </div>
        <span
          className={cn(
            "inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium",
            isStreaming
              ? "bg-emerald-100 text-emerald-800"
              : "bg-muted text-muted-foreground",
          )}
        >
          <Radio
            className={cn("size-3.5", isStreaming ? "animate-pulse" : "")}
          />
          {isStreaming ? "讨论生成中" : `${messages.length} 条`}
        </span>
      </div>
      <TimelineMessageList
        isStreaming={isStreaming}
        key={firstMessageId}
        messages={messages}
      />
    </section>
  );
}

export function DecisionArtifacts({
  artifact,
}: {
  artifact: RoundtableArtifactView | null;
}) {
  const reasons = asStringArray(artifact?.reasonsJson);
  const debateMap = asDebateMap(artifact?.debateMapJson);

  if (!artifact) {
    return (
      <section className="rounded-lg border border-dashed bg-card p-8 text-center text-sm text-muted-foreground">
        结论将在圆桌流完成后显示。
      </section>
    );
  }

  return (
    <section className="min-w-0 overflow-hidden rounded-lg border bg-card p-5 shadow-sm">
      <h2 className="text-lg font-semibold text-foreground">结论</h2>
      <div className="mt-4 grid min-w-0 gap-4 lg:grid-cols-3">
        <ArtifactBlock icon={FileText} title="Memo" value={artifact.memo} />
        <ArtifactBlock
          icon={Target}
          title="Recommendation"
          value={artifact.recommendation}
        />
        <div className="min-w-0 rounded-lg border bg-background p-4">
          <h3 className="font-semibold text-foreground">理由</h3>
          <ul className="mt-2 space-y-2 text-sm text-muted-foreground">
            {reasons.map((reason) => (
              <li className="flex gap-2" key={reason}>
                <span className="mt-2 size-1.5 shrink-0 rounded-full bg-primary" />
                <span className="min-w-0 break-words">{reason}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <div className="mt-4 min-w-0 rounded-lg border bg-background p-4">
        <h3 className="inline-flex items-center gap-2 font-semibold text-foreground">
          <Map className="size-4 text-primary" />
          争论地图
        </h3>
        <div className="mt-3 grid min-w-0 gap-3 md:grid-cols-2">
          {debateMap.map((item) => (
            <div
              className="min-w-0 rounded-lg border bg-card p-3 text-sm"
              key={`${item.personaName}-${item.position}`}
            >
              <p className="break-words font-medium text-foreground">
                {item.personaName}
              </p>
              <p className="mt-1 break-words leading-6 text-muted-foreground">
                {item.position}
              </p>
              <p className="mt-1 break-words text-xs leading-5 text-muted-foreground">
                {item.keyConcern}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export function SessionList({
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
        {isLoading ? (
          <Loader2 className="size-4 animate-spin text-muted-foreground" />
        ) : null}
      </div>
      <div className="space-y-2">
        {sessions.map((item) => (
          <button
            className={cn(
              "w-full rounded-lg border p-3 text-left text-sm transition",
              activeSessionId === item.id
                ? "border-primary bg-primary/5"
                : "bg-background hover:bg-muted/40",
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
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              {item.id}
            </p>
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

export function SummaryPanel({
  activeStep,
  isStreaming,
  personas,
  session,
}: {
  activeStep: RoundtableStepId;
  isStreaming: boolean;
  personas: RoundtablePersonaView[];
  session: RoundtableSessionView | null;
}) {
  return (
    <section className="rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-center gap-2">
        <CheckCircle2 className="size-4 text-primary" />
        <h2 className="font-semibold text-foreground">Workspace summary</h2>
      </div>
      <dl className="mt-4 space-y-3 text-sm">
        <SummaryRow label="Step" value={STEP_COPY[activeStep].title} />
        <SummaryRow label="Status" value={session?.status ?? "idle"} />
        <SummaryRow label="Messages" value={session?.transcript.length ?? 0} />
        <SummaryRow label="Personas" value={personas.length} />
        <SummaryRow
          label="Billing"
          value={isStreaming ? "reserved" : "settled on complete"}
        />
      </dl>
    </section>
  );
}

function StatusMetric({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="min-w-0 border-r px-4 py-3 last:border-r-0">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-foreground">
        {value}
      </p>
    </div>
  );
}

function TimelineMessageList({
  isStreaming,
  messages,
}: {
  isStreaming: boolean;
  messages: RoundtableMessageView[];
}) {
  const [visibleCount, setVisibleCount] = useState(0);
  const effectiveVisibleCount = isStreaming ? visibleCount : messages.length;
  const visibleMessages = messages.slice(0, effectiveVisibleCount);

  useEffect(() => {
    if (!isStreaming || visibleCount >= messages.length) return undefined;

    const timer = window.setTimeout(
      () => {
        setVisibleCount((current) => Math.min(current + 1, messages.length));
      },
      visibleCount === 0 ? 120 : 360,
    );

    return () => window.clearTimeout(timer);
  }, [isStreaming, messages.length, visibleCount]);

  return (
    <div className="space-y-3">
      {visibleMessages.map((message, index) => (
        <TimelineMessageCard
          animationDelay={Math.min(index, 4) * 40}
          isStreaming={isStreaming}
          key={`${message.id}:${message.content}`}
          message={message}
        />
      ))}
      {isStreaming && visibleCount < messages.length ? (
        <div className="inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-800">
          <Radio className="size-3.5 animate-pulse" />
          正在加入讨论记录
        </div>
      ) : null}
      {isStreaming && visibleCount === messages.length ? (
        <div className="min-w-0 rounded-lg border border-dashed border-emerald-200 bg-emerald-50 p-4">
          <div className="inline-flex items-center gap-2 text-xs font-semibold text-emerald-800">
            <Radio className="size-3.5 animate-pulse" />
            等待下一条讨论记录
          </div>
        </div>
      ) : null}
      {!messages.length && !isStreaming ? (
        <div className="rounded-lg border border-dashed bg-muted/40 p-6 text-center text-sm text-muted-foreground">
          创建 session 后即可启动讨论时间线。
        </div>
      ) : null}
    </div>
  );
}

function TimelineMessageCard({
  animationDelay,
  isStreaming,
  message,
}: {
  animationDelay: number;
  isStreaming: boolean;
  message: RoundtableMessageView;
}) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const [revealedLength, setRevealedLength] = useState(0);
  const shouldType = isStreaming && !prefersReducedMotion;
  const isTyping = shouldType && revealedLength < message.content.length;
  const visibleContent = shouldType
    ? message.content.slice(0, revealedLength)
    : message.content;

  useEffect(() => {
    if (!shouldType || revealedLength >= message.content.length)
      return undefined;

    const charactersPerTick = getTypewriterStep(message.content.length);
    const timer = window.setTimeout(() => {
      setRevealedLength((current) =>
        Math.min(current + charactersPerTick, message.content.length),
      );
    }, 18);

    return () => window.clearTimeout(timer);
  }, [message.content.length, revealedLength, shouldType]);

  return (
    <article
      className="min-w-0 rounded-lg border bg-background p-4 shadow-sm"
      style={{ animationDelay: `${animationDelay}ms` }}
    >
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="rounded-full bg-muted px-2 py-1 font-medium text-foreground">
          {ROUND_LABELS[message.roundName] ?? message.roundName}
        </span>
        <span className="inline-flex min-w-0 items-center gap-1">
          <UserRound className="size-3.5 shrink-0" />
          {message.personaName ?? message.role}
        </span>
        <span>#{message.sequence}</span>
      </div>
      <p className="whitespace-pre-wrap break-words text-sm leading-6 text-foreground">
        {visibleContent}
        {isTyping ? (
          <span
            aria-hidden="true"
            className="ml-0.5 inline-block h-4 border-r border-muted-foreground align-[-0.125rem]"
          />
        ) : null}
      </p>
    </article>
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
    <div className="min-w-0 rounded-lg border bg-background p-4">
      <h3 className="inline-flex items-center gap-2 font-semibold text-foreground">
        <Icon className="size-4 text-primary" />
        {title}
      </h3>
      <p className="mt-2 break-words text-sm leading-6 text-muted-foreground">
        {value}
      </p>
    </div>
  );
}

function SummaryRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-center justify-between gap-4">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="truncate font-medium text-foreground">{value}</dd>
    </div>
  );
}

function getStepIcon(step: RoundtableStep) {
  if (step.isComplete) return Check;
  if (!step.isAvailable) return Lock;
  return Circle;
}

function getStepIndicator({
  index,
  isComplete,
  isLocked,
  StepIcon,
}: {
  index: number;
  isComplete: boolean;
  isLocked: boolean;
  StepIcon: typeof Check;
}) {
  if (isComplete) return <StepIcon className="size-4" />;
  if (isLocked) return <StepIcon className="size-3.5" />;
  return index + 1;
}

function getPersonaNames(personas: RoundtablePersonaView[]) {
  return (
    personas.map((persona) => persona.displayName).join("、") || "后端自动选择"
  );
}

function getTypewriterStep(contentLength: number): number {
  if (contentLength > 1800) return 12;
  if (contentLength > 900) return 8;
  if (contentLength > 400) return 5;
  return 3;
}

function usePrefersReducedMotion(): boolean {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const query = window.matchMedia("(prefers-reduced-motion: reduce)");
    setPrefersReducedMotion(query.matches);
    const handleChange = () => setPrefersReducedMotion(query.matches);
    query.addEventListener("change", handleChange);
    return () => query.removeEventListener("change", handleChange);
  }, []);

  return prefersReducedMotion;
}

function asStringArray(value: unknown): string[] {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

function asDebateMap(value: unknown) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const record = item as Record<string, unknown>;
      return {
        keyConcern: String(record.keyConcern ?? ""),
        personaName: String(record.personaName ?? ""),
        position: String(record.position ?? ""),
      };
    })
    .filter(
      (
        item,
      ): item is {
        keyConcern: string;
        personaName: string;
        position: string;
      } => Boolean(item),
    );
}
