"""异步 Embedding 客户端基类。

基于模板方法模式，提供：
- httpx.AsyncClient 连接池管理
- tenacity 指数退避重试机制
- 单例模式复用 HTTP 客户端

子类只需实现 _request_embeddings 和 _get_provider_name
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import ClassVar

import httpx
from core.logging import get_logger
from langchain_core.embeddings import Embeddings
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_http_clients_lock = asyncio.Lock()

_DEFAULT_MAX_CONNECTIONS = 100
_DEFAULT_MAX_KEEPALIVE = 20
_DEFAULT_KEEPALIVE_EXPIRY = 30.0
_DEFAULT_TIMEOUT = 30.0
_DEFAULT_CONNECT_TIMEOUT = 10.0

_RETRY_ATTEMPTS = 3
_RETRY_WAIT_MIN = 1
_RETRY_WAIT_MAX = 10
_RETRY_WAIT_MULTIPLIER = 2

_DEFAULT_BATCH_SIZE = 10
_DEFAULT_MAX_CONCURRENT_BATCHES = 5


class BaseAsyncEmbeddings(BaseModel, Embeddings, ABC):
    """异步 Embedding 客户端基类。

    特性：
    - 连接池管理：使用 httpx.AsyncClient 复用连接
    - 自动重试：指数退避策略，最多重试 3 次
    - 异步优先：原生支持 async/await
    - 线程安全：单例 HTTP 客户端
    """

    model: str
    api_key: str | None = None
    base_url: str | None = None
    request_timeout: float = _DEFAULT_TIMEOUT

    max_connections: int = _DEFAULT_MAX_CONNECTIONS
    max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE

    batch_size: int = _DEFAULT_BATCH_SIZE
    max_concurrent_batches: int = _DEFAULT_MAX_CONCURRENT_BATCHES

    _http_clients: ClassVar[dict[str, httpx.AsyncClient]] = {}

    @classmethod
    @abstractmethod
    def _get_provider_name(cls) -> str:
        """返回提供商名称，用于日志输出。"""
        ...

    @abstractmethod
    async def _request_embeddings(self, texts: list[str]) -> list[list[float]]:
        """发送 Embedding 请求（子类实现）。

        Args:
            texts: 待向量化的文本列表

        Returns:
            按原始顺序排列的向量列表
        """
        ...

    def _get_client_key(self) -> str:
        """生成客户端缓存键（包含类名确保子类独立）。"""
        return f"{type(self).__name__}:{self.base_url}:{self.api_key}"

    async def _get_async_client(self) -> httpx.AsyncClient:
        """获取或创建异步 HTTP 客户端（单例模式）。

        使用 httpx.Limits 配置连接池：
        - max_connections: 最大并发连接数
        - max_keepalive_connections: 保持活跃的连接数
        - keepalive_expiry: 连接保持时间
        """
        client_key = self._get_client_key()
        cls = type(self)

        async with _http_clients_lock:
            if client_key not in cls._http_clients:
                limits = httpx.Limits(
                    max_connections=self.max_connections,
                    max_keepalive_connections=self.max_keepalive_connections,
                    keepalive_expiry=_DEFAULT_KEEPALIVE_EXPIRY,
                )
                timeout = httpx.Timeout(
                    self.request_timeout,
                    connect=_DEFAULT_CONNECT_TIMEOUT,
                )
                client = httpx.AsyncClient(
                    limits=limits,
                    timeout=timeout,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )
                cls._http_clients[client_key] = client
                logger.info(
                    "创建 %s HTTP 客户端: max_connections=%d, max_keepalive=%d",
                    cls._get_provider_name(),
                    self.max_connections,
                    self.max_keepalive_connections,
                )

        return cls._http_clients[client_key]

    @retry(
        stop=stop_after_attempt(_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=_RETRY_WAIT_MULTIPLIER, min=_RETRY_WAIT_MIN, max=_RETRY_WAIT_MAX),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    async def _request_with_retry(self, texts: list[str]) -> list[list[float]]:
        """带重试的请求包装。

        重试策略：
        - 最多重试 3 次
        - 指数退避：1s -> 2s -> 4s（最大 10s）
        - 仅对网络/超时错误重试
        """
        try:
            return await self._request_embeddings(texts)
        except httpx.HTTPStatusError as e:
            logger.exception(
                "[%s] API 请求失败: status=%s, url=%s, response=%s",
                self._get_provider_name(),
                e.response.status_code,
                e.request.url,
                e.response.text,
            )
            raise

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """异步对一组文本进行 embedding。

        自动按 batch_size 分批处理，使用 Semaphore 限制并发数，
        避免超过 API 限制的同时最大化吞吐量。

        错误处理策略：Fail-Fast
        - 任意 batch 失败将立即中止整个操作并抛出异常
        - 设计原因：部分 embedding 结果通常无意义，需要完整结果
        - 单个 batch 内部已有重试机制（见 _request_with_retry）

        Args:
            texts: 待 embedding 的文本列表

        Returns:
            与输入顺序一致的 embedding 向量列表

        Raises:
            EmbeddingAPIError: API 调用失败（重试耗尽后）
        """
        if not texts:
            return []

        batches: list[tuple[int, list[str]]] = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            batches.append((i, batch))

        semaphore = asyncio.Semaphore(self.max_concurrent_batches)

        async def process_batch(batch_index: int, batch: list[str]) -> tuple[int, list[list[float]]]:
            async with semaphore:
                embeddings = await self._request_with_retry(batch)
                return (batch_index, embeddings)

        tasks = [process_batch(idx, batch) for idx, batch in batches]
        results = await asyncio.gather(*tasks)

        results_sorted = sorted(results, key=lambda x: x[0])
        all_embeddings: list[list[float]] = []
        for _, embeddings in results_sorted:
            all_embeddings.extend(embeddings)

        return all_embeddings

    async def aembed_query(self, text: str) -> list[float]:
        """异步对单个查询文本进行 embedding。"""
        result = await self.aembed_documents([text])
        return result[0] if result else []

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """同步对一组文本进行 embedding（兼容接口）。"""
        return asyncio.run(self.aembed_documents(texts))

    def embed_query(self, text: str) -> list[float]:
        """同步对单个查询文本进行 embedding（兼容接口）。"""
        return asyncio.run(self.aembed_query(text))

    @classmethod
    async def close_all_clients(cls) -> None:
        """关闭所有 HTTP 客户端（用于优雅关闭）。"""
        for client in cls._http_clients.values():
            await client.aclose()
        cls._http_clients.clear()
        logger.info("已关闭所有 %s Embedding HTTP 客户端", cls._get_provider_name())
