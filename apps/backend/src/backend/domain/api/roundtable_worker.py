"""Internal Roundtable worker API for Wasp server-to-server calls."""

import os
from collections.abc import AsyncIterator
from hmac import compare_digest
from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.domain.schema.roundtable_schema import RoundtableLanguage
from backend.domain.schema.roundtable_worker_schema import (
    WORKER_CONTRACT_VERSION,
    FollowUpRequestV1,
    RecommendPersonasRequestV1,
    RecommendPersonasResponseV1,
    StartDiscussionRequestV1,
    WorkerErrorV1,
    WorkerPersona,
    WorkerStatusResponseV1,
)
from backend.domain.service.roundtable_service import RoundtableService

WORKER_SECRET_ENV = "AI_WORKER_SHARED_SECRET"  # noqa: S105
WORKER_SECRET_HEADER = "X-AI-Worker-Secret"  # noqa: S105
DEEPAGENTS_ENABLED_ENV = "ENABLE_DEEPAGENTS_ROUNDTABLE"


async def require_worker_secret(request: Request) -> None:
    expected = os.getenv(WORKER_SECRET_ENV, "")
    provided = request.headers.get(WORKER_SECRET_HEADER, "")
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        provided = authorization.removeprefix("Bearer ").strip()
    if not expected or not provided or not compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="Invalid worker secret.")


router = APIRouter(
    prefix="/internal/roundtable",
    tags=["Internal Roundtable Worker"],
    dependencies=[Depends(require_worker_secret)],
)


@router.get("/personas")
@inject
async def list_worker_personas(
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    language: RoundtableLanguage = "zh",
) -> list[WorkerPersona]:
    return await service.list_worker_personas(language)


@router.post("/personas/recommend")
@inject
async def recommend_worker_personas(
    request: RecommendPersonasRequestV1,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> RecommendPersonasResponseV1:
    _ensure_contract(request.contract_version, request.request_id)
    return await service.recommend_worker_personas(
        request.request_id,
        request.decision_prompt,
        request.language,
        request.max_personas,
    )


@router.post("/discussions/stream")
@inject
async def stream_worker_discussion(
    request: StartDiscussionRequestV1,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> StreamingResponse:
    _ensure_contract(request.contract_version, request.request_id)
    return StreamingResponse(
        _sse_body(service.stream_worker_discussion(request)),
        media_type="text/event-stream",
    )


@router.post("/follow-up/stream")
@inject
async def stream_worker_follow_up(
    request: FollowUpRequestV1,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> StreamingResponse:
    _ensure_contract(request.contract_version, request.request_id)
    return StreamingResponse(
        _sse_body(service.stream_worker_follow_up(request)),
        media_type="text/event-stream",
    )


@router.get("/status")
@inject
async def worker_status(
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> WorkerStatusResponseV1:
    return await service.worker_status(deepagents_enabled=_is_true(os.getenv(DEEPAGENTS_ENABLED_ENV)))


async def _sse_body(events: AsyncIterator[Any]) -> AsyncIterator[bytes]:
    async for event in events:
        yield f"event: {event.event_type}\ndata: {event.model_dump_json(by_alias=True)}\n\n".encode()


def _ensure_contract(contract_version: str, request_id: str) -> None:
    if contract_version == WORKER_CONTRACT_VERSION:
        return
    error = WorkerErrorV1(
        request_id=request_id,
        code="invalid_contract_version",
        message=f"Unsupported contractVersion: {contract_version}",
        retryable=False,
        details={"expected": WORKER_CONTRACT_VERSION, "received": contract_version},
    )
    raise HTTPException(status_code=400, detail=error.model_dump(by_alias=True))


def _is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}
