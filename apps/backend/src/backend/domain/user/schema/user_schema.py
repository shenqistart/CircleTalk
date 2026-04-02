"""用户 Pydantic Schema，用于请求/响应校验。"""

from datetime import datetime

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    """完整的用户响应 DTO。"""

    id: str
    username: str
    display_name: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: str
    roles: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """用户创建请求。"""

    username: str = Field(min_length=2, max_length=100)
    display_name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    roles: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """用户更新请求（所有字段均可选）。"""

    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    roles: list[str] | None = None


class UserQuery(BaseModel):
    """用户搜索/筛选参数。"""

    keyword: str | None = None
    status: str | None = None
    role: str | None = None
