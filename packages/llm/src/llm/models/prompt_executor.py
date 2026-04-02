"""PromptExecutor: 负责编排和执行基于模板的语言模型调用。"""

import uuid
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from core.context.request import get_request_context
from core.logging import get_logger
from jinja2 import Environment
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from sqlalchemy.ext.asyncio import AsyncSession

from core.sse.sse_events import ThinkingStatus


class PromptTemplateResult(Protocol):
    """PromptTemplate 查询结果的最小协议。"""

    @property
    def content(self) -> str: ...


@runtime_checkable
class PromptTemplateServiceProtocol(Protocol):
    """PromptTemplateService 的最小协议，解耦 llm 对 domain 的依赖。"""

    async def get_prompt_template_by_id(
        self, session: AsyncSession, prompt_id: str, extra_vars: dict[str, Any] | None = None
    ) -> PromptTemplateResult | None: ...


logger = get_logger(__name__)


@dataclass
class StreamChunk:
    """流式输出的数据块"""

    chunk_type: str  # "trace" | "delta" | "complete"
    content: str = ""
    step: str = ""
    status: ThinkingStatus = ThinkingStatus.IN_PROGRESS
    message: str = ""
    metadata: dict[str, Any] | None = None


class PromptExecutor:
    """
    Prompt执行器

    该类编排了从获取Prompt模板、渲染变量到调用LLM的整个流程。
    它通过依赖注入一个完全配置好的LLMClient来解耦与具体模型配置的依赖。
    """

    def __init__(
        self,
        chat_model: BaseChatModel,
        model_name: str,
        prompt_template_service: PromptTemplateServiceProtocol,
        jinja2_env: Environment | None = None,
        system_prompt: str | None = None,
    ) -> None:
        """
        初始化PromptExecutor。

        Args:
            chat_model: 一个可选的、已经完全配置好的LangChain聊天模型实例。
            model_name: 所用模型的名称，用于日志记录。
            prompt_template_service: Prompt模板服务（必需）
            jinja2_env: Jinja2环境（可选）
            system_prompt: 可选的默认系统提示，可被`generate`或`stream`方法覆盖。
        """
        self.chat_model = chat_model
        self.jinja2_env = jinja2_env
        self.system_prompt = system_prompt
        self.prompt_template_service = prompt_template_service
        logger.debug("[PROMPT] Executor initialized: model=%s", model_name)

    async def execute(self, user_prompt: str, system_prompt: str | None = None) -> str:
        """
        执行一次简单的、非流式的LLM调用。

        主要用于系统内部任务，如模板格式化。

        Args:
            user_prompt: 用户输入的提示。
            system_prompt: 可选的系统提示，如果提供则覆盖实例的默认值。

        Returns:
            LLM返回的文本内容。
        """
        final_system_prompt = system_prompt or self.system_prompt or ""
        messages = self._prepare_messages(final_system_prompt, user_prompt)
        result = await self.chat_model.ainvoke(input=messages)
        return result.content if isinstance(result.content, str) else str(result.content)

    async def generate(
        self,
        session: AsyncSession,
        prompt_id: str,
        prompt_vars: dict[str, Any],
        system_prompt: str | None = None,
        **_: Mapping[str, object] | None,
    ) -> BaseMessage:
        """

        通用内容生成（非流式）

        Args:
            prompt_id: 要使用的Prompt模板ID。
            prompt_vars: 填充模板所需的变量字典。
            system_prompt: 可选的系统级提示，如果提供，将覆盖模板中的默认设置。
            **kwargs: 传递给LLMClient的其他参数。
            session: 数据库会话，需显式传入的 AsyncSession 实例。

        Returns:
            生成的完整文本内容。
        """
        user_prompt, final_system_prompt = await self._prepare_prompts(session, prompt_id, prompt_vars, system_prompt)
        messages = self._prepare_messages(final_system_prompt, user_prompt)
        # LangChain Runnable 接口要求 config 类型满足 RunnableConfig；外部传入的 kwargs 只用于 provider
        result = await self.chat_model.ainvoke(
            input=messages,
        )
        logger.debug("[PROMPT] Non-stream generation done: template=%s", prompt_id)
        logger.debug("[PROMPT] Response content:\\n%s", result.content)
        if isinstance(result, AIMessage):
            result.id = str(uuid.uuid4())
        return result

    async def stream(
        self,
        session: AsyncSession,
        prompt_id: str,
        prompt_vars: dict[str, Any],
        system_prompt: str | None = None,
        **_: Mapping[str, object] | None,
    ) -> AsyncIterator[StreamChunk]:
        """
        通用内容生成（流式），返回 async generator

        Args:
            prompt_id: 要使用的Prompt模板ID。
            prompt_vars: 填充模板所需的变量字典。
            system_prompt: 可选的系统级提示，如果提供，将覆盖模板中的默认设置。
            **kwargs: 传递给LLMClient的其他参数。
            session: 数据库会话，需显式传入的 AsyncSession 实例。

        Yields:
            StreamChunk: 流式输出的数据块（trace 或 delta）
        """
        user_prompt, final_system_prompt = await self._prepare_prompts(session, prompt_id, prompt_vars, system_prompt)
        messages = self._prepare_messages(final_system_prompt, user_prompt)

        # 发送 trace: 调用 LLM
        yield StreamChunk(
            chunk_type="trace",
            step="调用LLM",
            status=ThinkingStatus.IN_PROGRESS,
            message="正在向LLM发送请求并接收流式响应",
            metadata={"source": "PromptExecutor"},
        )

        chunk_count = 0
        total_length = 0
        full_response_content: list[str] = []

        async for chunk in self.chat_model.astream(input=messages):
            chunk_count += 1
            content_piece = str(chunk.content) if chunk.content else ""
            if content_piece:
                total_length += len(content_piece)
                full_response_content.append(content_piece)
                yield StreamChunk(chunk_type="delta", content=content_piece)

        logger.debug(
            "[PROMPT] Stream generation done: template=%s, length=%d, chunks=%d", prompt_id, total_length, chunk_count
        )
        logger.debug("[PROMPT] Response content:\\n%s", "".join(full_response_content))

        # 发送 trace: 流式结束
        yield StreamChunk(
            chunk_type="trace",
            step="流式结束",
            status=ThinkingStatus.SUCCESS,
            message="LLM流式响应已结束",
            metadata={"source": "PromptExecutor"},
        )

    def _prepare_messages(self, system_prompt: str, user_prompt: str) -> list[dict[str, str]]:
        """
        [代码优化] 构造一个符合LLM API要求的消息字典列表。

        此方法将消息构建逻辑集中于一处，以遵循 DRY (Don't Repeat Yourself) 原则，
        使代码更简洁且易于维护。

        Args:
            system_prompt: 系统提示内容。
            user_prompt: 用户提示内容。

        Returns:
            一个包含消息字典的列表。
        """
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"type": "system", "content": system_prompt})
        messages.append({"type": "user", "content": user_prompt})
        return messages

    async def _prepare_prompts(
        self,
        session: AsyncSession,
        prompt_id: str,
        prompt_vars: dict[str, Any],
        system_prompt: str | None = None,
    ) -> tuple[str, str]:
        """
        统一准备用户提示和系统提示。
        它现在将变量处理委托给 PromptService。

        Args:
            prompt_id: Prompt模板的ID。
            prompt_vars: 用户提供的用于填充模板的变量。
            system_prompt: 可选的外部系统提示。

        Returns:
            一个元组，包含渲染后的用户提示 (user_prompt) 和最终的系统提示 (system_prompt)。
        """
        user_prompt = await self._render_prompt_template(session, prompt_id, prompt_vars)
        logger.debug("[PROMPT] Rendered template: id=%s", prompt_id)
        final_system_prompt = await self._prepare_system_prompt(system_prompt)
        return (user_prompt, final_system_prompt)

    async def _render_prompt_template(self, session: AsyncSession, prompt_id: str, prompt_vars: dict[str, Any]) -> str:
        """
        根据ID和变量准备最终的用户提示。
        """
        if not self.jinja2_env:
            msg = "PromptExecutor 未配置Jinja2环境，无法渲染模板。"
            raise ValueError(msg)
        prompt_obj = await self.prompt_template_service.get_prompt_template_by_id(session, prompt_id)
        if not prompt_obj:
            msg = f"无法生成内容，因为未在数据库中找到ID为 '{prompt_id}' 的Prompt模板"
            raise ValueError(msg)
        final_vars = self._prepare_variables(prompt_vars)
        try:
            template = self.jinja2_env.from_string(prompt_obj.content)
            return await template.render_async(final_vars)
        except Exception as e:
            logger.exception("[PROMPT] Jinja2 render error: template=%s", prompt_id)
            return f"--- JINJA2 RENDER ERROR: {e} ---\n\n{prompt_obj.content}"

    def _prepare_variables(self, user_vars: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        准备最终的变量字典。
        """
        try:
            context_vars = get_request_context().to_dict()
        except RuntimeError:
            context_vars = {}
        dynamic_built_in_vars = {"current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        return {**context_vars, **dynamic_built_in_vars, **(user_vars or {})}

    async def _prepare_system_prompt(self, system_prompt: str | None) -> str:
        """
        准备最终的系统提示。如果未提供，则使用实例的默认值。
        """
        if system_prompt:
            return system_prompt
        if self.system_prompt:
            return self.system_prompt
        return ""
