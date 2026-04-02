"""Schema 基础类和 Mixin，提供通用的 Pydantic Schema 组件。"""

from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, PlainSerializer


def datetime_to_str(value: datetime | str | None) -> str | None:
    """将 datetime 对象序列化为 ISO 格式字符串。"""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value


# 通用的日期时间字段类型，自动序列化为 ISO 格式字符串
DateTimeStr = Annotated[
    datetime | str | None,
    PlainSerializer(datetime_to_str, return_type=str, when_used="json"),
]


class AuditSchemaMixin(BaseModel):
    """
    审计字段 Schema Mixin。

    提供统一的审计追踪字段：
    - created_at: 创建时间
    - updated_at: 更新时间
    - created_by: 创建人
    - updated_by: 更新人
    """

    created_at: DateTimeStr = None
    updated_at: DateTimeStr = None
    created_by: str | None = None
    updated_by: str | None = None


class MetadataSchemaMixin(BaseModel):
    """
    元数据通用字段 Mixin。

    提供元数据模型的常用字段：
    - keywords: 关键词列表（用于向量检索）
    - examples: 示例查询
    - tags: 标签列表
    - icon: 图标名称（lucide-react）
    - color: 颜色值（十六进制）
    """

    keywords: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    icon: str | None = None
    color: str | None = None


class UIConfigSchemaMixin(BaseModel):
    """
    UI 配置 Schema Mixin。

    仅提供 icon 和 color 字段，用于不需要 keywords/examples/tags 的场景。
    """

    icon: str | None = None
    color: str | None = None
