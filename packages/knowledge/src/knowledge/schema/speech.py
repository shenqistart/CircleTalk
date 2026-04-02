"""演讲稿整理请求/响应 Schema（无状态 API）

三步向导:
- outline: 上传文件 + AI 生成智能大纲
- refine-segment: 精炼模式逐条处理
- polish: 全局润色
- save: 保存到知识库
- expand: 扩写模式 SSE 流（按大纲逐条扩写）
"""

from typing import Literal

from pydantic import BaseModel, field_validator


class SpeechRefineConfig(BaseModel):
    """整理配置（精炼/扩写通用）"""

    topic: str = ""
    audience: str = ""
    requirements: str = ""
    style_instructions: str = ""
    target_chars: int = 0
    mode: Literal["refine", "expand"] = "refine"


# --- 大纲 ---


class LLMOutlineItem(BaseModel):
    """LLM 大纲输出的单条（内部解析用）

    source_start/source_end 范围校验宽松处理:
    _build_outline_items 会安全修正越界/反转的范围并跳过空文本条目。
    """

    title: str
    description: str = ""
    budget: int
    source_start: int = 0
    source_end: int = 0


class OutlineItem(BaseModel):
    """大纲条目（前后端共享）"""

    index: int
    title: str
    description: str = ""
    budget: int
    source_start: int
    source_end: int
    source_text: str = ""


class OutlineResponse(BaseModel):
    """大纲 API 响应"""

    outline: list[OutlineItem]
    total_budget: int
    source_chars: int
    filename: str


# --- 精炼 ---


MAX_SEGMENT_TEXT_LENGTH = 20_000
MAX_REFINED_TEXTS_COUNT = 50
MAX_FINAL_TEXT_LENGTH = 200_000
MAX_OUTLINE_ITEMS = 30


class RefineSegmentRequest(BaseModel):
    """单条精炼请求（无状态，前端发送条目全文）"""

    segment_text: str
    topic: str
    description: str = ""
    config: SpeechRefineConfig
    previous_refined_tail: str | None = None

    @field_validator("segment_text")
    @classmethod
    def validate_segment_text(cls, v: str) -> str:
        if len(v) > MAX_SEGMENT_TEXT_LENGTH:
            msg = f"段落文本超过 {MAX_SEGMENT_TEXT_LENGTH} 字上限"
            raise ValueError(msg)
        if not v.strip():
            msg = "段落文本不能为空"
            raise ValueError(msg)
        return v


class RefineSegmentResponse(BaseModel):
    """单条精炼响应"""

    refined_text: str
    original_chars: int
    refined_chars: int


class PolishRequest(BaseModel):
    """全局润色请求（无状态，前端发送全部精炼文本）"""

    refined_texts: list[str]
    config: SpeechRefineConfig

    @field_validator("refined_texts")
    @classmethod
    def validate_refined_texts(cls, v: list[str]) -> list[str]:
        if len(v) > MAX_REFINED_TEXTS_COUNT:
            msg = f"段落数量超过 {MAX_REFINED_TEXTS_COUNT} 上限"
            raise ValueError(msg)
        if not v:
            msg = "精炼文本列表不能为空"
            raise ValueError(msg)
        return v


class PolishResponse(BaseModel):
    """全局润色响应"""

    final_text: str
    skipped: bool


class SaveRequest(BaseModel):
    """保存到知识库请求"""

    final_text: str
    knowledge_base_id: str
    filename: str

    @field_validator("final_text")
    @classmethod
    def validate_final_text(cls, v: str) -> str:
        if len(v) > MAX_FINAL_TEXT_LENGTH:
            msg = f"最终文稿超过 {MAX_FINAL_TEXT_LENGTH} 字上限"
            raise ValueError(msg)
        if not v.strip():
            msg = "最终文稿不能为空"
            raise ValueError(msg)
        return v

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, v: str) -> str:
        if not v.strip():
            msg = "文件名不能为空"
            raise ValueError(msg)
        return v


class SaveResponse(BaseModel):
    """保存到知识库响应"""

    knowledge_id: str
    filename: str


# --- 扩写管道 ---


class ExpandRequest(BaseModel):
    """扩写请求（按大纲逐条扩写，每条 OutlineItem 已携带 source_text）"""

    outline: list[OutlineItem]
    config: SpeechRefineConfig

    @field_validator("outline")
    @classmethod
    def validate_outline(cls, v: list[OutlineItem]) -> list[OutlineItem]:
        if not v:
            msg = "大纲不能为空"
            raise ValueError(msg)
        if len(v) > MAX_OUTLINE_ITEMS:
            msg = f"大纲条目数超过 {MAX_OUTLINE_ITEMS} 上限"
            raise ValueError(msg)
        return v
