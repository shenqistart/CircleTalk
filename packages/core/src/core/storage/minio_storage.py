"""MinIO/S3-compatible object storage implementation."""

import io
import logging
from typing import Any

from minio import Minio

logger = logging.getLogger(__name__)


class MinIOStorage:
    """MinIO storage service implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._bucket = config.get("bucket", "bedrock")
        secure = config.get("secure", False)
        self.client = Minio(
            endpoint=config.get("endpoint", "localhost:9000"),
            access_key=config.get("access_key", "minioadmin"),
            secret_key=config.get("secret_key", "minioadmin"),
            secure=secure,
        )

    async def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self._bucket):
            self.client.make_bucket(self._bucket)
            logger.info("Created bucket: %s", self._bucket)

    async def upload_file(
        self,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        data = io.BytesIO(file_content)
        self.client.put_object(
            self._bucket,
            file_path,
            data,
            length=len(file_content),
            content_type=content_type,
            metadata=metadata,
        )
        return file_path

    async def download_file(self, file_path: str) -> bytes:
        response = self.client.get_object(self._bucket, file_path)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete_file(self, file_path: str) -> None:
        self.client.remove_object(self._bucket, file_path)

    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        from datetime import timedelta

        return self.client.presigned_get_object(
            self._bucket,
            file_path,
            expires=timedelta(seconds=expires_in),
        )

    async def file_exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self._bucket, file_path)
            return True
        except Exception:
            return False

    async def get_file_metadata(self, file_path: str) -> dict[str, Any]:
        stat = self.client.stat_object(self._bucket, file_path)
        return {
            "size": stat.size,
            "etag": stat.etag,
            "content_type": stat.content_type,
            "last_modified": stat.last_modified,
            "metadata": stat.metadata,
        }
