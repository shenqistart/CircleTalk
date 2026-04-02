"""通用异常基类定义。"""

from typing import Any


class BusinessError(Exception):
    """业务异常基类。"""


class PermissionDeniedError(BusinessError):
    """权限不足。"""


class ResourceNotFoundError(BusinessError):
    """资源不存在。"""


class ResourceAlreadyExistsError(BusinessError):
    """资源已存在。"""


class FileParsingError(BusinessError):
    """文件解析失败异常。"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)


class StorageError(BusinessError):
    """存储操作失败异常。"""

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        self.message = message
        self.details: dict[str, Any] = details or {}
        super().__init__(self.message)
