# LLM 能力封装

> 版本: v1.0

`packages/llm` 封装 LLM 调用、向量检索、Prompt 模板等 AI 能力，屏蔽多供应商差异。

## 模块总览

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| `models` | LLM 客户端工厂、多供应商路由 | `get_chat_model()`, `get_fast_model()`, `LLMModule` |
| `models/providers` | 供应商适配（OpenAI、DashScope、Ollama） | `ChatModelProvider`, `OpenAICompatibleProvider` |
| `models/prompt_executor` | Prompt 模板渲染 + LLM 调用编排 | `PromptExecutor`, `StreamChunk` |
| `models/callbacks` | 统一可观测性回调 | `LoggingCallbackHandler` |
| `chains` | 结构化输出 Chain 工厂 | `create_structured_output_chain()` |
| `vector` | 多模式向量检索 + 嵌入管道 | `VectorStore`, `create_retriever()`, `RetrievalMode` |
| `vector/embeddings` | 异步 Embedding 供应商 | `get_embedding_client()`, `DashScopeEmbeddings` |
| `vector/rerankers` | 异步 Reranker 供应商 | `get_reranker_client()`, `DashScopeRerank` |
| `prompt` | Jinja2 模板环境 + 自定义过滤器 | `prompt_template_env`, `render_template_string()` |
| `observability` | LangSmith 链路追踪集成 | 自动初始化 |

## 目录结构

```
packages/llm/src/llm/
├── models/
│   ├── llm_factory.py        # get_chat_model(), 多租户懒初始化
│   ├── prompt_executor.py    # 模板渲染 → LLM 调用编排
│   ├── callbacks.py          # LangChain 统一日志回调
│   ├── template.py           # Prompt 模板管理
│   ├── vlm_config_factory.py # Docling VLM API 配置
│   └── providers/            # 供应商适配层
│       ├── base.py
│       ├── dashscope.py
│       ├── ollama.py
│       └── openai_compatible.py
├── chains/
│   ├── factory.py            # 结构化输出 Chain 工厂
│   └── llm_actions.py        # LLM Action 定义
├── vector/
│   ├── store.py              # VectorStore（pgvector 后端）
│   ├── retrievers/           # 检索器工厂 + 混合检索
│   ├── embeddings/           # 异步 Embedding 客户端
│   ├── rerankers/            # 异步 Reranker 客户端
│   ├── fusion/               # RRF 融合策略
│   ├── services/             # 向量服务层
│   └── mappers/              # 数据映射
├── prompt/
│   ├── environment.py        # Jinja2 环境 + 自定义过滤器
│   └── formatters.py         # Prompt 格式化工具
└── observability/
    └── langsmith_handler.py  # LangSmith 集成
```

## 核心设计模式

### 多供应商路由

`get_chat_model()` 工厂根据配置路由到不同供应商（OpenAI、DashScope、Ollama、Volcengine），返回 LangChain `BaseChatModel`。多租户懒初始化，非 OpenAI 供应商自动添加重试逻辑。

### 结构化输出

`create_structured_output_chain()` 自动选择最优策略：OpenAI 使用 function_calling（strict mode），其他供应商回退到 JSON mode + PydanticOutputParser。

### 混合检索

支持三种检索模式（`RetrievalMode`）：纯向量、纯全文、混合。混合模式使用 RRF（Reciprocal Rank Fusion）融合策略，可选 Reranker 二次排序。pgvector 后端支持按租户 Schema 隔离。
