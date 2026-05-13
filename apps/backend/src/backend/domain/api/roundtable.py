"""Roundtable decision advisor API."""

from collections.abc import AsyncIterator
from typing import Annotated

from core.database.session import db_session
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.error_handler import error_handler
from backend.domain.schema.roundtable_schema import (
    CreateRoundtableSessionRequest,
    CreateRoundtableSessionResponse,
    FollowUpRequest,
    RecommendPersonasRequest,
    RoundtableLanguage,
    RoundtablePersonaSchema,
    RoundtableSessionSchema,
    StreamSessionRequest,
)
from backend.domain.service.roundtable_service import RoundtableService

router = APIRouter(prefix="/roundtable", tags=["圆桌对话"])


@router.get("/personas")
@inject
@error_handler("查询圆桌人物")
async def list_personas(
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
    language: RoundtableLanguage = "zh",
) -> list[RoundtablePersonaSchema]:
    return await service.list_personas(session, language)


@router.post("/personas/recommend")
@inject
@error_handler("推荐圆桌人物")
async def recommend_personas(
    request: RecommendPersonasRequest,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> list[RoundtablePersonaSchema]:
    return await service.recommend(request.decision_prompt, request.language)


@router.post("/sessions")
@inject
@error_handler("创建圆桌会话")
async def create_session(
    request: CreateRoundtableSessionRequest,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CreateRoundtableSessionResponse:
    return await service.create_session(session, request)


@router.get("/sessions/{session_id}")
@inject
@error_handler("恢复圆桌会话")
async def get_session(
    session_id: str,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> RoundtableSessionSchema:
    try:
        return await service.get_session(session, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/sessions/{session_id}/stream")
@inject
async def stream_session(
    session_id: str,
    request: Request,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
    request_data: Annotated[StreamSessionRequest | None, Body()] = None,
) -> StreamingResponse:
    stream = service.stream_discussion(session, session_id, (request_data.language if request_data else "zh"))

    async def body() -> AsyncIterator[bytes]:
        try:
            async for chunk in stream:
                if await request.is_disconnected():
                    await service.mark_cancelled(session, session_id)
                    break
                yield chunk.encode("utf-8")
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    return StreamingResponse(body(), media_type="text/plain; charset=utf-8")


@router.post("/sessions/{session_id}/follow-up/stream")
@inject
async def stream_follow_up(
    session_id: str,
    request_data: FollowUpRequest,
    request: Request,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> StreamingResponse:
    stream = service.stream_follow_up(session, session_id, request_data.question, request_data.language)

    async def body() -> AsyncIterator[bytes]:
        async for chunk in stream:
            if await request.is_disconnected():
                await service.mark_cancelled(session, session_id)
                break
            yield chunk.encode("utf-8")

    return StreamingResponse(body(), media_type="text/plain; charset=utf-8")
