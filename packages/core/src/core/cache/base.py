"""
缓存抽象基类

定义统一的缓存接口，所有缓存后端必须实现此接口
"""

from abc import ABC, abstractmethod

# JSON 可序列化值类型
JSONValue = object


class CacheBackend(ABC):
    """
    缓存后端抽象基类

    所有缓存实现（Memory、Redis 等）必须继承此类并实现所有抽象方法

    设计原则：
    - 简单明确：只提供最基本的 CRUD 操作
    - 类型安全：明确的类型注解
    - 统一行为：所有实现必须遵循相同的语义
    """

    @abstractmethod
    def get(self, key: str) -> JSONValue | None:
        """
        获取缓存值

        参数：
            key: 缓存键

        返回：
            缓存值，如果不存在或已过期返回 None
        """

    @abstractmethod
    def set(self, key: str, value: JSONValue, ttl: int) -> None:
        """
        设置缓存值

        参数：
            key: 缓存键
            value: 缓存值（支持任意可序列化的 Python 对象）
            ttl: 过期时间（秒），必须 > 0

        注意：
            - ttl=0 表示立即过期（等同于不缓存）
            - ttl<0 无效，会抛出 ValueError
        """

    @abstractmethod
    def delete(self, key: str) -> None:
        """
        删除缓存值

        参数：
            key: 缓存键

        注意：
            - 如果 key 不存在，不抛出异常（幂等操作）
        """

    @abstractmethod
    def clear(self, pattern: str | None = None) -> None:
        """
        清除缓存

        参数：
            pattern: 可选的 Key 模式（如 "user:*"），如果为 None 则清空所有缓存

        注意：
            - 使用通配符 * 匹配任意字符（如 Redis KEYS 语法）
            - Memory 后端使用 fnmatch 模拟
        """

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        检查缓存键是否存在且未过期

        参数：
            key: 缓存键

        返回：
            True 如果存在且未过期，否则 False
        """
