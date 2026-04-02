"""用户 API 端点集成测试（使用 httpx）。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from backend.container import AppContainer
from backend.domain.user.api import user_router
from backend.domain.user.schema.user_schema import UserSchema
from core.database.session import db_session


@pytest.fixture
def mock_user_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def mock_session() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
async def client(mock_user_service: MagicMock, mock_session: AsyncMock):
    """创建不带生命周期的测试应用（无需真实数据库）。"""
    test_app = FastAPI()

    # 覆盖 db_session 依赖，返回 mock 对象
    async def override_db_session():
        yield mock_session

    test_app.dependency_overrides[db_session] = override_db_session
    test_app.include_router(user_router, prefix="/api")

    @test_app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "bedrock"}

    container = AppContainer()
    container.user_service.override(mock_user_service)
    container.wire(modules=["backend.domain.user.api.user"])

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    container.unwire()


@pytest.mark.asyncio
async def test_search_users(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.search_users = AsyncMock(return_value=([], 0))

    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["content"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.create_user = AsyncMock(
        return_value=UserSchema(
            id="test-id",
            username="newuser",
            display_name="New User",
            status="active",
            roles=["user"],
        )
    )

    response = await client.post(
        "/api/users",
        json={"username": "newuser", "display_name": "New User", "roles": ["user"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.get_user = AsyncMock(return_value=None)

    response = await client.get("/api/users/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
