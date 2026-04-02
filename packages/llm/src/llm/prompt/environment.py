"""
核心提示词模块，提供 Jinja2 模板渲染功能。

核心组件:
- `prompt_template_env`: 预配置的 Jinja2 环境实例，注册了自定义过滤器
- `render_template_string`: 从字符串渲染模板（用于数据库中的动态模板）

注意：固定模板文件已迁移至各域的 prompts/templates/ 目录：
- model/chat/prompts/templates/ - Chat 域模板
- model/knowledge/prompts/templates/ - Knowledge 域模板
"""

from jinja2 import Environment, select_autoescape

from llm.prompt import formatters

# 创建无 loader 的环境，用于渲染字符串模板
prompt_template_env = Environment(
    trim_blocks=False,
    lstrip_blocks=False,
    enable_async=True,
    autoescape=select_autoescape(("html", "xml", "jinja", "j2")),
)

# 注册自定义过滤器
prompt_template_env.filters["summarize_ai_payload"] = formatters.summarize_ai_payload
prompt_template_env.filters["format_filters_for_prompt"] = formatters.format_filters_for_prompt
prompt_template_env.filters["format_json_for_prompt"] = formatters.format_json_for_prompt


def render_template_string(template_str: str, **kwargs: object) -> str:
    """从字符串渲染 Jinja2 模板。"""
    template = prompt_template_env.from_string(template_str)
    return template.render(**kwargs)


async def render_template_string_async(template_str: str, **kwargs: object) -> str:
    """从字符串异步渲染 Jinja2 模板。"""
    template = prompt_template_env.from_string(template_str)
    return await template.render_async(**kwargs)
