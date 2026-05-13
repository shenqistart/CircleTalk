"""SQLAlchemy DeclarativeBase and common mixins."""

from sqlalchemy.orm import DeclarativeBase

from core.model.audit_mixin import AuditMixin

__all__ = ["AuditMixin", "Base"]


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    def __init__(self, **kwargs: object) -> None:
        valid_attrs = set(self.__mapper__.attrs.keys())
        for key, value in kwargs.items():
            if key in valid_attrs:
                setattr(self, key, value)

    def to_dict(self) -> dict[str, object]:
        """Convert model instance to dictionary, excluding embedding fields."""
        return {
            c.key: getattr(self, c.key)
            for c in self.__table__.columns
            if not c.key.endswith("_embedding")
        }
