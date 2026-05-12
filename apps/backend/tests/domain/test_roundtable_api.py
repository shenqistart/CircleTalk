from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from core.database.session import db_session
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.container import AppContainer
from backend.domain.api import roundtable_router
from backend.domain.schema.roundtable_schema import CreateRoundtableSessionResponse, RoundtableSessionSchema


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    test_app = FastAPI()

    async def override_db_session():
        yield AsyncMock()

    test_app.dependency_overrides[db_session] = override_db_session
    test_app.include_router(roundtable_router, prefix="/api")
    container = AppContainer()
    service = MagicMock()
    service.personas.return_value = []
    service.recommend.return_value = []
    now = "2026-05-12T00:00:00Z"
    session = RoundtableSessionSchema(
        id="s1",
        decision_prompt="是否创业",
        status="ready",
        selected_personas=[],
        transcript=[],
        artifacts=None,
        created_at=now,
        updated_at=now,
    )
    service.create_session = AsyncMock(
        return_value=CreateRoundtableSessionResponse(session=session, recommended_personas=[])
    )
    service.get_session = AsyncMock(return_value=session)
    container.roundtable_service.override(service)
    container.wire(modules=["backend.domain.api.roundtable"])
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    container.unwire()


@pytest.mark.asyncio
async def test_create_roundtable_session_manual_selection(client: AsyncClient) -> None:
    response = await client.post(
        "/api/roundtable/sessions", json={"decisionPrompt": "是否创业", "personaIds": ["socrates"]}
    )
    assert response.status_code == 200
    assert response.json()["session"]["id"] == "s1"


@pytest.mark.asyncio
async def test_get_roundtable_session_restore(client: AsyncClient) -> None:
    response = await client.get("/api/roundtable/sessions/s1")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
