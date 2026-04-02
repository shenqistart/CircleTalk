"""
本地内存缓存实现

使用 Python 字典 + 过期时间实现的线程安全缓存

特性：
- TTL 自动过期：每次 get() 时检查过期时间
- 线程安全：使用 threading.Lock 保护共享状态
- 零依赖：仅使用 Python 标准库
- 适用场景：单实例部署

实现细节：
- 缓存结构：{key: {"value": Any, "expire_at": float}}
- 过期策略：惰性删除（访问时检查）+ 后台清理（可选）
- 内存管理：无 LRU，依赖 TTL 自然过期
"""

import threading
import time
from fnmatch import fnmatch
from typing import TypedDict

from core.cache.base import CacheBackend, JSONValue
from core.logging import get_logger

logger = get_logger(__name__)


class _CacheEntry(TypedDict):
    value: JSONValue
    expire_at: float


class MemoryCache(CacheBackend):
    """
    本地内存缓存实现

    线程安全的字典缓存，支持 TTL 自动过期

    使用示例：
        cache = MemoryCache()
        cache.set("user:123", {"name": "Alice"}, ttl=300)
        user = cache.get("user:123")
    """

    def __init__(self) -> None:
        """初始化内存缓存。"""
        self._cache: dict[str, _CacheEntry] = {}
        self._lock = threading.Lock()
        logger.info("内存缓存已初始化")

    def get(self, key: str) -> JSONValue | None:
        """
        获取缓存值

        参数：
            key: 缓存键

        返回：
            缓存值，如果不存在或已过期返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None
            entry = self._cache[key]
            expire_at = entry["expire_at"]
            if time.time() >= expire_at:
                del self._cache[key]
                logger.debug("缓存已过期并删除: key=%s", key)
                return None
            return entry["value"]

    def set(self, key: str, value: JSONValue, ttl: int) -> None:
        """
        设置缓存值

        参数：
            key: 缓存键
            value: 缓存值（任意 Python 对象）
            ttl: 过期时间（秒），必须 > 0

        异常：
            ValueError: 如果 ttl <= 0
        """
        if ttl <= 0:
            msg = f"ttl 必须 > 0，当前值: {ttl}"
            raise ValueError(msg)
        expire_at = time.time() + float(ttl)
        with self._lock:
            self._cache[key] = {"value": value, "expire_at": expire_at}
            logger.debug("缓存已设置: key=%s, ttl=%ss", key, ttl)

    def delete(self, key: str) -> None:
        """
        删除缓存值

        参数：
            key: 缓存键

        注意：如果 key 不存在，不抛出异常
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug("缓存已删除: key=%s", key)

    def clear(self, pattern: str | None = None) -> None:
        """
        清除缓存

        参数：
            pattern: 可选的 Key 模式（如 "user:*"），如果为 None 则清空所有缓存

        注意：使用 fnmatch 实现通配符匹配
        """
        with self._lock:
            if pattern is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info("已清空所有缓存: count=%s", count)
            else:
                keys_to_delete = [key for key in self._cache if fnmatch(key, pattern)]
                for key in keys_to_delete:
                    del self._cache[key]
                logger.info("按模式清除缓存: pattern=%s, count=%s", pattern, len(keys_to_delete))

    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在且未过期

        参数：
            key: 缓存键

        返回：
            True 如果存在且未过期，否则 False
        """
        with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache[key]
            expire_at = entry["expire_at"]
            if time.time() >= expire_at:
                del self._cache[key]
                return False
            return True

    def size(self) -> int:
        """
        获取当前缓存项数量（包括已过期但未删除的项）

        返回：
            缓存项数量
        """
        with self._lock:
            return len(self._cache)

    def cleanup_expired(self) -> int:
        """
        手动清理所有过期项

        返回：
            清理的项数

        注意：
            - 通常不需要手动调用，get() 会惰性删除
            - 可在定时任务中调用以释放内存
        """
        current_time = time.time()
        with self._lock:
            keys_to_delete = [key for key, entry in self._cache.items() if current_time >= entry["expire_at"]]
            for key in keys_to_delete:
                del self._cache[key]
            if keys_to_delete:
                logger.info("手动清理过期缓存: count=%s", len(keys_to_delete))
            return len(keys_to_delete)
