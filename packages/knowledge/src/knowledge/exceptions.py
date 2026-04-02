"""Knowledge模块业务异常类体系

提供细粒度的异常类型，替代通用的Exception，
便于API层准确映射HTTP状态码和错误信息。
"""

from typing import Any

from core.exception.base import (
    BusinessError,
)
from core.exception.base import (
    FileParsingError as CoreFileParsingError,
)
from core.exception.base import (
    StorageError as CoreStorageError,
)


class KnowledgeError(BusinessError):
    """知识模块基础异常类，所有知识相关异常的父类。"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)


class KnowledgeNotFoundError(KnowledgeError):
    """知识未找到异常,对应HTTP 404。"""

    def __init__(self, knowledge_id: str, details: dict[str, Any] | None = None) -> None:
        message = f"知识未找到: {knowledge_id}"
        super().__init__(message, details)
        self.knowledge_id = knowledge_id


class KnowledgeAccessDeniedError(KnowledgeError):
    """知识访问权限不足异常,对应HTTP 403。"""

    def __init__(self, knowledge_id: str, username: str, details: dict[str, Any] | None = None) -> None:
        message = f"用户 {username} 无权访问知识 {knowledge_id}"
        super().__init__(message, details)
        self.knowledge_id = knowledge_id
        self.username = username


class FileParsingError(KnowledgeError, CoreFileParsingError):
    """文件解析失败异常，对应HTTP 400。"""

    def __init__(self, filename: str, reason: str, details: dict[str, Any] | None = None) -> None:
        message = f"文件解析失败 '{filename}': {reason}"
        KnowledgeError.__init__(self, message, details)
        self.filename = filename
        self.reason = reason


class ChunkingError(KnowledgeError):
    """知识分块失败异常,对应HTTP 500。"""

    def __init__(self, knowledge_id: str, reason: str, details: dict[str, Any] | None = None) -> None:
        message = f"知识分块失败 (知识ID: {knowledge_id}): {reason}"
        super().__init__(message, details)
        self.knowledge_id = knowledge_id
        self.reason = reason


class StorageError(KnowledgeError, CoreStorageError):
    """对象存储操作失败异常，对应HTTP 500。"""

    def __init__(
        self,
        operation: str,
        file_path: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"存储操作失败 ({operation}): {file_path} - {reason}"
        KnowledgeError.__init__(self, message, details)
        self.operation = operation
        self.file_path = file_path
        self.reason = reason


class VectorSearchError(KnowledgeError):
    """向量检索失败异常，对应HTTP 500。"""

    def __init__(self, query: str, reason: str, details: dict[str, Any] | None = None) -> None:
        message = f"向量检索失败 (查询: '{query}'): {reason}"
        super().__init__(message, details)
        self.query = query
        self.reason = reason


class KnowledgeMetadataError(KnowledgeError):
    """知识元数据操作失败异常,对应HTTP 400。"""

    def __init__(
        self,
        knowledge_id: str,
        field: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"知识元数据操作失败 (知识ID: {knowledge_id}, 字段: {field}): {reason}"
        super().__init__(message, details)
        self.knowledge_id = knowledge_id
        self.field = field
        self.reason = reason


class VersionManagementError(KnowledgeError):
    """版本管理操作失败异常,对应HTTP 400或500。"""

    def __init__(
        self,
        knowledge_id: str,
        operation: str,
        reason: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        message = f"版本管理操作失败 (知识ID: {knowledge_id}, 操作: {operation}): {reason}"
        super().__init__(message, details)
        self.knowledge_id = knowledge_id
        self.operation = operation
        self.reason = reason
