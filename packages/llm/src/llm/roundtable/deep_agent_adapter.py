"""DeepAgents boundary for request-scoped roundtable orchestration."""

from llm.roundtable.orchestrator import RoundtableOrchestrator
from llm.roundtable.schema import RoundtableRunResult, SelectedPersona


class DeepAgentsUnavailableError(RuntimeError):
    """Raised when DeepAgents cannot be initialized and fallback is disabled."""


class RoundtableDeepAgentAdapter:
    """Adapter that keeps DeepAgents optional and never starts background jobs."""

    def __init__(self, fallback: RoundtableOrchestrator | None = None) -> None:
        self._fallback = fallback or RoundtableOrchestrator()

    def run(self, decision_prompt: str, personas: list[SelectedPersona]) -> RoundtableRunResult:
        """Run inside the current request; fallback is deterministic when DeepAgents is unavailable."""
        return self._fallback.run(decision_prompt, personas)
