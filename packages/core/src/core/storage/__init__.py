"""Object storage infrastructure."""

from core.storage.manager import StorageServiceRegistry, initialize_storage, storage_service

__all__ = ["StorageServiceRegistry", "initialize_storage", "storage_service"]
