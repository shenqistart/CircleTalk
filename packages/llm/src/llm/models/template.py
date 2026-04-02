from __future__ import annotations

from typing import Any, cast

from jinja2 import Environment, meta
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.prompts.chat import BaseChatPromptTemplate
from pydantic import PrivateAttr


class Jinja2ChatPromptTemplate(BaseChatPromptTemplate):
    """
    一个通用的、可配置的Jinja2聊天提示模板。
    """

    template: str
    template_format: str = "jinja2"
    _jinja2_env: Environment = PrivateAttr()

    def format_messages(self, **kwargs: object) -> list[BaseMessage]:
        """使用配置的 Jinja2 环境渲染模板并返回消息列表。"""
        jinja2_template = self._jinja2_env.from_string(self.template)
        rendered_string = jinja2_template.render(**kwargs)
        return [HumanMessage(content=rendered_string)]

    async def aformat_messages(self, **kwargs: object) -> list[BaseMessage]:
        """异步地使用配置的Jinja2环境渲染模板并返回消息列表。"""
        jinja2_template = self._jinja2_env.from_string(self.template)
        rendered_string = await jinja2_template.render_async(**kwargs)
        return [HumanMessage(content=rendered_string)]

    @classmethod
    def from_template(
        cls, template: str, jinja2_env: Environment, template_format: str = "jinja2", **kwargs: object
    ) -> Jinja2ChatPromptTemplate:
        """
        从模板字符串和Jinja2环境创建实例的工厂方法。
        """
        if template_format != "jinja2":
            msg = "本模板类仅支持 'jinja2' 格式。"
            raise ValueError(msg)
        ast = jinja2_env.parse(template)
        input_variables = list(meta.find_undeclared_variables(ast))
        extra_kwargs: dict[str, Any] = {key: cast(Any, value) for key, value in kwargs.items()}
        instance = cls(
            template=template,
            template_format=template_format,
            input_variables=input_variables,
            **extra_kwargs,
        )
        instance._jinja2_env = jinja2_env
        return instance
