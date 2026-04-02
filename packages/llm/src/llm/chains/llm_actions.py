"""
[新增模块] 定义LLM决策后处理的统一动作和处理器。

该模块旨在解决在多个Handler中重复处理LLM选择结果的问题。
它将LLM返回的原始意图（SELECT, CLARIFY, DISCARD）转换为一个更高级别的、
可直接执行的"动作"对象。
"""

from abc import ABC
from collections.abc import Sequence
from typing import TypeVar

from core.type import DescribableSchema, LLMDecision, SelectionResult
from pydantic import BaseModel

T = TypeVar("T", bound=DescribableSchema)


class DecisionContext(BaseModel):
    """
    为决策处理器提供额外的上下文信息，以便其能够根据不同场景（如单选/多选）
    执行更精细的逻辑。
    """

    allow_multiple: bool = False
    query_string: str | None = None


class DecisionAction(BaseModel, ABC):
    """决策动作的抽象基类（不使用泛型，payload 类型由子类定义）。"""

    reason: str | None = None


class ApplySelection[T: DescribableSchema](DecisionAction):
    """动作：应用单个选择。"""

    payload: T


class ApplyMultiSelection[T: DescribableSchema](DecisionAction):
    """动作：应用多个选择。"""

    payload: list[T]


class RequestClarification[T: DescribableSchema](DecisionAction):
    """动作：要求用户从候选列表中澄清。"""

    payload: list[T]


class Discard(DecisionAction):
    """动作：丢弃所有候选项，不进行选择。"""

    payload: None = None


DecisionActionResult = (
    ApplySelection[DescribableSchema]
    | ApplyMultiSelection[DescribableSchema]
    | RequestClarification[DescribableSchema]
    | Discard
)


class LLMDecisionProcessor:
    """
    [核心] 封装了将LLM原始选择结果转换为具体决策动作的逻辑。
    这是一个无状态的处理器，可以被任何Handler实例化和调用。
    """

    def process(
        self,
        llm_result: SelectionResult,
        candidates: Sequence[DescribableSchema],
        context: DecisionContext | None = None,
    ) -> DecisionActionResult:
        """
        处理LLM的选择结果并返回一个相应的决策动作。

        :param llm_result: 来自 selection_chain 的原始输出。
        :param candidates: 传递给 chain 的原始候选项列表（使用 Sequence 支持协变）。
        :param context: 包含额外信息的决策上下文，如是否允许多选。
        :return: 一个具体的 DecisionAction 子类对象。
        """
        decision = LLMDecision(llm_result.decision)
        reason = llm_result.reason
        ctx = context or DecisionContext()
        if decision == LLMDecision.SELECT and llm_result.best_choice_indices:
            selected_items = self._get_items_by_indices(candidates, llm_result.best_choice_indices)
            if ctx.allow_multiple:
                return ApplyMultiSelection[DescribableSchema](payload=selected_items, reason=reason)
            if selected_items:
                return ApplySelection[DescribableSchema](payload=selected_items[0], reason=reason)
        if decision == LLMDecision.CLARIFY:
            clarification_items = self._get_items_by_indices(
                candidates, llm_result.best_choice_indices, use_all_if_empty=True
            )
            return RequestClarification[DescribableSchema](payload=clarification_items, reason=reason)
        return Discard(reason=reason)

    def _get_items_by_indices(self, items: Sequence[T], indices: list[int], use_all_if_empty: bool = False) -> list[T]:
        """根据索引安全地从序列中提取元素（Sequence 支持协变）。"""
        if not indices and use_all_if_empty:
            return list(items)
        return [items[i] for i in indices if 0 <= i < len(items)]


decision_processor = LLMDecisionProcessor()
