"""共享异常定义。"""

from .base import (
    BusinessError,
    FileParsingError,
    PermissionDeniedError,
    ResourceAlreadyExistsError,
    ResourceNotFoundError,
    StorageError,
)
from .business import BusinessError as BusinessLayerError

__all__ = [
    "BusinessError",
    "BusinessLayerError",
    "FileParsingError",
    "PermissionDeniedError",
    "ResourceAlreadyExistsError",
    "ResourceNotFoundError",
    "StorageError",
]
