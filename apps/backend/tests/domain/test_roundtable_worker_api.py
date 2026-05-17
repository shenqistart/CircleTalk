from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.container import AppContainer
from backend.domain.api import roundtable_worker_router
from backend.domain.schema.roundtable_worker_schema import (
    RecommendPersonasResponseV1,
    WorkerCompletedEvent,
    WorkerPersona,
    WorkerStartedEvent,
    WorkerStatusResponseV1,
)


@pytest.fixture
def roundtable_service() -> MagicMock:
    service = MagicMock()
    service.list_worker_personas = AsyncMock(return_value=[])
    service.recommend_worker_personas = AsyncMock(
        return_value=RecommendPersonasResponseV1(request_id="req-1", personas=[])
    )
    service.worker_status = AsyncMock(
        return_value=WorkerStatusResponseV1(
            deepagents_available=False,
            deepagents_detail="not installed",
            deepagents_enabled=False,
        )
    )

    async def stream_discussion(_request):
        yield WorkerStartedEvent(request_id="req-1", session_id="s1", started_at=datetime.now(UTC))
        yield WorkerCompletedEvent(request_id="req-1", session_id="s1", usage={}, completed_at=datetime.now(UTC))

    service.stream_worker_discussion = MagicMock(side_effect=stream_discussion)
    return service


@pytest_asyncio.fixture
async def client(monkeypatch: pytest.MonkeyPatch, roundtable_service: MagicMock) -> AsyncClient:
    monkeypatch.setenv("AI_WORKER_SHARED_SECRET", "test-secret")
    test_app = FastAPI()
    test_app.include_router(roundtable_worker_router)
    container = AppContainer()
    container.roundtable_service.override(roundtable_service)
    container.wire(modules=["backend.domain.api.roundtable_worker"])
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    container.unwire()


@pytest.mark.asyncio
async def test_internal_worker_requires_shared_secret(client: AsyncClient) -> None:
    response = await client.get("/internal/roundtable/status")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_internal_worker_rejects_wrong_shared_secret(client: AsyncClient) -> None:
    response = await client.get("/internal/roundtable/status", headers={"X-AI-Worker-Secret": "wrong"})

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_internal_worker_status_accepts_bearer_secret(client: AsyncClient) -> None:
    response = await client.get("/internal/roundtable/status", headers={"Authorization": "Bearer test-secret"})

    assert response.status_code == 200
    assert response.json()["contractVersion"] == "roundtable.worker.v1"


@pytest.mark.asyncio
async def test_internal_worker_requires_all_supplied_secret_headers_to_match(client: AsyncClient) -> None:
    response = await client.get(
        "/internal/roundtable/status",
        headers={"Authorization": "Bearer test-secret", "X-AI-Worker-Secret": "wrong"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_recommend_rejects_invalid_contract_version(client: AsyncClient) -> None:
    response = await client.post(
        "/internal/roundtable/personas/recommend",
        headers={"X-AI-Worker-Secret": "test-secret"},
        json={"contractVersion": "roundtable.worker.v0", "requestId": "req-1", "decisionPrompt": "是否创业"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "invalid_contract_version"


@pytest.mark.asyncio
async def test_discussion_stream_returns_versioned_sse(client: AsyncClient) -> None:
    response = await client.post(
        "/internal/roundtable/discussions/stream",
        headers={"X-AI-Worker-Secret": "test-secret"},
        json={
            "contractVersion": "roundtable.worker.v1",
            "requestId": "req-1",
            "sessionId": "s1",
            "userIdHash": "u-hash",
            "decisionPrompt": "是否创业",
            "personas": [
                WorkerPersona(
                    id="socrates",
                    name="Socrates",
                    title="Philosopher",
                    description="Questions assumptions",
                    expertise=["ethics"],
                    language="en",
                ).model_dump(by_alias=True)
                | {"selectionSource": "manual", "sequence": 1}
            ],
        },
    )

    assert response.status_code == 200
    assert "event: roundtable.worker.v1.started" in response.text
    assert "event: roundtable.worker.v1.completed" in response.text
