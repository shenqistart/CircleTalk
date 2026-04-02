"""审计字段 Mixin，为 SQLAlchemy 模型提供统一的审计追踪字段。"""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """
    时间戳 Mixin，仅提供创建/更新时间。

    适用场景：
    - 不需要追踪操作人的模型（如 UserProfile）
    - 仅需时间戳的辅助模型
    """

    @declared_attr
    def created_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            server_default=func.now(),
            nullable=False,
            comment="创建时间",
        )

    @declared_attr
    def updated_at(cls) -> Mapped[datetime]:
        return mapped_column(
            DateTime,
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
            comment="更新时间",
        )


class AuditMixin(TimestampMixin):
    """
    完整审计 Mixin，包含时间戳和操作人字段。

    继承 TimestampMixin，额外提供 created_by / updated_by 字段。

    适用场景：
    - 主要业务模型（Skill, Intent, Component 等）
    - 需要追踪操作人的关联表
    """

    @declared_attr
    def created_by(cls) -> Mapped[str | None]:
        return mapped_column(
            String(100),
            comment="创建人",
        )

    @declared_attr
    def updated_by(cls) -> Mapped[str | None]:
        return mapped_column(
            String(100),
            comment="更新人",
        )
