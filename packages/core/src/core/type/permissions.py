"""跨层共享的权限类型定义。

这些类型被 core、domain 共同使用，放在 core 层避免循环依赖。
"""

from dataclasses import dataclass
from enum import StrEnum


class Action(StrEnum):
    """操作类型枚举。"""

    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    SHARE = "share"
    MANAGE = "manage"


class ResourceType(StrEnum):
    """资源类型枚举。各应用可扩展此枚举或在 domain 层定义具体类型。"""

    FOLDER = "folder"


@dataclass(frozen=True)
class ResourceContext:
    """资源上下文 - 适配 Casbin ABAC 反射。

    属性名使用 snake_case，与 matcher 中 r.obj.owner / r.obj.id 匹配。

    Attributes:
        id: 资源标识，格式 "resource_type:resource_id"
        owner: 资源所有者 username
    """

    id: str
    owner: str | None = None


class Roles:
    """系统角色常量定义。"""

    ADMIN = "admin"


ADMIN_ROLE = Roles.ADMIN


def normalize_roles(roles: list[str] | None) -> list[str]:
    """标准化角色列表为小写。"""
    return [role.lower() for role in (roles or [])]


def is_admin(roles: list[str] | None) -> bool:
    """检查用户是否拥有 admin 角色。"""
    normalized = [role.lower() for role in (roles or [])]
    return ADMIN_ROLE in normalized


def to_resource_type(value: ResourceType | str) -> ResourceType:
    """将输入标准化为 ResourceType 枚举。"""
    if isinstance(value, ResourceType):
        return value
    return ResourceType(value)


@dataclass
class ResourceFilterContext:
    """资源过滤上下文。

    Attributes:
        accessible_ids: 可访问的资源 ID 列表
            - None: Admin 用户，不过滤
            - []: 用户无任何权限
            - [...]: 用户可访问的 ID 列表
        is_admin: 是否为 Admin 用户
        username: 当前用户名
        user_roles: 用户角色列表
    """

    accessible_ids: list[str] | None
    is_admin: bool
    username: str
    user_roles: list[str]
