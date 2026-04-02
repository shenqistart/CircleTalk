"""Redis connection management and tenant-aware key operations."""

import logging
from functools import lru_cache
from collections.abc import AsyncGenerator

import redis.asyncio as aioredis

from core.context.request import try_current_tenant

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service with tenant-isolated key prefixing."""

    def __init__(self, db: int | None = None) -> None:
        self._db = db or 0
        self._client: aioredis.Redis[str] | None = None

    def _initialize_client(self) -> aioredis.Redis[str]:
        from core.config.loader import ConfigLoader

        config = ConfigLoader.load()
        redis_config = config.get("redis", {})
        pool = aioredis.ConnectionPool(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            password=redis_config.get("password"),
            db=self._db,
            max_connections=20,
            decode_responses=True,
            health_check_interval=30,
        )
        return aioredis.Redis(connection_pool=pool)

    def _get_client(self) -> aioredis.Redis[str]:
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    def _build_key(self, key: str) -> str:
        tenant = try_current_tenant()
        if tenant:
            return f"{tenant}:{key}"
        return key

    def get_client(self) -> aioredis.Redis[str]:
        return self._get_client()

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self._get_client().set(self._build_key(key), value, ex=ex)

    async def get(self, key: str) -> str | None:
        return await self._get_client().get(self._build_key(key))  # type: ignore[return-value]

    async def delete(self, *keys: str) -> None:
        prefixed = [self._build_key(k) for k in keys]
        await self._get_client().delete(*prefixed)

    async def expire(self, key: str, time: int) -> None:
        await self._get_client().expire(self._build_key(key), time)

    async def scan_iter(self, match: str) -> AsyncGenerator[str, None]:
        async for key in self._get_client().scan_iter(match=self._build_key(match)):
            yield key  # type: ignore[misc]

    async def delete_by_pattern(self, pattern: str) -> None:
        keys_to_delete: list[str] = []
        async for key in self.scan_iter(pattern):
            keys_to_delete.append(key)
        if keys_to_delete:
            await self._get_client().delete(*keys_to_delete)

    async def close(self) -> None:
        if self._client:
            await self._client.close()


@lru_cache(maxsize=1)
def redis_service() -> RedisService:
    return RedisService()
