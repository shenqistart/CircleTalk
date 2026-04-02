"""用户数据访问层。"""

from core.repository.base_repository import BaseRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.model.user import User


class UserRepository(BaseRepository[User]):
    """用户实体 Repository，单例无状态。"""

    def __init__(self) -> None:
        super().__init__(User)

    def _get_searchable_fields(self) -> list[str]:
        return ["username", "display_name", "email", "phone"]

    async def get_by_username(self, session: AsyncSession, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
