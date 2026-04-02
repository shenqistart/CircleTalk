"""环境变量工具模块."""

import os
from collections.abc import Mapping


class EnvUtils:
    """环境变量工具，提供环境配置的读取和验证."""

    @staticmethod
    def get_bool(name: str, default: bool = False) -> bool:
        """将环境变量转换为布尔值"""
        value = os.environ.get(name, str(default)).lower()
        return value in {"true", "1", "yes", "y"}

    @staticmethod
    def get_int(name: str, default: int = 0) -> int:
        """将环境变量转换为整数"""
        try:
            return int(os.environ.get(name, default))
        except (ValueError, TypeError):
            return default

    @staticmethod
    def get_str(name: str, default: str = "") -> str:
        """获取环境变量字符串值"""
        return os.environ.get(name, default)

    @staticmethod
    def get_from_dict_or_env(
        data: Mapping[str, object],
        key: str,
        env_key: str,
        default: str | None = None,
    ) -> str | None:
        """从配置字典或环境变量中获取值（优先使用字典）。

        按以下优先级获取配置值：
        1. 配置字典中的 key
        2. 环境变量 env_key
        3. 默认值 default

        Args:
            data: 配置字典
            key: 字典键名
            env_key: 环境变量键名
            default: 默认值

        Returns:
            获取到的字符串值或 None
        """
        value = data.get(key)
        if isinstance(value, str) and value:
            return value
        env_value = os.getenv(env_key)
        if env_value:
            return env_value
        return default
