"""DeepAgents adapter boundary for first-version roundtable orchestration."""

from dataclasses import dataclass

from llm.roundtable.orchestrator import RoundtableOrchestrator
from llm.roundtable.schema import RoundtableLanguage, RoundtableResult, SelectedPersona


@dataclass(frozen=True)
class DeepAgentStatus:
    """DeepAgents availability status."""

    available: bool
    detail: str


def deepagents_status() -> DeepAgentStatus:
    """Return whether deepagents can be imported without making backend own it."""
    try:
        import deepagents  # type: ignore[import-not-found]  # noqa: F401, PLC0415
    except Exception as exc:  # pragma: no cover - environment dependent
        return DeepAgentStatus(available=False, detail=str(exc))
    return DeepAgentStatus(available=True, detail="deepagents import ok")


class DeepAgentRoundtableAdapter:
    """Adapter that keeps DeepAgents request-scoped and falls back deterministically."""

    def __init__(self, fallback: RoundtableOrchestrator | None = None) -> None:
        self._fallback = fallback or RoundtableOrchestrator()

    def run(
        self, decision_prompt: str, personas: list[SelectedPersona], language: RoundtableLanguage | str | None = None
    ) -> RoundtableResult:
        """Run inside the current request; fallback is deterministic when DeepAgents is unavailable."""
        return self._fallback.run(decision_prompt, personas, language)


RoundtableDeepAgentAdapter = DeepAgentRoundtableAdapter
