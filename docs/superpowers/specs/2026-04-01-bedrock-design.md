# Bedrock — 公司级规范示例项目设计文档

> **日期**: 2026-04-01
> **状态**: 已批准（已按实际代码状态更新）
> **定位**: 公司基石项目，所有子服务的规范源头、学习入口和设计语言参考

---

## 1. 项目定位

Bedrock 是公司的基础参考实现项目，承担三个核心职责：

1. **规范示例** — 通过完整的 User domain 演示后端三层架构（API → Service → Repository）和前端 features 组织模式
2. **Claude Code 最佳实践** — 通过 `.claude/` 目录展示 rules、skills、hooks、settings 的标准配置方式
3. **设计语言基座** — 后续的基础 UI/UX、主样式、主设计都在此项目中定义，子服务从这里继承

所有新项目启动时，团队成员先到 bedrock 学习 Claude 使用方式和前后端规范定义。

---

## 2. 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.135.x |
| Python | Python | >= 3.13 |
| ORM | SQLAlchemy (async) | 2.0.x |
| 数据库迁移 | Alembic | 1.18.x |
| 数据库 | PostgreSQL | 17+ |
| 向量扩展 | pgvector | - |
| DI 容器 | dependency-injector | 4.48.x |
| 缓存 | Redis | 7.x |
| 对象存储 | MinIO | - |
| LLM 框架 | LangChain / LangGraph | - |
| 提示词模板 | Jinja2 | - |
| 中文分词 | jieba | - |
| 全文搜索 | PostgreSQL TSVector + sqlalchemy-utils | - |
| 前端框架 | React | 19 |
| 类型 | TypeScript | 5.9 |
| 构建 | Vite | - |
| 样式 | Tailwind CSS 4.x + shadcn/ui | - |
| 数据请求 | TanStack Query | - |
| 图标 | lucide-react | - |
| 动画 | framer-motion | - |
| 包管理 | pnpm (前端) + uv (Python) | pnpm >= 9, uv latest |
| 代码质量 | Ruff + Pyright (Python), ESLint + tsc (TypeScript) | - |
| 测试 | pytest + pytest-asyncio (后端) | - |

---

## 3. 项目结构

```
bedrock/
├── apps/
│   ├── backend/                    # FastAPI Python 后端
│   │   ├── src/
│   │   │   └── backend/
│   │   │       ├── main.py         # 启动入口 + 中间件 + 路由注册
│   │   │       ├── container.py    # DI 容器（AppContainer）
│   │   │       ├── common/         # 通用工具
│   │   │       │   ├── response.py       # CommonResponse + success_response + error_response
│   │   │       │   ├── error_handler.py  # @error_handler 装饰器
│   │   │       │   └── pagination.py     # PageParams + PageResult
│   │   │       └── domain/
│   │   │           └── user/       # 用户管理 domain（示例）
│   │   │               ├── api/
│   │   │               │   └── user.py
│   │   │               ├── service/
│   │   │               │   └── user_service.py
│   │   │               ├── repository/
│   │   │               │   └── user_repository.py
│   │   │               ├── model/
│   │   │               │   └── user.py
│   │   │               └── schema/
│   │   │                   └── user_schema.py
│   │   ├── tests/
│   │   │   └── domain/
│   │   │       └── user/
│   │   ├── alembic/                # 数据库迁移
│   │   │   ├── env.py
│   │   │   ├── alembic.ini
│   │   │   └── versions/
│   │   ├── config.yaml             # 运行时配置
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   │
│   └── frontend/                   # React TypeScript 前端
│       ├── src/
│       │   ├── app/                # 应用层
│       │   │   ├── routes/         # 路由定义
│       │   │   ├── layouts/        # 布局组件（Sidebar + Header + Content）
│       │   │   └── providers/      # 全局 Provider（Theme、Auth、Query）
│       │   ├── features/           # 功能模块
│       │   │   └── user/
│       │   │       ├── components/ # UserTable、UserForm、UserDetail
│       │   │       ├── hooks/      # useUsers、useCreateUser
│       │   │       ├── api/        # 用户 API 请求封装
│       │   │       └── types/      # 用户类型定义
│       │   ├── shared/             # 全局共享
│       │   │   ├── hooks/          # usePagination、useDebounce
│       │   │   ├── lib/            # request、format、validation
│       │   │   └── types/          # ApiResponse、PageResult
│       │   └── styles/             # 设计系统
│       │       ├── globals.css     # Tailwind 入口 + CSS 变量
│       │       └── tokens/         # 设计 token（颜色、间距、字体）
│       ├── components.json         # shadcn/ui 配置
│       ├── tailwind.config.ts
│       ├── vite.config.ts
│       ├── tsconfig.json
│       └── package.json
│
├── packages/
│   ├── core/                       # 共享基础设施包
│   │   ├── src/core/
│   │   │   ├── database/
│   │   │   │   ├── base.py         # DeclarativeBase
│   │   │   │   ├── session.py      # db_session() + scoped_session()
│   │   │   │   ├── identifier.py   # 租户 → schema 映射
│   │   │   │   └── state.py        # DatabaseRegistry
│   │   │   ├── repository/
│   │   │   │   ├── base_repository.py  # BaseRepository[T] 泛型 CRUD
│   │   │   │   ├── pk_strategy.py      # 主键策略
│   │   │   │   └── specification.py    # SearchSpec、PageRequest
│   │   │   ├── cache/
│   │   │   │   ├── base.py             # CacheBackend 抽象基类
│   │   │   │   ├── memory.py           # 内存缓存实现
│   │   │   │   ├── redis.py            # Redis 客户端
│   │   │   │   ├── redis_service.py    # RedisService 实现
│   │   │   │   └── factory.py          # 缓存后端工厂
│   │   │   ├── config/
│   │   │   │   └── loader.py           # YAML 配置 + 环境变量覆盖
│   │   │   ├── context/
│   │   │   │   └── request.py          # RequestContext（contextvars）
│   │   │   ├── storage/
│   │   │   │   ├── manager.py          # StorageService 工厂
│   │   │   │   └── minio_storage.py    # MinIO/S3 实现
│   │   │   ├── logging/                # 结构化日志系统
│   │   │   │   ├── config.py           # LogConfig + ColoredFormatter + SmartExceptionFormatter
│   │   │   │   ├── core.py             # configure_logging() + get_logger() + log_response()
│   │   │   │   ├── context_filter.py   # RequestContextFilter（注入 request_id）
│   │   │   │   ├── early.py            # 启动早期日志（import 阶段使用）
│   │   │   │   ├── state.py            # LoggingPhase 枚举 + 状态管理
│   │   │   │   └── timing.py           # 慢请求计时装饰器
│   │   │   ├── exception/              # 异常体系
│   │   │   │   ├── base.py             # BusinessError + PermissionDeniedError + ResourceNotFoundError 等
│   │   │   │   └── business.py         # 业务异常重导出
│   │   │   ├── schema/                 # Schema 基础类
│   │   │   │   └── base.py             # AuditSchemaMixin + DateTimeStr + MetadataSchemaMixin + UIConfigSchemaMixin
│   │   │   ├── service/                # Service 基类
│   │   │   │   └── base_crud_service.py # BaseCRUDService[ModelType, SchemaType]（含钩子方法）
│   │   │   ├── model/                  # ORM Mixin 库
│   │   │   │   ├── audit_mixin.py      # TimestampMixin + AuditMixin
│   │   │   │   ├── fts_mixin.py        # FTSMixin（全文搜索 TSVector 自动更新）
│   │   │   │   ├── ui_config_mixin.py  # UIConfigMixin（icon + color 字段）
│   │   │   │   └── protocols.py        # ResourceEntity Protocol
│   │   │   ├── type/                   # 共享类型定义
│   │   │   │   ├── common.py           # JSONValue、JSONDict、StrObjectDict、Args、Kwargs
│   │   │   │   └── permissions.py      # Action、ResourceType、ResourceContext、ResourceFilterContext、Roles
│   │   │   └── utils/                  # 工具函数
│   │   │       ├── env.py              # EnvUtils（bool/int/str 环境变量读取）
│   │   │       ├── file.py             # 文件操作工具
│   │   │       ├── text.py             # tokenize_for_fts()（jieba 分词）
│   │   │       └── token.py            # Token 计数工具
│   │   └── pyproject.toml
│   │
│   ├── llm/                        # LLM 共享包
│   │   ├── src/llm/
│   │   │   ├── models/             # LLM 模型层
│   │   │   │   ├── llm_factory.py      # 多租户 LLM 工厂（多 Provider）
│   │   │   │   ├── prompt_executor.py  # PromptExecutor（执行器封装）
│   │   │   │   ├── callbacks.py        # LoggingCallbackHandler
│   │   │   │   ├── template.py         # Jinja2ChatPromptTemplate
│   │   │   │   ├── vlm_config_factory.py  # VLM 配置工厂
│   │   │   │   └── providers/          # Provider 实现
│   │   │   │       ├── base.py             # create_chat_model() 路由函数
│   │   │   │       ├── openai_compatible.py # OpenAI 兼容接口
│   │   │   │       ├── dashscope.py        # 阿里云 DashScope
│   │   │   │       └── ollama.py           # Ollama 本地模型
│   │   │   ├── chains/             # LangChain 链
│   │   │   │   ├── factory.py          # create_structured_output_chain()（with_structured_output）
│   │   │   │   └── llm_actions.py      # 通用 LLM 动作封装
│   │   │   ├── vector/             # 向量检索子系统
│   │   │   │   ├── embeddings/         # Embedding 客户端
│   │   │   │   │   ├── base.py             # BaseEmbedding 抽象
│   │   │   │   │   ├── dashscope.py        # DashScope Embedding
│   │   │   │   │   ├── volcengine.py       # 火山引擎 Embedding
│   │   │   │   │   └── factory.py          # get_embedding_client()
│   │   │   │   ├── rerankers/          # 重排序客户端
│   │   │   │   │   ├── base.py             # BaseReranker 抽象
│   │   │   │   │   ├── dashscope.py        # DashScope Reranker
│   │   │   │   │   ├── volcengine.py       # 火山引擎 Reranker
│   │   │   │   │   └── factory.py          # get_reranker_client()
│   │   │   │   ├── retrievers/         # 检索器
│   │   │   │   │   ├── vector.py           # 向量检索
│   │   │   │   │   ├── fts.py              # 全文检索
│   │   │   │   │   └── hybrid.py           # 混合检索
│   │   │   │   ├── fusion/             # 结果融合
│   │   │   │   │   └── strategies.py       # HybridSearchConfig + FusionStrategy（RRF 等）
│   │   │   │   ├── store/              # 向量存储
│   │   │   │   │   ├── vector_store.py     # VectorStore（pgvector + SQLAlchemy，Schema 隔离）
│   │   │   │   │   ├── metadata_filters.py # 元数据过滤
│   │   │   │   │   └── sqlalchemy_filters.py # SQLAlchemy 过滤构建器
│   │   │   │   ├── services/           # 向量服务
│   │   │   │   │   ├── base_vector_service.py  # BaseVectorService[ModelT]（DB 与向量库同步）
│   │   │   │   │   └── vector_crud_service.py  # 通用向量 CRUD 服务
│   │   │   │   └── mappers/            # 文档映射器
│   │   │   ├── prompt/             # 提示词系统
│   │   │   │   ├── environment.py      # Jinja2 环境 + render_template_string()
│   │   │   │   └── formatters.py       # 自定义过滤器（summarize_ai_payload 等）
│   │   │   └── observability/      # 可观测性
│   │   │       └── langsmith_handler.py  # LangSmith 追踪配置
│   │   └── pyproject.toml
│   │
│   └── knowledge/                  # 知识库共享包
│       ├── src/knowledge/
│       │   ├── model/              # 知识库领域模型
│       │   │   ├── knowledge_base.py   # KnowledgeBase（顶层容器）
│       │   │   ├── folder.py           # KnowledgeFolder（树形文件夹）
│       │   │   ├── knowledge.py        # Knowledge（文档）
│       │   │   ├── chunk.py            # KnowledgeChunk（分片，含 FTSMixin）
│       │   │   ├── section.py          # KnowledgeSection（结构感知分块）
│       │   │   └── batch_operation.py  # 批量操作模型
│       │   ├── repository/         # 知识库仓储层
│       │   │   ├── knowledge_base_repository.py  # KnowledgeBaseRepository
│       │   │   ├── folder_repository.py          # KnowledgeFolderRepository（含树形查询）
│       │   │   ├── knowledge_repository.py       # KnowledgeRepository（含权限过滤）
│       │   │   ├── chunk_repository.py           # KnowledgeChunkRepository
│       │   │   └── section_repository.py         # KnowledgeSectionRepository
│       │   ├── schema/             # 知识库 Schema
│       │   │   ├── retrieval.py        # RetrievedChunk + KnowledgeCitation
│       │   │   └── speech.py           # 演讲稿整理相关 Schema（大纲/精炼/润色/保存/扩写）
│       │   ├── exceptions.py           # 知识库异常定义
│       │   └── knowledge_config.py     # 知识库配置
│       └── pyproject.toml
│
├── .claude/                        # Claude Code 规范体系（核心）
│   ├── rules/                      # 开发规范（自动加载）
│   │   ├── principles.md           # 核心不可变原则
│   │   ├── workflow.md             # 任务执行工作流
│   │   ├── quality.md              # 代码质量标准
│   │   ├── git.md                  # Git 工作流 + 提交规范
│   │   ├── backend/
│   │   │   ├── python.md           # Python 后端规则
│   │   │   └── conventions.md      # 后端结构约定
│   │   └── frontend/
│   │       └── react.md            # React 前端规则
│   ├── skills/                     # 项目技能（按需调用）
│   │   ├── README.md
│   │   ├── enforcing-project-standards/
│   │   ├── running-project-tests/
│   │   ├── delivering-changes/
│   │   └── upgrading-dependencies/
│   ├── hooks/
│   │   └── code-guard.sh           # 编辑后自动 lint + type check
│   ├── settings.json
│   └── settings.local.json         # (gitignore)
│
├── docs/
│   ├── superpowers/
│   │   ├── specs/                  # 设计文档
│   │   └── plans/                  # 实现计划
│   ├── claude/                     # Claude 使用文档
│   │   ├── architecture.md         # Claude Code 架构说明
│   │   ├── cheatsheet.md           # 快速参考
│   │   └── customization.md        # 定制化指南
│   ├── backend/
│   │   ├── architecture.md         # 后端架构文档
│   │   └── dependency-injection.md # DI 容器模式
│   ├── frontend/
│   │   └── development.md          # 前端开发规范
│   └── index.md                    # 文档首页（VitePress）
│
├── CLAUDE.md                       # 项目入口指南
├── package.json                    # pnpm workspace 根
├── pyproject.toml                  # uv workspace 根
├── pnpm-workspace.yaml
└── .gitignore
```

---

## 4. 后端架构

### 4.1 请求链路

```
Client → CORS Middleware → Authentication Middleware → Log Middleware
       → API (@inject + Depends) → Service (session) → Repository → DB
       → CommonResponse[T] → Client
```

### 4.2 三层架构规则

| 层 | 位置 | 职责 | 关键规则 |
|---|------|------|---------|
| **API** | `domain/<name>/api/` | HTTP 路由处理 | `@inject` + `Depends(Provide["..."])` 注入 Service；`Depends(db_session)` 获取 Session；静态路由在参数化路由之前 |
| **Service** | `domain/<name>/service/` | 业务逻辑编排 | 构造器注入依赖；首参数 `session: AsyncSession`；写操作调用 `flush()`；不使用 `@inject` |
| **Repository** | `domain/<name>/repository/` | 数据访问 | Singleton 无状态；所有方法接收 `session`；不创建 Session、不 commit |
| **Model** | `domain/<name>/model/` | ORM 实体 | 数据库表定义 + Mixin |
| **Schema** | `domain/<name>/schema/` | 数据校验 | Pydantic 请求/响应 DTO |

### 4.3 Session/事务管理

- **HTTP 请求**：`db_session()` 依赖自动管理 begin → commit/rollback
- **后台任务**：`scoped_session(tenant)` 需手动 commit
- Service 层调用 `flush()` 确保数据可见，但不 commit
- Repository 层只执行查询，不管理任何事务

### 4.4 依赖注入

```python
# container.py — 扁平化单容器
class AppContainer(DeclarativeContainer):
    config = providers.Configuration()

    # Infrastructure
    database_registry = providers.Singleton(DatabaseRegistry)
    redis = providers.Singleton(RedisService)

    # Repository
    user_repository = providers.Singleton(UserRepository)

    # Service
    user_service = providers.Singleton(UserService, repository=user_repository)
```

容器启动时 wire 到 API 模块，API 端点通过 `@inject` + `Depends(Provide["..."])` 获取 Service。

### 4.5 通用工具（common/）

**response.py**
```python
class CommonResponse[T]:
    code: int           # 200, 400, 404, 500
    message: str
    data: T | None

# 构建函数
success_response(data, message="success") -> CommonResponse[T]
error_response(message) -> CommonResponse[None]
not_found_response(message) -> CommonResponse[None]
pageable_success_response(content, total, params) -> CommonResponse[PageResult[T]]
```

**pagination.py**
```python
class PageParams:
    page: int = 1       # ?page=1
    size: int = 10       # ?size=10

class PageResult[T]:
    content: list[T]
    total: int
    page: int
    size: int
    total_pages: int
```

**error_handler.py**
```python
@error_handler("操作名称")       # 异常 → HTTPException
@response_error_handler("操作名称")  # 异常 → CommonResponse
```

---

## 5. User Domain 详细设计

### 5.1 Model

```python
# domain/user/model/user.py
class User(Base, AuditMixin):
    __tablename__ = "bedrock_user"

    id: str                     # PK, UUID
    username: str               # 唯一，登录名
    display_name: str           # 显示名
    email: str | None           # 邮箱
    phone: str | None           # 手机号
    avatar: str | None          # 头像 URL
    status: str                 # active / disabled
    roles: list[str]            # 角色列表 (ARRAY)
    last_login_at: datetime | None
    # AuditMixin: created_at, updated_at, created_by, updated_by
```

### 5.2 Schema

```python
# domain/user/schema/user_schema.py
class UserSchema(BaseModel):       # 完整响应 DTO
class UserCreate(BaseModel):       # 创建：username, display_name, email, phone, roles
class UserUpdate(BaseModel):       # 更新：所有字段 optional
class UserQuery(BaseModel):        # 查询过滤：keyword, status, role
```

### 5.3 Repository

```python
# domain/user/repository/user_repository.py
class UserRepository(BaseRepository[User]):
    # 继承: get_by_id, get_all, create, update, delete, search_paged
    async def get_by_username(session, username) -> User | None
    async def get_by_email(session, email) -> User | None
```

### 5.4 Service

```python
# domain/user/service/user_service.py
class UserService:
    def __init__(self, repository: UserRepository)

    async def create_user(session, data: UserCreate) -> UserSchema
    async def get_user(session, user_id: str) -> UserSchema
    async def update_user(session, user_id: str, data: UserUpdate) -> UserSchema
    async def delete_user(session, user_id: str) -> bool
    async def search_users(session, query: UserQuery, page_params) -> tuple[list[UserSchema], int]
    async def toggle_status(session, user_id: str) -> UserSchema
```

### 5.5 API

```python
# domain/user/api/user.py
router = APIRouter(prefix="/users", tags=["用户管理"])

GET    /users                    # 分页查询（keyword, status, role 过滤）
POST   /users                    # 创建用户
GET    /users/{user_id}          # 获取单个用户
PUT    /users/{user_id}          # 更新用户
DELETE /users/{user_id}          # 删除用户
PUT    /users/{user_id}/status   # 启用/禁用
```

所有端点返回 `CommonResponse[T]`，使用 `@inject` + `Depends(Provide["user_service"])` + `Depends(db_session)`。

---

## 6. packages/core 基础设施

### 6.1 模块清单

| 模块 | 职责 |
|------|------|
| `database/base.py` | DeclarativeBase |
| `database/session.py` | `db_session()` HTTP 用、`scoped_session(tenant)` 后台用 |
| `database/identifier.py` | 租户 → PostgreSQL schema 映射 |
| `database/state.py` | DatabaseRegistry 引擎池管理 |
| `repository/base_repository.py` | `BaseRepository[T]` 泛型 CRUD（get_by_id / get_all / create / update / delete / search_paged） |
| `repository/pk_strategy.py` | 单一/复合主键支持 |
| `repository/specification.py` | SearchSpec 查询规约、PageRequest |
| `cache/base.py` | `CacheBackend` 抽象基类（get / set / delete / clear / exists） |
| `cache/memory.py` | 内存缓存实现（基于 dict + fnmatch 模式清除） |
| `cache/redis.py` | Redis 客户端初始化 |
| `cache/redis_service.py` | RedisService 实现 |
| `cache/factory.py` | 缓存后端工厂（根据配置返回 Memory 或 Redis） |
| `config/loader.py` | YAML 配置加载 + `BEDROCK_` 前缀环境变量覆盖 |
| `context/request.py` | RequestContext（tenant / username / roles / request_id），基于 contextvars |
| `storage/manager.py` | StorageService 工厂 |
| `storage/minio_storage.py` | MinIO/S3 实现（upload / download / delete / get_url） |
| `logging/config.py` | `LogConfig`（路径/格式/阈值常量）+ `ColoredFormatter`（Spring Boot 风格彩色输出）+ `SmartExceptionFormatter`（过滤三方库堆栈） |
| `logging/core.py` | `configure_logging()` / `get_logger()` / `get_startup_logger()` / `log_response()` |
| `logging/context_filter.py` | `RequestContextFilter`（将 request_id 注入所有日志记录） |
| `logging/early.py` | 启动早期（import 阶段）专用日志，早于 `configure_logging()` 调用 |
| `logging/state.py` | `LoggingPhase` 枚举 + 全局相位管理（避免重复初始化） |
| `logging/timing.py` | 慢请求/慢操作计时装饰器 |
| `exception/base.py` | `BusinessError` + `PermissionDeniedError` + `ResourceNotFoundError` + `ResourceAlreadyExistsError` + `FileParsingError` + `StorageError` |
| `exception/business.py` | `BusinessError` 重导出（方便上层引用） |
| `schema/base.py` | `AuditSchemaMixin`（created_at/updated_at/created_by/updated_by）+ `DateTimeStr`（datetime → ISO 字符串序列化）+ `MetadataSchemaMixin` + `UIConfigSchemaMixin` |
| `service/base_crud_service.py` | `BaseCRUDService[ModelType, SchemaType]`，含 `_before_create` / `_after_create` / `_before_update` / `_after_update` / `_before_delete` / `_after_delete` 钩子 |
| `model/audit_mixin.py` | `TimestampMixin`（仅时间戳）+ `AuditMixin`（继承前者，加 created_by/updated_by） |
| `model/fts_mixin.py` | `FTSMixin`（`fts_document` TSVector 列 + SQLAlchemy 事件自动更新） |
| `model/ui_config_mixin.py` | `UIConfigMixin`（`icon` + `color` 字段，面向前端可视化配置） |
| `model/protocols.py` | `ResourceEntity` Protocol（要求 `id: str`，供泛型路由工厂使用） |
| `type/__init__.py` | `SchemaType`（判别联合枚举）+ `DescribableSchema`（`to_llm_description_string()` 抽象）+ `TitleMixin` |
| `type/common.py` | `JSONValue` / `JSONDict` / `StrObjectDict` / `Args` / `Kwargs` |
| `type/permissions.py` | `Action` / `ResourceType` / `ResourceContext` / `ResourceFilterContext` / `Roles` + `is_admin()` / `normalize_roles()` |
| `utils/env.py` | `EnvUtils`（`get_bool` / `get_int` / `get_str` / `get_from_dict_or_env`） |
| `utils/file.py` | 文件操作工具（路径处理、MIME 检测等） |
| `utils/text.py` | `tokenize_for_fts()`（jieba 分词 + 停用词过滤，为 PostgreSQL FTS 准备） |
| `utils/token.py` | Token 计数工具（用于 LLM 调用前估算 token 数） |

### 6.2 AuditMixin 从 database/ 迁移到 model/

原始设计中 `AuditMixin` 位于 `database/base.py`，当前代码已将 ORM Mixin 独立到 `model/` 子模块：

| 旧位置 | 新位置 | 说明 |
|--------|--------|------|
| `database/base.py` 中的 `AuditMixin` | `model/audit_mixin.py` | 拆分为 `TimestampMixin` + `AuditMixin` |
| （无） | `model/fts_mixin.py` | 全文搜索 Mixin |
| （无） | `model/ui_config_mixin.py` | UI 配置 Mixin |
| （无） | `model/protocols.py` | 资源实体 Protocol |

---

## 7. packages/llm LLM 基础设施

### 7.1 模块概述

`packages/llm` 是与 AI 模型交互的共享基础设施包，封装多 Provider LLM 调用、向量检索和提示词渲染，供各 domain 按需引用。

### 7.2 models/ — LLM 模型层

| 文件 | 职责 |
|------|------|
| `llm_factory.py` | 多租户 LLM 工厂，根据租户 + 模块名称（`LLMModule` 枚举）路由到对应 ChatModel 实例；OpenAI 兼容类型内置 retry，其他类型通过 `with_retry()` 包装 |
| `prompt_executor.py` | `PromptExecutor`：统一的提示词执行器，组合 LLM + Jinja2 模板 |
| `callbacks.py` | `LoggingCallbackHandler`：LangChain 回调，记录 LLM 调用耗时和 token 使用 |
| `template.py` | `Jinja2ChatPromptTemplate`：LangChain `BaseChatPromptTemplate` 子类，支持 Jinja2 渲染 |
| `vlm_config_factory.py` | VLM（视觉语言模型）配置工厂 |
| `providers/base.py` | `create_chat_model()` 路由函数，根据 provider 名称分发到具体实现 |
| `providers/openai_compatible.py` | OpenAI 兼容接口（含 ChatOpenAI / AzureOpenAI） |
| `providers/dashscope.py` | 阿里云 DashScope（通义千问等） |
| `providers/ollama.py` | Ollama 本地模型 |

### 7.3 chains/ — LangChain 链

| 文件 | 职责 |
|------|------|
| `factory.py` | `create_structured_output_chain()`：使用 `with_structured_output()` 创建结构化输出链；OpenAI 自动使用 Function Calling，其他 Provider 降级到 JSON mode |
| `llm_actions.py` | 通用 LLM 动作封装（单次对话、批量调用等） |

### 7.4 vector/ — 向量检索子系统

#### embeddings/ — Embedding 客户端

| 文件 | 职责 |
|------|------|
| `base.py` | `BaseEmbedding` 抽象基类 |
| `dashscope.py` | DashScope Embedding（text-embedding-v3 等） |
| `volcengine.py` | 火山引擎 Embedding |
| `factory.py` | `get_embedding_client()` 工厂 |

#### rerankers/ — 重排序客户端

| 文件 | 职责 |
|------|------|
| `base.py` | `BaseReranker` 抽象基类 |
| `dashscope.py` | DashScope Reranker |
| `volcengine.py` | 火山引擎 Reranker |
| `factory.py` | `get_reranker_client()` 工厂 |

#### retrievers/ — 检索器

| 文件 | 职责 |
|------|------|
| `vector.py` | 纯向量检索（cosine / dot-product） |
| `fts.py` | 全文检索（PostgreSQL TSVector） |
| `hybrid.py` | 混合检索（向量 + 全文，通过 `RetrievalMode` 枚举控制） |

#### fusion/ — 结果融合

| 文件 | 职责 |
|------|------|
| `strategies.py` | `HybridSearchConfig` + `FusionStrategy`（RRF 倒排融合等多种策略） |

#### store/ — 向量存储

| 文件 | 职责 |
|------|------|
| `vector_store.py` | `VectorStore`：基于 pgvector + SQLAlchemy 的向量存储，支持 PostgreSQL Schema 隔离（多租户），提供 upsert / delete / similarity_search / hybrid_search |
| `metadata_filters.py` | 向量检索元数据过滤器定义 |
| `sqlalchemy_filters.py` | `SQLAlchemyFilterBuilder`：将元数据过滤条件转换为 SQLAlchemy WHERE 子句 |

#### services/ — 向量服务

| 文件 | 职责 |
|------|------|
| `base_vector_service.py` | `BaseVectorService[ModelT]`：抽象基类，封装业务模型与向量库的同步逻辑；子类实现 `_create_document_from_model()` |
| `vector_crud_service.py` | 通用向量 CRUD 服务，继承 BaseVectorService |

### 7.5 prompt/ — 提示词系统

| 文件 | 职责 |
|------|------|
| `environment.py` | `prompt_template_env`（预配置 Jinja2 环境实例）+ `render_template_string()` / `render_template_string_async()` |
| `formatters.py` | 自定义 Jinja2 过滤器：`summarize_ai_payload`、`format_filters_for_prompt`、`format_json_for_prompt` |

### 7.6 observability/ — 可观测性

| 文件 | 职责 |
|------|------|
| `langsmith_handler.py` | `configure_langsmith_tracing()`：配置 LangSmith 链路追踪（通过环境变量开关） |

---

## 8. packages/knowledge 知识库基础设施

### 8.1 模块概述

`packages/knowledge` 封装知识库的领域模型、仓储层和 Schema，实现三层知识组织架构（知识库 → 文件夹 → 文档 → 分片）。

### 8.2 model/ — 知识库领域模型

三层知识组织架构：

```
KnowledgeBase（知识库）
  └── KnowledgeFolder（文件夹，树形）
        └── Knowledge（文档）
              └── KnowledgeSection（结构感知分块，章节/段落）
                    └── KnowledgeChunk（分片，FTS + 向量检索基本单元）
```

| 模型 | 表名 | 说明 |
|------|------|------|
| `KnowledgeBase` | `bedrock_knowledge_base` | 顶层容器；含 `KnowledgeBaseType`（standard / personal）；通过 Casbin RBAC 管理权限 |
| `KnowledgeFolder` | `bedrock_knowledge_folder` | 树形文件夹；含 `parent_folder_id` 自引用外键 |
| `Knowledge` | `bedrock_knowledge` | 文档实体；含文件元数据（filename、file_size、content_type） |
| `KnowledgeSection` | `bedrock_knowledge_section` | 结构感知分块（章节/段落）；作为 Chunk 的上层聚合 |
| `KnowledgeChunk` | `bedrock_knowledge_chunk` | 分片，继承 `FTSMixin`；含 `start_char_index` / `end_char_index` 支持动态上下文扩展 |
| `batch_operation.py` | - | 批量操作辅助模型（任务追踪） |

### 8.3 repository/ — 知识库仓储层

| 仓储 | 关键能力 |
|------|---------|
| `KnowledgeBaseRepository` | 标准 CRUD + 按类型/所有者查询 |
| `KnowledgeFolderRepository` | `find_by_owner()` + `find_root_folders()` + 树形遍历 |
| `KnowledgeRepository` | 标准 CRUD + 权限过滤（`ResourceFilterContext`） |
| `KnowledgeChunkRepository` | 批量插入 + 按知识 ID / section ID 查询 |
| `KnowledgeSectionRepository` | 按知识 ID 查询 + 批量操作 |

### 8.4 schema/ — 知识库 Schema

| Schema | 说明 |
|--------|------|
| `retrieval.py` | `RetrievedChunk`（检索结果片段，含分数/来源/缩略图等字段）+ `KnowledgeCitation`（引用展示 Schema，提供 `from_chunk()` 工厂方法） |
| `speech.py` | 演讲稿整理三步向导 Schema：`OutlineItem` / `OutlineResponse`（大纲）、`RefineSegmentRequest/Response`（逐段精炼）、`PolishRequest/Response`（全局润色）、`SaveRequest/Response`（保存知识库）、`ExpandRequest`（扩写模式） |

---

## 9. 前端架构

### 9.1 目录组织

```
src/
├── app/           # 应用层：路由、布局、全局 Provider
├── features/      # 功能模块：按业务划分，每个模块包含 components/hooks/api/types
├── shared/        # 全局共享：hooks、工具函数、类型
└── styles/        # 设计系统：CSS 变量、设计 token
```

### 9.2 User 功能模块

| 页面/组件 | 说明 |
|-----------|------|
| UserTable | 用户列表，表格 + 搜索 + 状态/角色筛选 + 分页 |
| UserForm | 创建/编辑表单弹窗 |
| UserDetail | 用户详情侧边栏或弹窗 |
| 状态切换 | 启用/禁用 toggle |

### 9.3 前端规范

- React 19 + TypeScript 5.9，strict mode
- 禁止 `any` 类型、`@ts-ignore`、`eslint-disable`
- Hook 依赖必须完整
- 组件 >150 行考虑拆分
- shadcn/ui 作为组件基础，在 shared/components/ 中二次封装
- TanStack Query 管理服务端状态
- 设计 token 通过 CSS 变量定义，Tailwind 引用

---

## 10. `.claude/` 规范体系

### 10.1 rules/ — 开发规范

| 文件 | 内容 | 加载方式 |
|------|------|---------|
| `principles.md` | 核心原则：质量优先、先思考再编码、工具优先、DI > Factory > Inheritance | 全局自动加载 |
| `workflow.md` | 任务执行流：检索 → 澄清 → 定位 → 判断 → 说明计划 → 代码审查 | 全局自动加载 |
| `quality.md` | 质量标准：函数 >80 行拆分、>3 层嵌套重构、无 emoji 注释 | 全局自动加载 |
| `git.md` | Git 规范：worktree、commit emoji 类型、分支策略 | 全局自动加载 |
| `backend/python.md` | Python 规则：Pyright/Ruff 零错误、三层规则、import 约定、session 模式 | 条件加载（编辑后端文件时） |
| `backend/conventions.md` | 结构约定：目录放置规则、配置管理、API 端点清单 | 条件加载 |
| `frontend/react.md` | React 规则：禁止 any、strict mode、组件拆分、技术栈约束 | 条件加载（编辑前端文件时） |

### 10.2 skills/ — 项目技能

| 技能 | 用途 |
|------|------|
| `enforcing-project-standards` | 代码审计：plan 对齐、静态分析、架构检查、命名验证 |
| `running-project-tests` | 测试执行：测试金字塔、pytest fixture、智能选择 |
| `delivering-changes` | 交付流水线：preflight → lint → test → commit → PR |
| `upgrading-dependencies` | 依赖升级：前端 pnpm + 后端 pip 升级验证 |

### 10.3 hooks/code-guard.sh

编辑/写入文件后自动触发：
- Phase 1：Ruff format/check + Pyright（Python 文件）、ESLint（TypeScript 文件）
- Phase 2：文件修改追踪记录
- 退出码 2 表示有错误需修复，0 表示通过

### 10.4 settings.json

```json
{
  "permissions": {
    "allow": [
      "Bash(pnpm:*)", "Bash(python:*)", "Bash(pip:*)",
      "Bash(ruff:*)", "Bash(pyright:*)", "Bash(pytest:*)",
      "Bash(alembic:*)", "Bash(git:*)", "Bash(docker:*)"
    ]
  },
  "hooks": {
    "PostToolUse": [{
      "matcher": "Edit|Write",
      "command": ".claude/hooks/code-guard.sh \"$TOOL_INPUT\"",
      "timeout": 30000
    }]
  },
  "language": "zh-CN"
}
```

### 10.5 迁移策略

从 provider-aip 迁移时：
- 去除所有 `provider-aip`、`pharmbrain` 等旧公司/旧项目引用
- 去除 freeze scope 机制（code-guard.sh Phase 0）
- 保留通用的架构原则、工作流、质量标准、三层规则
- 配置前缀从 `PROVIDER_AIP_` 改为 `BEDROCK_`

---

## 11. CLAUDE.md 入口文件

内容包括：
1. 项目简介 — bedrock 是什么、公司级规范示例项目定位
2. 项目结构概览 — apps/backend、apps/frontend、packages/core
3. 后端架构 — 三层分层（API → Service → Repository）+ DI 容器模式
4. 前端架构 — features 组织 + shared 共享 + 设计系统
5. 快速启动命令
6. Rules 文件索引 — 自动加载 vs 条件加载
7. 文档引用 — 指向 docs/ 下的架构文档

---

## 12. 配置文件

### config.yaml（后端运行时配置）

```yaml
server:
  port: 8000
  name: bedrock

cache:
  backend: memory          # memory | redis

redis:
  host: localhost
  port: 6379

database:
  host: localhost
  port: 5432
  username: postgres
  password: postgres
  pool_size: 20
  max_overflow: 5

storage:
  backend: minio
  endpoint: localhost:9000
  access_key: minioadmin
  secret_key: minioadmin

tenants:
  default:
    database:
      name: bedrock
```

### .gitignore

覆盖：
- Python（__pycache__、.venv、dist、*.egg-info）
- Node（node_modules、dist、.vite）
- 环境文件（.env、.env.local）
- IDE（.idea、.vscode）
- OS（.DS_Store）
- Claude Code（.claude/state/、.claude/settings.local.json）
- Git worktree

---

## 13. 不在范围内

以下内容不在本次实现范围：

- `apps/backend` 内的 LLM/AI 业务逻辑（LangGraph 对话图、知识库 API 端点）— `packages/llm` 和 `packages/knowledge` 已作为共享包存在，具体业务域由上层应用自行实现
- SSE 流式事件端点
- 权限系统（Casbin RBAC）— `core/type/permissions.py` 已定义类型契约，具体 enforcer 配置由各应用负责
- Worker 后台任务服务
- 移动端（Flutter）
- 数据仓库（dbt / Cube.js）
- 文档转换服务（converter）
- HashiCorp Vault 密钥管理
- CI/CD 流水线配置
