"""用户 ORM 模型。"""

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import AuditMixin, Base


class User(Base, AuditMixin):
    """Bedrock 平台用户实体。"""

    __tablename__ = "bedrock_user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
