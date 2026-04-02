"""核心共享类型定义。

提供跨模块复用的 JSON/通用负载/Args 类型，避免重复使用 ``Any``。
"""

from __future__ import annotations

JSONPrimitive = str | int | float | bool | None
JSONValue = object
JSONDict = dict[str, JSONValue]
Args = tuple[object, ...]
Kwargs = dict[str, object]
StrObjectDict = dict[str, object]

__all__ = [
    "Args",
    "JSONDict",
    "JSONPrimitive",
    "JSONValue",
    "Kwargs",
    "StrObjectDict",
]
