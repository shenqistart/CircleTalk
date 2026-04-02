"""
缓存工厂函数

根据配置选择合适的缓存后端（Memory 或 Redis）

设计原则：
- 单例模式：全局共享一个缓存实例
- 配置驱动：通过 config.yaml 切换后端
- 延迟初始化：首次调用时才创建实例

使用示例：
    from core.cache import get_cache

    cache = get_cache()
    cache.set("key", "value", ttl=300)
"""

from typing import Any

from core.cache.base import CacheBackend
from core.cache.memory import MemoryCache
from core.cache.redis import RedisCache
from core.logging import get_logger

logger = get_logger(__name__)
_CACHE_STATE: dict[str, CacheBackend | None] = {"instance": None}


def get_cache() -> CacheBackend:
    """
    获取缓存实例（单例）

    返回：
        CacheBackend 实例（Memory 或 Redis）

    注意：
        - 第一次调用时根据配置创建实例
        - 后续调用直接返回已创建的实例
        - 线程安全（使用模块级变量 + import lock）

    配置：
        在 config.yaml 中配置缓存后端：
        ```yaml
        cache:
          backend: memory  # 或 redis
        ```

        如果未配置，默认使用 memory
    """
    if (instance := _CACHE_STATE["instance"]) is not None:
        return instance
    backend_type = "memory"
    try:
        from core.config.loader import ConfigLoader

        raw_config: dict[str, Any] = ConfigLoader.load()
        cache_config: dict[str, Any] = raw_config.get("cache", {})
        backend_type = cache_config.get("backend", "memory")
    except Exception as e:
        logger.warning("读取缓存配置失败，使用默认 memory 模式: %s", e)
    if backend_type == "redis":
        logger.info("初始化 RedisCache")
        _CACHE_STATE["instance"] = RedisCache()
    elif backend_type == "memory":
        logger.info("初始化 MemoryCache")
        _CACHE_STATE["instance"] = MemoryCache()
    else:
        logger.error("未知的缓存后端类型: %s，回退到 memory", backend_type)
        _CACHE_STATE["instance"] = MemoryCache()
    return _CACHE_STATE["instance"]


def reset_cache() -> None:
    """
    重置缓存实例（主要用于测试）

    注意：
        - 会清空当前缓存内容
        - 下次调用 get_cache() 会重新创建实例
    """
    _CACHE_STATE["instance"] = None
    logger.info("缓存实例已重置")
