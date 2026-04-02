"""Redis cache backend implementation."""

import json
from typing import Any

import redis


class RedisCache:
    """Redis-backed cache with JSON serialization."""

    def __init__(self, redis_client: redis.Redis[str]) -> None:
        self._client = redis_client

    async def get(self, key: str) -> Any | None:
        value = self._client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        if ttl:
            self._client.setex(key, ttl, serialized)
        else:
            self._client.set(key, serialized)

    async def delete(self, key: str) -> None:
        self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(self._client.exists(key))

    async def clear(self, pattern: str | None = None) -> None:
        if pattern is None:
            self._client.flushdb()
        else:
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
