"""Request context providing tenant, user, and role information via contextvars."""

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class RequestContextParams:
    """Parameters for setting request context."""

    tenant: str
    username: str
    roles: list[str] = field(default_factory=list)
    request_id: str = ""


@dataclass
class RequestContext:
    """Immutable request context accessible throughout the request lifecycle."""

    tenant: str
    username: str
    roles: list[str]
    request_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant": self.tenant,
            "username": self.username,
            "roles": self.roles,
            "request_id": self.request_id,
        }


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "_request_context", default=None
)


def set_request_context(params: RequestContextParams) -> None:
    ctx = RequestContext(
        tenant=params.tenant,
        username=params.username,
        roles=params.roles,
        request_id=params.request_id,
    )
    _request_context.set(ctx)


def get_request_context() -> RequestContext:
    ctx = _request_context.get()
    if ctx is None:
        msg = "Request context not set. Are you inside an HTTP request?"
        raise RuntimeError(msg)
    return ctx


def try_current_tenant() -> str | None:
    ctx = _request_context.get()
    return ctx.tenant if ctx else None


def current_tenant() -> str:
    return get_request_context().tenant


def current_username() -> str:
    return get_request_context().username


def current_user_roles() -> list[str]:
    return get_request_context().roles


def clear_request_context() -> None:
    _request_context.set(None)
