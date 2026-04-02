"""
通用链工厂 - LangChain 1.x 最佳实践版本

使用 with_structured_output() 直接获取结构化输出，
OpenAI 自动使用 Function Calling，Ollama 等降级到 JSON mode。
"""

from typing import Any

from core.logging import get_logger
from jinja2 import Environment
from langchain_core.language_models import BaseChatModel
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompt_values import PromptValue
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

from llm.models.llm_factory import LLMModule, get_chat_model
from llm.models.template import Jinja2ChatPromptTemplate

logger = get_logger(__name__)


def create_structured_output_chain(
    jinja2_env: Environment,
    template_name: str,
    output_model: type[BaseModel],
    log_message_prefix: str,
    strict: bool = True,
) -> Runnable[dict[str, Any], Any]:
    """
    LangChain 1.x 标准链工厂 - 使用 with_structured_output()

    核心改进:
    1. 移除 json_mode 参数 - 不再需要
    2. 移除 PydanticOutputParser - OpenAI 直接返回结构化对象
    3. 使用 with_structured_output() - 自动选择最佳策略
    4. 支持 strict mode - 强制输出符合 schema

    Args:
        jinja2_env: Jinja2环境
        template_name: 模板文件名
        output_model: Pydantic模型（自动转换为 JSON schema）
        log_message_prefix: 日志前缀
        strict: 是否启用 OpenAI strict mode（推荐True）

    Returns:
        配置好的 LCEL 链
    """
    # 获取聊天模型（不需要 json_mode）
    chat_model: BaseChatModel = get_chat_model(LLMModule.CHAT)

    # 检测 provider 并选择策略
    if isinstance(chat_model, ChatOpenAI):
        # OpenAI: 使用 function calling
        try:
            structured_llm = chat_model.with_structured_output(
                output_model,
                method="function_calling",
                strict=strict,
                include_raw=False,
            )
            logger.info("使用 OpenAI function calling 获取结构化输出: %s", output_model.__name__)
        except Exception as e:
            # 降级到 JSON mode
            logger.warning("Function calling 失败，降级到 JSON mode: %s", e)
            structured_llm = chat_model.with_structured_output(
                output_model,
                method="json_mode",
            )
    else:
        # Ollama 等其他模型：使用 JSON mode + Parser
        logger.warning(
            "模型 %s 不支持 function calling，降级到 JSON mode + PydanticOutputParser", type(chat_model).__name__
        )
        # 需要手动解析
        output_parser = PydanticOutputParser(pydantic_object=output_model)

        # 尝试使用 with_structured_output（某些模型支持）
        try:
            structured_llm = chat_model.with_structured_output(
                output_model,
                method="json_mode",
            )
        except (AttributeError, NotImplementedError):
            # 完全降级：手动组合
            structured_llm = chat_model | output_parser

    # 加载模板
    if jinja2_env.loader is None:
        msg = "Jinja2 Environment 必须配置 loader"
        raise RuntimeError(msg)
    template_content, _, _ = jinja2_env.loader.get_source(jinja2_env, template_name)
    prompt = Jinja2ChatPromptTemplate.from_template(template=template_content, jinja2_env=jinja2_env)

    def log_prompt(prompt_value: PromptValue) -> PromptValue:
        """记录渲染后的提示词"""
        messages = prompt_value.to_messages()

        # 如果是非 function calling 模型，自动添加 schema 说明
        if not isinstance(chat_model, ChatOpenAI):
            schema_json = output_model.model_json_schema()
            schema_instruction = f"\n\n请严格按照以下 JSON schema 输出:\n{schema_json}"
            # 在最后一条消息添加 schema
            if messages:
                messages[-1].content = str(messages[-1].content) + schema_instruction

        rendered_prompt = "\n".join([str(msg.content) for msg in messages])
        logger.info("%s:\\n%s", log_message_prefix, rendered_prompt)
        return prompt_value

    def log_output(parsed_output: BaseModel) -> BaseModel:
        """记录解析后的结构化输出"""
        log_title = log_message_prefix.split("渲染后的", maxsplit=1)[0]
        logger.info("%s 结构化输出: %s", log_title, parsed_output.model_dump_json(indent=2))
        return parsed_output

    # 构建简化的链
    return (
        prompt
        | RunnableLambda(log_prompt)
        | structured_llm  # 直接返回 Pydantic 对象
        | RunnableLambda(log_output)
    )
