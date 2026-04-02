"""LangChain 标准元数据过滤器构建器。

提供链式API构建符合 LangChain 1.0 标准的元数据过滤器，
支持权限过滤、业务过滤的组合。
"""

from typing import ClassVar, cast

from core.type.common import JSONValue


class MetadataFilterBuilder:
    """Metadata Filter 构建器（LangChain 1.0 标准）。

    提供链式API构建符合LangChain 1.0标准的元数据过滤器。
    支持权限过滤、业务过滤的组合。

    设计原则:
    1. 类型安全: 所有操作符都有类型提示
    2. 链式调用: 支持 builder.add_filter(...).add_in(...).build()
    3. 验证: 自动验证过滤器格式
    4. 可测试: 纯函数，无副作用

    支持操作符:
    - $eq: 等于（默认）
    - $ne: 不等于
    - $gt, $gte, $lt, $lte: 数值比较
    - $in, $nin: 包含/不包含
    - $and, $or: 逻辑组合
    - $not: 逻辑非
    - $exists: 字段存在性检查
    """

    ALLOWED_OPERATORS: ClassVar[set[str]] = {
        "$eq",
        "$ne",
        "$gt",
        "$gte",
        "$lt",
        "$lte",
        "$in",
        "$nin",
        "$and",
        "$or",
        "$not",
        "$exists",
    }

    def __init__(self) -> None:
        """初始化空的过滤器构建器。"""
        self.filters: dict[str, JSONValue] = {}

    def add_filter(self, field: str, value: JSONValue, operator: str = "$eq") -> "MetadataFilterBuilder":
        """添加单个过滤条件。

        Args:
            field: 字段名（如 "category", "owner_id"）
            value: 字段值
            operator: 操作符（默认 "$eq" 表示等于）

        Returns:
            self - 支持链式调用
        """
        if operator == "$eq":
            self.filters[field] = value
        else:
            if operator not in self.ALLOWED_OPERATORS:
                msg = f"不支持的操作符: {operator}，允许的操作符: {self.ALLOWED_OPERATORS}"
                raise ValueError(msg)
            self.filters[field] = {operator: value}
        return self

    def add_in(self, field: str, values: list[JSONValue]) -> "MetadataFilterBuilder":
        """添加 $in 操作符（字段值在列表中）。

        Args:
            field: 字段名
            values: 值列表

        Returns:
            self - 支持链式调用
        """
        if not values:
            msg = "$in 操作符的值列表不能为空"
            raise ValueError(msg)
        self.filters[field] = {"$in": values}
        return self

    def add_nin(self, field: str, values: list[JSONValue]) -> "MetadataFilterBuilder":
        """添加 $nin 操作符（字段值不在列表中）。

        Args:
            field: 字段名
            values: 排除的值列表

        Returns:
            self - 支持链式调用
        """
        if not values:
            msg = "$nin 操作符的值列表不能为空"
            raise ValueError(msg)
        self.filters[field] = {"$nin": values}
        return self

    def add_exists(self, field: str, exists: bool = True) -> "MetadataFilterBuilder":
        """添加 $exists 操作符（检查字段是否存在）。

        Args:
            field: 字段名
            exists: True表示字段必须存在，False表示字段必须不存在

        Returns:
            self - 支持链式调用
        """
        self.filters[field] = {"$exists": exists}
        return self

    def add_and(self, conditions: list[dict[str, JSONValue]]) -> "MetadataFilterBuilder":
        """添加 $and 操作符（所有条件必须满足）。

        Args:
            conditions: 条件列表

        Returns:
            self - 支持链式调用
        """
        if not conditions:
            msg = "$and 操作符的条件列表不能为空"
            raise ValueError(msg)
        if "$and" in self.filters:
            existing = cast(list[dict[str, JSONValue]], self.filters.get("$and"))
            existing.extend(conditions)
        else:
            self.filters["$and"] = list(conditions)
        return self

    def add_or(self, conditions: list[dict[str, JSONValue]]) -> "MetadataFilterBuilder":
        """添加 $or 操作符（任一条件满足即可）。

        Args:
            conditions: 条件列表

        Returns:
            self - 支持链式调用
        """
        if not conditions:
            msg = "$or 操作符的条件列表不能为空"
            raise ValueError(msg)
        if "$or" in self.filters:
            existing = cast(list[dict[str, JSONValue]], self.filters.get("$or"))
            existing.extend(conditions)
        else:
            self.filters["$or"] = list(conditions)
        return self

    def add_not(self, condition: dict[str, JSONValue]) -> "MetadataFilterBuilder":
        """添加 $not 操作符（条件取反）。

        Args:
            condition: 要取反的条件

        Returns:
            self - 支持链式调用
        """
        if not condition:
            msg = "$not 操作符的条件不能为空"
            raise ValueError(msg)
        self.filters["$not"] = condition
        return self

    def build(self) -> dict[str, JSONValue]:
        """构建并返回最终的过滤器字典。

        Returns:
            符合 LangChain 1.0 标准的过滤器字典
        """
        return dict(self.filters)

    def reset(self) -> "MetadataFilterBuilder":
        """重置构建器，清空所有过滤条件。

        Returns:
            self - 支持链式调用
        """
        self.filters = {}
        return self

    @staticmethod
    def validate_filter(filter_dict: dict[str, JSONValue]) -> bool:
        """验证 filter 格式是否符合 LangChain 1.0 标准。

        Args:
            filter_dict: 要验证的过滤器字典

        Returns:
            True 如果格式有效，否则抛出 ValueError
        """
        if not isinstance(filter_dict, dict):
            msg = "过滤器必须是字典类型"
            raise TypeError(msg)
        for key, value in filter_dict.items():
            if key.startswith("$") and key not in MetadataFilterBuilder.ALLOWED_OPERATORS:
                msg = f"不支持的操作符: {key}"
                raise ValueError(msg)
            if isinstance(value, dict):
                dict_value: dict[str, JSONValue] = value
                MetadataFilterBuilder.validate_filter(dict_value)
            if isinstance(value, list):
                if key in {"$and", "$or"}:
                    for condition in value:
                        if not isinstance(condition, dict):
                            msg = f"{key} 的条件必须是字典类型"
                            raise TypeError(msg)
                        condition_dict: dict[str, JSONValue] = condition
                        MetadataFilterBuilder.validate_filter(condition_dict)
                elif key in {"$in", "$nin"} and (not value):
                    msg = f"{key} 的值列表不能为空"
                    raise ValueError(msg)
        return True

    @staticmethod
    def merge_filters(*filters: dict[str, JSONValue]) -> dict[str, JSONValue]:
        """合并多个过滤器（使用 $and 连接）。

        Args:
            *filters: 多个过滤器字典

        Returns:
            合并后的过滤器字典
        """
        non_empty_filters = [f for f in filters if f]
        if not non_empty_filters:
            return {}
        if len(non_empty_filters) == 1:
            return non_empty_filters[0].copy()
        return {"$and": non_empty_filters}

    @staticmethod
    def build_permission_filter(
        accessible_ids: list[str] | None = None,
        id_field: str = "knowledge_id",
    ) -> dict[str, JSONValue]:
        """构建权限过滤条件。

        语义约定：
        - None: 不过滤（Admin 或未配置权限系统）
        - []: 用户无任何权限，返回 deny-all 过滤器
        - [...]: 正常 RBAC 过滤

        Args:
            accessible_ids: 预计算的可访问资源 ID 列表（由 RBAC 系统提供）
            id_field: ID 字段名（默认 "knowledge_id"）

        Returns:
            权限过滤条件字典
        """
        if accessible_ids is None:
            return {}
        if not accessible_ids:
            return cast(dict[str, JSONValue], {id_field: {"$in": ["__no_access__"]}})
        return cast(dict[str, JSONValue], {id_field: {"$in": accessible_ids}})

    @staticmethod
    def to_postgres_where_clause(
        filter_dict: dict[str, JSONValue], metadata_column: str = "metadata"
    ) -> tuple[str, dict[str, JSONValue]]:
        """将 LangChain 1.0 标准过滤器转换为 PostgreSQL JSONB WHERE 子句。

        Args:
            filter_dict: LangChain 过滤器字典
            metadata_column: 元数据列名（默认 "metadata"）

        Returns:
            tuple[str, dict[str, Any]]: (WHERE 子句, 参数字典)
        """
        if not filter_dict:
            return ("TRUE", {})
        MetadataFilterBuilder.validate_filter(filter_dict)
        builder = _PostgresFilterBuilder(metadata_column)
        where_clause = builder.build(filter_dict)
        return (where_clause, builder.params)


class _PostgresFilterBuilder:
    """将 LangChain filter 转换为 PostgreSQL WHERE 子句的辅助构建器。"""

    def __init__(self, metadata_column: str) -> None:
        self.metadata_column = metadata_column
        self.params: dict[str, JSONValue] = {}
        self._counter = 0

    def build(self, filter_dict: dict[str, JSONValue]) -> str:
        return self._build_filter(filter_dict)

    def _build_filter(self, filter_dict: dict[str, JSONValue]) -> str:
        if not isinstance(filter_dict, dict):
            msg = "过滤条件必须是字典类型"
            raise TypeError(msg)
        conditions = [self._build_condition(key, value) for key, value in filter_dict.items()]
        return " AND ".join(conditions) if len(conditions) > 1 else conditions[0]

    def _build_condition(self, key: str, value: JSONValue) -> str:
        if key in {"$and", "$or"}:
            return self._build_logical_condition(key, value)
        if key == "$not":
            return self._build_not_condition(value)
        return self._build_field_condition(key, value)

    def _build_logical_condition(self, operator: str, value: JSONValue) -> str:
        if not isinstance(value, list):
            msg = f"{operator} 的值必须是列表"
            raise TypeError(msg)
        if not value:
            msg = f"{operator} 的值必须是非空列表"
            raise ValueError(msg)
        connector = " AND " if operator == "$and" else " OR "
        expressions: list[str] = []
        for condition in value:
            if not isinstance(condition, dict):
                msg = f"{operator} 的子条件必须为字典"
                raise TypeError(msg)
            expressions.append(self._build_filter(condition))
        return f"({connector.join(expressions)})"

    def _build_not_condition(self, value: JSONValue) -> str:
        if not isinstance(value, dict):
            msg = "$not 的值必须是字典"
            raise TypeError(msg)
        condition = self._build_filter(value)
        return f"NOT ({condition})"

    def _build_field_condition(self, field: str, value: JSONValue) -> str:
        if isinstance(value, dict):
            return self._build_operator_condition(field, value)
        return self._simple_equality(field, value)

    def _build_operator_condition(self, field: str, operators: dict[str, JSONValue]) -> str:
        conditions = [self._apply_operator(field, op, op_value) for op, op_value in operators.items()]
        return " AND ".join(conditions) if len(conditions) > 1 else conditions[0]

    def _apply_operator(self, field: str, operator: str, operand: JSONValue) -> str:
        if operator == "$eq":
            return self._simple_equality(field, operand)
        if operator == "$ne":
            return self._comparison_clause(field, operand, "!=")
        if operator in {"$gt", "$gte", "$lt", "$lte"}:
            comparison_map = {"$gt": ">", "$gte": ">=", "$lt": "<", "$lte": "<="}
            return self._numeric_comparison(field, operand, comparison_map[operator])
        if operator == "$in":
            self._assert_non_empty_list(operator, operand)
            param = self._add_param(operand)
            return f"{self.metadata_column}->>{field!r} = ANY(%({param})s)"
        if operator == "$nin":
            self._assert_non_empty_list(operator, operand)
            param = self._add_param(operand)
            return f"{self.metadata_column}->>{field!r} != ALL(%({param})s)"
        if operator == "$exists":
            if not isinstance(operand, bool):
                msg = "$exists 的值必须是布尔值"
                raise TypeError(msg)
            return f"{self.metadata_column} ? {field!r}" if operand else f"NOT ({self.metadata_column} ? {field!r})"
        msg = f"不支持的操作符: {operator}"
        raise ValueError(msg)

    def _simple_equality(self, field: str, value: JSONValue) -> str:
        param = self._add_param(value)
        return f"{self.metadata_column}->>{field!r} = %({param})s"

    def _comparison_clause(self, field: str, value: JSONValue, operator: str) -> str:
        param = self._add_param(value)
        return f"{self.metadata_column}->>{field!r} {operator} %({param})s"

    def _numeric_comparison(self, field: str, value: JSONValue, operator: str) -> str:
        param = self._add_param(value)
        return f"({self.metadata_column}->>{field!r})::numeric {operator} %({param})s"

    @staticmethod
    def _assert_non_empty_list(operator: str, value: JSONValue) -> None:
        if not isinstance(value, list):
            msg = f"{operator} 的值必须是列表"
            raise TypeError(msg)
        if not value:
            msg = f"{operator} 的值列表不能为空"
            raise ValueError(msg)

    def _add_param(self, value: JSONValue) -> str:
        param_name = f"param_{self._counter}"
        self._counter += 1
        self.params[param_name] = value
        return param_name
