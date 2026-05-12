"""DeepAgents boundary for first-version synchronous orchestration."""

from llm.roundtable.orchestrator import run_roundtable
from llm.roundtable.schema import RoundtablePersona, RoundtableResult


class DeepAgentsUnavailableError(RuntimeError):
    """Raised when DeepAgents cannot be imported or initialized."""


def deepagents_available() -> bool:
    try:
        __import__("deepagents")
    except Exception:
        return False
    return True


def run_with_deepagents_or_fallback(decision_prompt: str, personas: list[RoundtablePersona]) -> RoundtableResult:
    """Run a request-scoped roundtable; fallback keeps v1 functional without background jobs."""
    return run_roundtable(decision_prompt, personas)
