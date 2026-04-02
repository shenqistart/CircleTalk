"""提示词模板中使用的自定义格式化工具函数。"""

import json

from core.type.common import JSONValue


def format_filters_for_prompt(filters: dict[str, list[str] | None]) -> str:
    """
    将已简化的过滤器字典格式化为LLM友好的、简洁的JSON字符串。

    此函数假定输入的字典已经是被 `CumulativeFilters.get_contextual_filters`
    处理过的简单结构 (`Dict[str, List[str]]`)。

    其主要职责是清理空值并序列化为JSON。
    """
    if not filters:
        return "{}"
    cleaned = {k: v for k, v in filters.items() if v is not None and v not in ([], {}, "")}
    return json.dumps(cleaned, ensure_ascii=False)


def format_json_for_prompt(json_str: str) -> str:
    """
    将包含JSON字符串的模板变量格式化为更易读的格式，并确保正确的缩进。
    """
    try:
        data = json.loads(f"[{json_str}]")
        return json.dumps(data, ensure_ascii=False, indent=4)
    except json.JSONDecodeError:
        return f"[\n{json_str}\n]"


def summarize_ai_payload(payload_str: str) -> str:
    """根据AI响应负载的类型生成简洁的摘要。"""
    try:
        data: JSONValue = json.loads(payload_str)
    except (json.JSONDecodeError, TypeError):
        return payload_str

    # 尝试解析为 TextPayload
    summary = _summarize_text_payload(data)
    if summary is not None:
        return summary

    return payload_str


def _summarize_text_payload(data: JSONValue) -> str | None:
    if not isinstance(data, dict) or "message" not in data:
        return None
    message = data.get("message")
    return str(message) if message is not None else None
