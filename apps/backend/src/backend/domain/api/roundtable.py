"""Roundtable REST and text stream endpoints."""

from typing import Annotated

from core.database.session import db_session
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.error_handler import error_handler
from backend.domain.schema.roundtable_schema import (
    CreateRoundtableSessionRequest,
    CreateRoundtableSessionResponse,
    FollowUpRequest,
    RecommendPersonasRequest,
    RoundtablePersonaSchema,
    RoundtableSessionSchema,
)
from backend.domain.service.roundtable_service import RoundtableService

router = APIRouter(prefix="/roundtable", tags=["圆桌对话"])


@router.get("/personas")
@inject
@error_handler("查询圆桌人物")
async def list_personas(
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> list[RoundtablePersonaSchema]:
    return [
        RoundtablePersonaSchema(
            id=persona.id,
            display_name=persona.display_name,
            skill_name=persona.skill_name,
            summary=persona.summary,
            selection_reason=persona.selection_reason,
        )
        for persona in service.personas()
    ]


@router.post("/personas/recommend")
@inject
@error_handler("推荐圆桌人物")
async def recommend_persona_list(
    request: RecommendPersonasRequest,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
) -> list[RoundtablePersonaSchema]:
    return [service._persona_schema(persona) for persona in service.recommend(request.decision_prompt)]


@router.post("/sessions")
@inject
@error_handler("创建圆桌会话")
async def create_session(
    request: CreateRoundtableSessionRequest,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CreateRoundtableSessionResponse:
    return await service.create_session(session, request.decision_prompt, request.persona_ids)


@router.get("/sessions/{session_id}")
@inject
@error_handler("恢复圆桌会话")
async def get_session(
    session_id: str,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> RoundtableSessionSchema:
    restored = await service.get_session(session, session_id)
    if restored is None:
        raise HTTPException(status_code=404, detail="roundtable session not found")
    return restored


@router.post("/sessions/{session_id}/stream")
@inject
async def stream_session(
    session_id: str,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> StreamingResponse:
    return StreamingResponse(service.stream_session(session, session_id), media_type="text/plain; charset=utf-8")


@router.post("/sessions/{session_id}/follow-up/stream")
@inject
async def stream_follow_up(
    session_id: str,
    request: FollowUpRequest,
    service: Annotated[RoundtableService, Depends(Provide["roundtable_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> StreamingResponse:
    return StreamingResponse(service.follow_up(session, session_id, request.question), media_type="text/plain; charset=utf-8")
