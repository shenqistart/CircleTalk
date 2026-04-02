"""FTS（全文搜索）Mixin，为SQLAlchemy模型提供自动化的FTS文档生成功能。"""

from typing import TypeVar

from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, Mapper, mapped_column
from sqlalchemy_utils import TSVectorType

from core.utils.text import tokenize_for_fts

FTSModel = TypeVar("FTSModel", bound="FTSMixin")


class FTSMixin:
    """
    一个为 SQLAlchemy 模型提供自动全文搜索（FTS）文档更新功能的 Mixin。

    要使用此 Mixin，子类模型需要：
    1. 在类定义中继承 FTSMixin。
    2. 实现 `_get_fts_text()` 实例方法，该方法应返回一个用于全文搜索的、
       由模型各字段内容拼接而成的原始字符串。
    """

    @declared_attr
    def fts_document(cls) -> Mapped[str]:
        """
        定义 fts_document 列，用于存储全文搜索的 tsvector 数据。
        `declared_attr` 确保每个子类都会创建自己的列实例。
        """
        return mapped_column(TSVectorType())

    def _get_fts_text(self) -> str:
        """
        获取用于全文搜索的原始文本。

        子类必须重写此方法，根据自身的字段和权重逻辑，
        返回一个拼接好的字符串。
        """
        msg = "继承 FTSMixin 的子类必须实现 _get_fts_text 方法。"
        raise NotImplementedError(msg)

    @staticmethod
    def _update_fts_document(_mapper: Mapper[FTSModel], _connection: Connection, target: FTSModel) -> None:
        """
        SQLAlchemy 事件监听器回调函数。

        在模型实例被插入或更新到数据库之前，此函数会被调用，
        自动生成并填充 `fts_document` 字段。
        """
        raw_text = target._get_fts_text()
        target.fts_document = tokenize_for_fts(raw_text)

    @classmethod
    def __declare_last__(cls) -> None:
        """
        在所有模型类完成映射后，为其附加 SQLAlchemy 事件监听器。

        `__declare_last__` 是一个特殊的钩子，确保监听器只被附加到
        具体的、继承了 FTSMixin 的子类上，而不是 Mixin 本身。
        """
        event.listen(cls, "before_insert", cls._update_fts_document)
        event.listen(cls, "before_update", cls._update_fts_document)
