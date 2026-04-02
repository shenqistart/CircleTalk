"""异步 Reranker 基类。

基于模板方法模式，提供：
- httpx.AsyncClient 连接池管理
- tenacity 指数退避重试机制
- 异步优先，同步降级

子类只需实现 _request_rerank 和 _get_provider_name

解决 P0 问题：原实现使用 requests 同步调用，但被 await 异步调用导致阻塞。
现改为使用 httpx.AsyncClient 实现真正的异步。
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import ClassVar

import httpx
from core.logging import get_logger
from langchain_core.callbacks.base import Callbacks
from langchain_core.documents import BaseDocumentCompressor, Document
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = get_logger(__name__)

_http_clients_lock = asyncio.Lock()

_DEFAULT_MAX_CONNECTIONS = 50
_DEFAULT_MAX_KEEPALIVE = 10
_DEFAULT_KEEPALIVE_EXPIRY = 30.0
_DEFAULT_TIMEOUT = 60.0
_DEFAULT_CONNECT_TIMEOUT = 10.0

_RETRY_ATTEMPTS = 3
_RETRY_WAIT_MIN = 1
_RETRY_WAIT_MAX = 10
_RETRY_WAIT_MULTIPLIER = 2


class RerankResult(BaseModel):
    """Rerank API 返回的单条结果。"""

    index: int
    relevance_score: float


class BaseAsyncReranker(BaseDocumentCompressor, ABC):
    """异步 Reranker 基类。

    特性：
    - 连接池管理：使用 httpx.AsyncClient 复用连接
    - 自动重试：指数退避策略，最多重试 3 次
    - 异步优先：原生支持 async/await
    - 同步降级：compress_documents 使用 asyncio.run

    解决 P0 问题：
    - 原实现使用 requests 同步库
    - 但 retriever_factory 中使用 await reranker.acompress_documents() 调用
    - 导致事件循环阻塞，现改为真正的异步实现
    """

    top_n: int = 3
    model: str
    api_key: str | None = None
    base_url: str | None = None
    request_timeout: float = _DEFAULT_TIMEOUT

    max_connections: int = _DEFAULT_MAX_CONNECTIONS
    max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE

    _http_clients: ClassVar[dict[str, httpx.AsyncClient]] = {}

    @classmethod
    @abstractmethod
    def _get_provider_name(cls) -> str:
        """返回提供商名称，用于日志输出。"""
        ...

    @abstractmethod
    async def _request_rerank(self, query: str, documents: list[str]) -> list[RerankResult]:
        """发送 Rerank 请求（子类实现）。

        Args:
            query: 查询文本
            documents: 待重排序的文档列表

        Returns:
            按相关性排序的结果列表
        """
        ...

    def _get_client_key(self) -> str:
        """生成客户端缓存键（包含类名确保子类独立）。"""
        return f"{type(self).__name__}:{self.base_url}:{self.api_key}"

    async def _get_async_client(self) -> httpx.AsyncClient:
        """获取或创建异步 HTTP 客户端（单例模式，并发安全）。

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
                    "创建 %s Reranker HTTP 客户端: max_connections=%d",
                    cls._get_provider_name(),
                    self.max_connections,
                )

        return cls._http_clients[client_key]

    @retry(
        stop=stop_after_attempt(_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=_RETRY_WAIT_MULTIPLIER, min=_RETRY_WAIT_MIN, max=_RETRY_WAIT_MAX),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
        reraise=True,
    )
    async def _request_with_retry(self, query: str, documents: list[str]) -> list[RerankResult]:
        """带重试的请求包装。

        重试策略：
        - 最多重试 3 次
        - 指数退避：1s -> 2s -> 4s（最大 10s）
        - 仅对网络/超时错误重试
        """
        return await self._request_rerank(query, documents)

    async def acompress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Callbacks | None = None
    ) -> Sequence[Document]:
        """异步对文档进行重排序。

        Args:
            documents: 待重排序的文档列表
            query: 查询文本
            callbacks: LangChain 回调（本实现未使用）

        Returns:
            按相关性排序的文档列表（top_n 个）
        """
        _ = callbacks  # 基类接口要求，本实现未使用
        if not documents:
            return []

        docs_for_rerank = [doc.page_content for doc in documents]

        try:
            rerank_results = await self._request_with_retry(query, docs_for_rerank)
        except httpx.HTTPStatusError:
            logger.exception("调用 %s Rerank API 失败", self._get_provider_name())
            return []

        if not rerank_results:
            logger.warning("%s Rerank 服务未返回有效结果", self._get_provider_name())
            return []

        final_docs: list[Document] = []
        for result in rerank_results:
            if result.index >= len(documents):
                continue
            doc = documents[result.index]
            new_metadata = dict(doc.metadata) if doc.metadata else {}
            new_metadata["relevance_score"] = result.relevance_score
            final_docs.append(Document(page_content=doc.page_content, metadata=new_metadata))

        return final_docs

    def compress_documents(
        self, documents: Sequence[Document], query: str, callbacks: Callbacks | None = None
    ) -> Sequence[Document]:
        """同步对文档进行重排序（兼容接口）。

        检测当前是否在事件循环中：
        - 若不在事件循环中，使用 asyncio.run
        - 若在事件循环中，抛出 RuntimeError 提示使用异步方法
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(self.acompress_documents(documents, query, callbacks))

        msg = "compress_documents() 不能在已有事件循环中调用，请使用 await acompress_documents() 替代"
        raise RuntimeError(msg)

    @classmethod
    async def close_all_clients(cls) -> None:
        """关闭所有 HTTP 客户端（用于优雅关闭）。"""
        for client in cls._http_clients.values():
            await client.aclose()
        cls._http_clients.clear()
        logger.info("已关闭所有 %s Reranker HTTP 客户端", cls._get_provider_name())
