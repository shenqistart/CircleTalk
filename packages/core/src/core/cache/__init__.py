"""
通用缓存抽象层

提供统一的缓存接口，支持多种后端实现：
- Memory: 本地内存缓存（单实例部署）
- Redis: 分布式缓存（多实例部署）

设计原则：
1. 统一接口：所有缓存后端实现相同的 API
2. 命名空间隔离：使用前缀避免 Key 冲突
3. TTL 自动过期：所有缓存项都有过期时间
4. 线程安全：支持并发访问

使用示例：
    from core.cache import get_cache

    cache = get_cache()
    cache.set("user:123", {"name": "Alice"}, ttl=300)
    user = cache.get("user:123")
    cache.delete("user:123")
"""

from core.cache.base import CacheBackend
from core.cache.factory import get_cache, reset_cache
from core.cache.memory import MemoryCache
from core.cache.redis_service import RedisService

__all__ = ["CacheBackend", "MemoryCache", "RedisService", "get_cache", "reset_cache"]
