"""用户域测试夹具。"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.user.repository.user_repository import UserRepository
from backend.domain.user.service.user_service import UserService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_user_repository() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repository: MagicMock) -> UserService:
    return UserService(repository=mock_user_repository)
