"""Storage service singleton registry."""

import logging
from typing import Any, ClassVar, Protocol

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    """Storage service interface."""

    async def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream", metadata: dict[str, str] | None = None) -> str: ...
    async def download_file(self, file_path: str) -> bytes: ...
    async def delete_file(self, file_path: str) -> None: ...
    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str: ...
    async def file_exists(self, file_path: str) -> bool: ...


class StorageServiceRegistry:
    """Storage service singleton registry."""

    _instance: ClassVar[StorageService | None] = None

    @classmethod
    async def initialize(cls, config: dict[str, Any]) -> None:
        backend = config.get("backend", "minio")
        if backend == "minio":
            from core.storage.minio_storage import MinIOStorage

            cls._instance = MinIOStorage(config)
            await cls._instance.ensure_bucket()  # type: ignore[attr-defined]
        else:
            msg = f"Unsupported storage backend: {backend}"
            raise NotImplementedError(msg)
        logger.info("Storage service initialized: %s", backend)

    @classmethod
    def get(cls) -> StorageService:
        if cls._instance is None:
            msg = "Storage service not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return cls._instance


async def initialize_storage(config: dict[str, Any]) -> None:
    await StorageServiceRegistry.initialize(config)


def storage_service() -> StorageService:
    return StorageServiceRegistry.get()
