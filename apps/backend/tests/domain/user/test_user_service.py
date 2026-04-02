"""UserService 单元测试。"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.domain.user.schema.user_schema import UserCreate
from backend.domain.user.service.user_service import UserService


@pytest.mark.asyncio
async def test_create_user_success(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_username = AsyncMock(return_value=None)

    mock_user = MagicMock()
    mock_user.id = "test-uuid"
    mock_user.username = "johndoe"
    mock_user.display_name = "John Doe"
    mock_user.email = "john@example.com"
    mock_user.phone = None
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.roles = ["user"]
    mock_user.last_login_at = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.created_by = "admin"
    mock_user.updated_by = "admin"
    mock_user_repository.create = AsyncMock(return_value=mock_user)

    with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
        result = await user_service.create_user(
            mock_session,
            UserCreate(username="johndoe", display_name="John Doe", email="john@example.com", roles=["user"]),
        )

    assert result.username == "johndoe"
    assert result.display_name == "John Doe"
    mock_user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_username(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_username = AsyncMock(return_value=MagicMock())

    with pytest.raises(ValueError, match="already exists"):
        with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
            await user_service.create_user(
                mock_session,
                UserCreate(username="existing", display_name="Existing User"),
            )


@pytest.mark.asyncio
async def test_get_user_found(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user = MagicMock()
    mock_user.id = "user-1"
    mock_user.username = "johndoe"
    mock_user.display_name = "John Doe"
    mock_user.email = None
    mock_user.phone = None
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.roles = []
    mock_user.last_login_at = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.created_by = None
    mock_user.updated_by = None
    mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)

    result = await user_service.get_user(mock_session, "user-1")
    assert result is not None
    assert result.username == "johndoe"


@pytest.mark.asyncio
async def test_get_user_not_found(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_id = AsyncMock(return_value=None)
    result = await user_service.get_user(mock_session, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_toggle_status(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user = MagicMock()
    mock_user.status = "active"
    mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)

    toggled_user = MagicMock()
    toggled_user.id = "user-1"
    toggled_user.username = "johndoe"
    toggled_user.display_name = "John"
    toggled_user.email = None
    toggled_user.phone = None
    toggled_user.avatar = None
    toggled_user.status = "disabled"
    toggled_user.roles = []
    toggled_user.last_login_at = None
    toggled_user.created_at = None
    toggled_user.updated_at = None
    toggled_user.created_by = None
    toggled_user.updated_by = None
    mock_user_repository.update = AsyncMock(return_value=toggled_user)

    with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
        result = await user_service.toggle_status(mock_session, "user-1")

    assert result is not None
    assert result.status == "disabled"
    mock_user_repository.update.assert_called_once()
