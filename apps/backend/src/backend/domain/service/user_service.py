"""用户业务逻辑层。"""

import uuid

from core.context.request import current_username
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.repository.user_repository import UserRepository
from backend.domain.schema.user_schema import UserCreate, UserSchema, UserUpdate


class UserService:
    """编排用户操作，依赖通过构造函数注入。"""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(self, session: AsyncSession, data: UserCreate) -> UserSchema:
        existing = await self._repository.get_by_username(session, data.username)
        if existing is not None:
            msg = f"用户名 '{data.username}' 已存在"
            raise ValueError(msg)

        user_data = {
            "id": str(uuid.uuid4()),
            "username": data.username,
            "display_name": data.display_name,
            "email": data.email,
            "phone": data.phone,
            "roles": data.roles,
            "status": "active",
            "created_by": current_username(),
            "updated_by": current_username(),
        }
        user = await self._repository.create(session, user_data)
        return UserSchema.model_validate(user)

    async def get_user(self, session: AsyncSession, user_id: str) -> UserSchema | None:
        user = await self._repository.get_by_id(session, user_id)
        if user is None:
            return None
        return UserSchema.model_validate(user)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str,
        data: UserUpdate,
    ) -> UserSchema | None:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = current_username()
        user = await self._repository.update(session, user_id, update_data)
        if user is None:
            return None
        return UserSchema.model_validate(user)

    async def delete_user(self, session: AsyncSession, user_id: str) -> bool:
        return await self._repository.delete(session, user_id)

    async def search_users(
        self,
        session: AsyncSession,
        keyword: str | None = None,
        status: str | None = None,
        role: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[UserSchema], int]:
        filters: dict[str, str] = {}
        if status:
            filters["status"] = status
        # 角色筛选需要 ARRAY contains 查询，暂留待后续实现
        _ = role

        users, total = await self._repository.search_paged(
            session,
            page=page,
            size=size,
            query=keyword,
            **filters,
        )
        schemas = [UserSchema.model_validate(u) for u in users]
        return schemas, total

    async def toggle_status(self, session: AsyncSession, user_id: str) -> UserSchema | None:
        user = await self._repository.get_by_id(session, user_id)
        if user is None:
            return None
        new_status = "disabled" if user.status == "active" else "active"
        updated = await self._repository.update(
            session,
            user_id,
            {"status": new_status, "updated_by": current_username()},
        )
        if updated is None:
            return None
        return UserSchema.model_validate(updated)
