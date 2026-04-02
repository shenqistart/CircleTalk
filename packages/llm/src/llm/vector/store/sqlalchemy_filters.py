"""SQLAlchemy 元数据过滤器构建器。

用于 ORM 查询的 SQLAlchemy WHERE 条件构建。
"""

from collections.abc import Callable, Mapping, Sequence
from typing import cast

from sqlalchemy import Float, Table, and_, func, or_
from sqlalchemy.sql.elements import ColumnElement

SQLBoolExpr = ColumnElement[bool]
MaybeSQLBoolExpr = SQLBoolExpr | None
FilterDict = dict[str, object]


class SQLAlchemyFilterBuilder:
    """SQLAlchemy 元数据过滤器构建器，负责将过滤条件转换为 SQLAlchemy WHERE 子句。

    该类将复杂的嵌套过滤逻辑解耦为多个单一职责的方法，
    降低了代码复杂度和嵌套深度。

    支持的操作符：
    - $and, $or, $not: 逻辑操作符
    - $in: 字段值在列表中
    - $contains: JSONB 数组包含元素
    - $overlap: JSONB 数组与给定列表有交集
    - $gt, $gte, $lt, $lte: 数值比较
    - 简单相等比较
    """

    def __init__(self, table: Table) -> None:
        """初始化过滤器构建器。

        Args:
            table: SQLAlchemy 表对象
        """
        self.table = table

    def build_condition(self, filter_dict: FilterDict) -> MaybeSQLBoolExpr:
        """递归构建 WHERE 条件。

        Args:
            filter_dict: 过滤条件字典

        Returns:
            SQLAlchemy 条件表达式，或 None 如果没有条件
        """
        conditions: list[SQLBoolExpr] = []
        for key, value in filter_dict.items():
            condition = self._process_filter_item(key, value)
            if condition is not None:
                conditions.append(condition)
        return self._combine_conditions(conditions)

    def _process_filter_item(self, key: str, value: object) -> MaybeSQLBoolExpr:
        """处理单个过滤项。

        Args:
            key: 过滤键（字段名或操作符）
            value: 过滤值

        Returns:
            SQLAlchemy 条件表达式，或 None
        """
        if key == "$and" and isinstance(value, list):
            sub_filters: list[FilterDict] = [cast(FilterDict, item) for item in value if isinstance(item, dict)]
            return self._build_and_condition(sub_filters)
        if key == "$or" and isinstance(value, list):
            sub_filters = [cast(FilterDict, item) for item in value if isinstance(item, dict)]
            return self._build_or_condition(sub_filters)
        if key == "$not" and isinstance(value, dict):
            return self._build_not_condition(cast(FilterDict, value))
        if isinstance(value, dict):
            return self._build_field_condition(key, cast(FilterDict, value))
        return self._build_equality_condition(key, value)

    def _build_and_condition(self, sub_filters: Sequence[FilterDict]) -> MaybeSQLBoolExpr:
        """构建 AND 逻辑条件。"""
        sub_conditions: list[SQLBoolExpr] = []
        for sub_filter in sub_filters:
            if (built := self.build_condition(sub_filter)) is not None:
                sub_conditions.append(built)
        if not sub_conditions:
            return None
        return cast(SQLBoolExpr, and_(*sub_conditions))

    def _build_or_condition(self, sub_filters: Sequence[FilterDict]) -> MaybeSQLBoolExpr:
        """构建 OR 逻辑条件。"""
        sub_conditions: list[SQLBoolExpr] = []
        for sub_filter in sub_filters:
            if (built := self.build_condition(sub_filter)) is not None:
                sub_conditions.append(built)
        if not sub_conditions:
            return None
        return cast(SQLBoolExpr, or_(*sub_conditions))

    def _build_not_condition(self, sub_filter: FilterDict) -> MaybeSQLBoolExpr:
        """构建 NOT 逻辑条件。"""
        sub_condition = self.build_condition(sub_filter)
        if sub_condition is None:
            return None
        return cast(SQLBoolExpr, ~sub_condition)

    def _build_field_condition(self, field: str, operators: Mapping[str, object]) -> MaybeSQLBoolExpr:
        """构建字段级条件（包含操作符）。"""
        conditions: list[SQLBoolExpr] = []

        def _append_clause(clause: MaybeSQLBoolExpr) -> None:
            if clause is not None:
                conditions.append(clause)

        operator_builders: dict[str, Callable[[str, object], MaybeSQLBoolExpr]] = {
            "$in": self._build_in_condition,
            "$contains": self._build_contains_condition,
            "$overlap": self._build_overlap_condition,
        }
        for op, builder in operator_builders.items():
            if op in operators:
                _append_clause(builder(field, operators[op]))

        comparison_map = {"$gt": ">", "$gte": ">=", "$lt": "<", "$lte": "<="}
        for op, sql_op in comparison_map.items():
            if op in operators:
                _append_clause(self._build_comparison_condition(field, operators[op], sql_op))

        return self._combine_conditions(conditions)

    def _build_comparison_condition(self, field: str, operand: object, sql_op: str) -> MaybeSQLBoolExpr:
        """构建数值比较条件（$gt, $gte, $lt, $lte）。"""
        if not isinstance(operand, (int, float, str)):
            return None
        field_expr = self.table.c.metadata[field].astext.cast(Float)
        value_float = float(operand)
        comparison_funcs = {
            ">": lambda f, v: cast(SQLBoolExpr, f > v),
            ">=": lambda f, v: cast(SQLBoolExpr, f >= v),
            "<": lambda f, v: cast(SQLBoolExpr, f < v),
            "<=": lambda f, v: cast(SQLBoolExpr, f <= v),
        }
        if sql_op in comparison_funcs:
            return comparison_funcs[sql_op](field_expr, value_float)
        return None

    def _build_in_condition(self, field: str, values: object) -> MaybeSQLBoolExpr:
        """构建 IN 条件：字段值在列表中。"""
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            return None
        sequence_values = list(values)
        if not sequence_values:
            return None
        clause = self.table.c.metadata[field].astext.in_([str(v) for v in sequence_values])
        return cast(SQLBoolExpr, clause)

    def _build_contains_condition(self, field: str, value: object) -> MaybeSQLBoolExpr:
        """构建 CONTAINS 条件：JSONB 数组包含元素。"""
        clause = self.table.c.metadata[field].contains([value])
        return cast(SQLBoolExpr, clause)

    def _build_overlap_condition(self, field: str, values: object) -> MaybeSQLBoolExpr:
        """构建 OVERLAP 条件：JSONB 数组与给定列表有交集。

        使用 jsonb_path_exists 检查数组是否包含任一指定元素。
        """
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
            return None
        sequence_values = list(values)
        if not sequence_values:
            return None
        path_expr = f'$ ? (@ == "{sequence_values[0]}"'
        path_expr += "".join(f' || @ == "{v}"' for v in sequence_values[1:])
        path_expr += ")"
        clause = func.jsonb_path_exists(self.table.c.metadata[field], path_expr)
        return cast(SQLBoolExpr, clause)

    def _build_equality_condition(self, field: str, value: object) -> MaybeSQLBoolExpr:
        """构建简单相等条件。"""
        clause = self.table.c.metadata[field].astext == str(value)
        return cast(SQLBoolExpr, clause)

    def _combine_conditions(self, conditions: Sequence[SQLBoolExpr]) -> MaybeSQLBoolExpr:
        """合并多个条件。

        Args:
            conditions: 条件列表

        Returns:
            如果有多个条件，用 AND 连接；如果只有一个，直接返回；如果没有，返回 None
        """
        if len(conditions) > 1:
            return cast(SQLBoolExpr, and_(*conditions))
        if len(conditions) == 1:
            return conditions[0]
        return None
