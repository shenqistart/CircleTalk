"""用户管理 REST API 端点。"""

from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.error_handler import error_handler
from backend.common.pagination import PageParams
from backend.common.response import (
    CommonResponse,
    not_found_response,
    pageable_success_response,
    success_response,
)
from backend.domain.user.schema.user_schema import UserCreate, UserUpdate
from backend.domain.user.service.user_service import UserService
from core.database.session import db_session

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
@inject
@error_handler("查询用户")
async def search_users(
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
    pagination: Annotated[PageParams, Depends()],
    keyword: str | None = Query(None, description="搜索关键词"),
    status: str | None = Query(None, description="按状态筛选"),
    role: str | None = Query(None, description="按角色筛选"),
) -> CommonResponse[Any]:
    users, total = await user_service.search_users(
        session,
        keyword=keyword,
        status=status,
        role=role,
        page=pagination.page,
        size=pagination.size,
    )
    return pageable_success_response(
        content=[u.model_dump() for u in users],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.post("")
@inject
@error_handler("创建用户")
async def create_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.create_user(session, user_data)
    return success_response(user.model_dump())


@router.get("/{user_id}")
@inject
@error_handler("获取用户")
async def get_user(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.get_user(session, user_id)
    if user is None:
        return not_found_response("用户不存在")
    return success_response(user.model_dump())


@router.put("/{user_id}")
@inject
@error_handler("更新用户")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.update_user(session, user_id, user_data)
    if user is None:
        return not_found_response("用户不存在")
    return success_response(user.model_dump())


@router.delete("/{user_id}")
@inject
@error_handler("删除用户")
async def delete_user(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    deleted = await user_service.delete_user(session, user_id)
    if not deleted:
        return not_found_response("用户不存在")
    return success_response(message="用户已删除")


@router.put("/{user_id}/status")
@inject
@error_handler("切换用户状态")
async def toggle_user_status(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.toggle_status(session, user_id)
    if user is None:
        return not_found_response("用户不存在")
    return success_response(user.model_dump())
