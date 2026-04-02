"""UI 配置 Mixin，为 SQLAlchemy 模型提供统一的 UI 展示字段。"""

from sqlalchemy import String
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column


class UIConfigMixin:
    """
    UI 配置 Mixin，提供图标和颜色字段。

    用于在前端展示时提供统一的视觉配置：
    - icon: lucide-react 图标库的图标名称
    - color: 十六进制颜色值（如 #3B82F6）
    """

    @declared_attr
    def icon(cls) -> Mapped[str | None]:
        return mapped_column(
            String(50),
            comment="图标名称（lucide-react 图标库）",
        )

    @declared_attr
    def color(cls) -> Mapped[str | None]:
        return mapped_column(
            String(20),
            comment="颜色值（十六进制，如 #3B82F6）",
        )
