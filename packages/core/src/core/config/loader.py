"""Configuration loader: YAML files with environment variable overrides."""

import logging
import os
from pathlib import Path
from typing import Any, ClassVar

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load configuration from YAML with environment variable override support.

    Priority: Environment variables > config.yaml
    Environment variables use BEDROCK_ prefix (e.g., BEDROCK_DATABASE_HOST).
    """

    _config: ClassVar[dict[str, Any] | None] = None

    @classmethod
    def load(cls) -> dict[str, Any]:
        if cls._config is not None:
            return cls._config
        cls._config = cls._load_yaml_config()
        return cls._config

    @classmethod
    def reload(cls) -> dict[str, Any]:
        cls._config = None
        return cls.load()

    @classmethod
    def _load_yaml_config(cls) -> dict[str, Any]:
        config_path = cls._resolve_config_path("config.yaml")
        if config_path is None:
            logger.warning("config.yaml not found, using empty config")
            return {}
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        logger.info("Loaded config from %s", config_path)
        return config

    @classmethod
    def _resolve_config_path(cls, filename: str) -> Path | None:
        env_path = os.environ.get("CONFIG_PATH")
        if env_path:
            p = Path(env_path)
            return p if p.exists() else None

        current = Path.cwd()
        candidate = current / filename
        if candidate.exists():
            return candidate

        for parent in current.parents:
            candidate = parent / filename
            if candidate.exists():
                return candidate
            if (parent / ".git").exists():
                break

        return None
