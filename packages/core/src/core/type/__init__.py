"""核心领域模型中使用的通用类型和枚举。"""

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel

from .common import Args, JSONDict, JSONPrimitive, JSONValue, Kwargs, StrObjectDict


class SchemaType(StrEnum):
    """
    用于 Pydantic 模型中 `schema_type` 字段的枚举，
    作为判别联合体 (Discriminated Union)，确保数据在序列化和反序列化过程中的类型安全。
    """

    ENTITY = "entity"
    TOOL_DEFINITION = "tool_definition"
    SKILL = "skill"
    FILTER = "filter"
    TIME = "time"
    PROMPT_TEMPLATE = "prompt_template"
    KNOWLEDGE_BASE = "knowledge_base"
    KNOWLEDGE_DOCUMENT = "knowledge_document"
    KNOWLEDGE_CHUNK = "knowledge_chunk"
    KNOWLEDGE_FOLDER = "knowledge_folder"
    KNOWLEDGE_SECTION = "knowledge_section"
    EVALUATION_SUITE = "evaluation_suite"
    EVALUATION_RESULT = "evaluation_result"
    INTENT = "intent"
    COMPONENT = "component"


class TitleMixin(BaseModel):
    """为 Pydantic 模型添加统一的 title 属性。"""

    @property
    def title(self) -> str:
        msg = "子类必须实现此属性"
        raise NotImplementedError(msg)


class DescribableSchema(BaseModel, ABC):
    """抽象基类，定义需要向 LLM 提供丰富描述的 Schema 契约。"""

    @abstractmethod
    def to_llm_description_string(self) -> str:
        """返回为 LLM 选择优化的、包含丰富上下文的描述字符串。"""


__all__ = [
    "Args",
    "DescribableSchema",
    "JSONDict",
    "JSONPrimitive",
    "JSONValue",
    "Kwargs",
    "SchemaType",
    "StrObjectDict",
    "TitleMixin",
]
