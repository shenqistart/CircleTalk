# Bedrock 实现计划

> **状态：** 已完成
> **日期：** 2026-04-01

**目标：** 创建 bedrock 项目 — 公司级规范示例项目，展示后端三层架构、Claude Code 规范、前端设计系统，以及 LLM/知识库共享包。

**架构：** 采用 pnpm（前端）+ uv（Python）工作区的 Monorepo 结构。后端使用 FastAPI + SQLAlchemy async + dependency-injector，严格遵循 API → Service → Repository 分层。前端使用 React 19 + TypeScript + Tailwind + shadcn/ui。共享包包括 core（基础设施）、llm（LLM + 向量检索）、knowledge（知识库域模型）。`.claude/` 目录提供完整的开发规则、技能、钩子和配置。

**技术栈：** Python 3.13+, FastAPI, SQLAlchemy 2.0 async, dependency-injector, Alembic, PostgreSQL, Redis, MinIO, LangChain, LangGraph, pgvector, React 19, TypeScript 5.9, Vite, Tailwind CSS 4.x, shadcn/ui, TanStack Query, VitePress, pnpm, uv

**规格文档：** `docs/superpowers/specs/2026-04-01-bedrock-design.md`

---

## 文件结构

### 根目录

```
bedrock/
├── package.json                    # pnpm workspace root
├── pyproject.toml                  # uv workspace root
├── pnpm-workspace.yaml
├── .gitignore
├── CLAUDE.md
```

### packages/core

```
packages/core/
├── pyproject.toml
└── src/core/
    ├── __init__.py
    ├── database/
    │   ├── __init__.py
    │   ├── base.py                 # DeclarativeBase + AuditMixin
    │   ├── session.py              # db_session() + scoped_session()
    │   ├── identifier.py           # SQL identifier safety
    │   └── state.py                # DatabaseRegistry
    ├── repository/
    │   ├── __init__.py
    │   ├── base_repository.py      # BaseRepository[T]
    │   ├── pk_strategy.py          # PK strategies
    │   └── specification.py        # SearchSpec + PageRequest + PageResponse
    ├── cache/
    │   ├── __init__.py
    │   ├── backend.py              # CacheBackend 抽象层 + 工厂模式
    │   ├── memory.py               # MemoryCache
    │   ├── redis.py                # RedisCache
    │   └── redis_service.py        # RedisService
    ├── config/
    │   ├── __init__.py
    │   └── loader.py               # ConfigLoader
    ├── context/
    │   ├── __init__.py
    │   └── request.py              # RequestContext
    ├── exception/
    │   ├── __init__.py
    │   └── errors.py               # BusinessError、ResourceNotFoundError 等统一异常层次
    ├── logging/
    │   ├── __init__.py
    │   ├── config.py               # 日志配置（彩色输出、请求 ID 追踪）
    │   ├── filters.py              # 智能异常过滤
    │   └── timing.py               # 性能计时
    ├── model/
    │   ├── __init__.py
    │   └── mixins.py               # AuditMixin、FTSMixin、UIConfigMixin、ResourceEntity 协议
    ├── schema/
    │   ├── __init__.py
    │   └── mixins.py               # AuditSchemaMixin、DateTimeStr
    ├── service/
    │   ├── __init__.py
    │   └── base_crud_service.py    # BaseCRUDService + hooks 模式
    ├── storage/
    │   ├── __init__.py
    │   ├── manager.py              # StorageServiceRegistry
    │   └── minio_storage.py        # MinIOStorage
    ├── type/
    │   ├── __init__.py
    │   └── types.py                # SchemaType、DescribableSchema、权限类型、通用类型别名
    └── utils/
        ├── __init__.py
        ├── text.py                 # 中文分词工具
        └── token.py                # Token 工具
```

### packages/llm

```
packages/llm/
├── pyproject.toml
└── src/llm/
    ├── __init__.py
    ├── chains/
    │   └── structured.py           # 结构化输出链（自动 Provider 检测、JSON mode 降级）
    ├── models/
    │   ├── __init__.py
    │   ├── manager.py              # 多 Provider LLM 管理
    │   ├── providers/              # OpenAI、DashScope、VolcEngine、Ollama
    │   ├── engine.py               # Prompt 执行引擎
    │   └── callbacks.py            # 回调追踪
    ├── observability/
    │   └── langsmith.py            # LangSmith 追踪集成
    ├── prompt/
    │   └── jinja2_env.py           # Jinja2 模板环境
    └── vector/
        ├── __init__.py
        ├── embeddings/             # DashScope、VolcEngine 异步 Embedding
        ├── fusion/                 # RRF + 加权求和融合策略
        ├── rerankers/              # DashScope、VolcEngine 重排序
        ├── retrievers/             # 向量检索、全文检索、RRF 混合检索
        ├── services/               # VectorCRUDService 自动同步
        └── store/                  # PostgreSQL + pgvector 存储
```

### packages/knowledge

```
packages/knowledge/
├── pyproject.toml
└── src/knowledge/
    ├── __init__.py
    ├── model/
    │   ├── __init__.py
    │   └── models.py               # KnowledgeBase、Folder、Knowledge、Chunk、Section + 批量操作模型
    ├── repository/
    │   ├── __init__.py
    │   ├── knowledge_base_repository.py
    │   ├── folder_repository.py    # 树形操作支持
    │   ├── knowledge_repository.py
    │   ├── chunk_repository.py
    │   └── section_repository.py
    └── schema/
        ├── __init__.py
        ├── retrieval.py            # 检索结果 Schema
        └── speech.py               # 语音处理 Schema
```

### apps/backend

```
apps/backend/
├── pyproject.toml
├── config.yaml
├── Dockerfile
├── alembic.ini
├── alembic/
│   ├── env.py
│   └── versions/
└── src/backend/
    ├── __init__.py
    ├── main.py
    ├── container.py
    ├── common/
    │   ├── __init__.py
    │   ├── response.py
    │   ├── error_handler.py
    │   └── pagination.py
    └── domain/
        └── user/
            ├── __init__.py
            ├── api/
            │   ├── __init__.py
            │   └── user.py
            ├── service/
            │   ├── __init__.py
            │   └── user_service.py
            ├── repository/
            │   ├── __init__.py
            │   └── user_repository.py
            ├── model/
            │   ├── __init__.py
            │   └── user.py
            └── schema/
                ├── __init__.py
                └── user_schema.py
```

### apps/backend/tests

```
tests/
├── conftest.py
└── domain/
    └── user/
        ├── conftest.py
        ├── test_user_repository.py
        ├── test_user_service.py
        └── test_user_api.py
```

### apps/frontend

```
apps/frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tsconfig.app.json
├── tsconfig.node.json
├── eslint.config.js
├── components.json
├── index.html
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── index.css
    ├── app/
    │   ├── routes/
    │   │   └── index.tsx
    │   ├── layouts/
    │   │   └── AppLayout.tsx
    │   └── providers/
    │       ├── QueryProvider.tsx
    │       └── ThemeProvider.tsx
    ├── features/
    │   └── user/
    │       ├── components/
    │       │   ├── UserTable.tsx
    │       │   ├── UserForm.tsx
    │       │   └── UserStatusToggle.tsx
    │       ├── hooks/
    │       │   └── useUsers.ts
    │       ├── api/
    │       │   └── userApi.ts
    │       └── types/
    │           └── index.ts
    ├── shared/
    │   ├── components/
    │   │   └── ui/                 # shadcn/ui components
    │   ├── hooks/
    │   │   └── usePagination.ts
    │   ├── lib/
    │   │   ├── utils.ts
    │   │   └── request.ts
    │   └── types/
    │       └── api.ts
    └── styles/
        └── tokens/
            └── colors.css
```

### .claude/

```
.claude/
├── settings.json
├── rules/
│   ├── principles.md
│   ├── workflow.md
│   ├── quality.md
│   ├── git.md
│   ├── backend/
│   │   ├── python.md
│   │   └── conventions.md
│   └── frontend/
│       └── react.md
├── skills/
│   ├── README.md
│   ├── enforcing-project-standards/
│   │   ├── SKILL.md
│   │   ├── FILTERS.md
│   │   └── PATTERNS.md
│   ├── running-project-tests/
│   │   └── SKILL.md
│   ├── delivering-changes/
│   │   └── SKILL.md
│   └── upgrading-dependencies/
│       └── SKILL.md
└── hooks/
    └── code-guard.sh
```

### docs/

```
docs/
├── .vitepress/
│   └── config.ts                   # VitePress 文档站点配置
├── superpowers/
│   ├── specs/
│   │   └── 2026-04-01-bedrock-design.md
│   └── plans/
│       └── 2026-04-01-bedrock-implementation.md
├── backend/
│   ├── architecture.md
│   └── dependency-injection.md
├── claude/
│   ├── architecture.md             # Claude Code 架构解析
│   ├── quickref.md                 # 速查手册
│   └── customization.md            # 定制指南
└── frontend/
    └── development.md
```

---

## 任务 1：根目录项目脚手架

**文件：**
- Create: `package.json`
- Create: `pyproject.toml`
- Create: `pnpm-workspace.yaml`
- Create: `.gitignore`

- [ ] **Step 1: Create root package.json**

```json
{
  "name": "bedrock",
  "version": "1.0.0",
  "private": true,
  "description": "Company-level reference implementation project",
  "scripts": {
    "dev": "pnpm --parallel --filter './apps/*' dev",
    "dev:backend": "cd apps/backend && python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000",
    "dev:frontend": "pnpm --filter @bedrock/frontend dev",
    "lint": "pnpm --parallel --filter './apps/*' lint",
    "lint:backend": "cd apps/backend && ruff format src/ && ruff check --fix src/ && pyright src/",
    "lint:frontend": "pnpm --filter @bedrock/frontend lint",
    "test": "cd apps/backend && pytest",
    "build": "pnpm --filter @bedrock/frontend build"
  },
  "engines": {
    "node": ">=20.0.0"
  },
  "packageManager": "pnpm@9.0.0"
}
```

- [ ] **Step 2: Create root pyproject.toml**

```toml
[project]
name = "bedrock-workspace"
version = "0.1.0"
requires-python = ">=3.13"

[tool.uv.workspace]
members = ["packages/*", "apps/backend"]
```

- [ ] **Step 3: Create pnpm-workspace.yaml**

```yaml
packages:
  - 'apps/*'
  - 'packages/*'
```

- [ ] **Step 4: Create .gitignore**

```gitignore
# macOS
.DS_Store

# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
*.egg
dist/
build/
.eggs/
.venv/
venv/
*.so

# Node
node_modules/
dist/
.vite/
*.tsbuildinfo

# Environment
.env
.env.local
.env.*.local

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Logs
*.log
npm-debug.log*
pnpm-debug.log*

# Test
.coverage
htmlcov/
.pytest_cache/

# Claude Code
.claude/state/
.claude/settings.local.json

# Git worktree
.worktrees/
```

- [ ] **Step 5: Commit**

```bash
git add package.json pyproject.toml pnpm-workspace.yaml .gitignore
git commit -m "🔧 chores: scaffold root project configuration"
```

---

## 任务 2：packages/core — 数据库模块

**文件：**
- Create: `packages/core/pyproject.toml`
- Create: `packages/core/src/core/__init__.py`
- Create: `packages/core/src/core/database/__init__.py`
- Create: `packages/core/src/core/database/base.py`
- Create: `packages/core/src/core/database/identifier.py`
- Create: `packages/core/src/core/database/state.py`
- Create: `packages/core/src/core/database/session.py`

- [ ] **Step 1: Create packages/core/pyproject.toml**

```toml
[project]
name = "bedrock-core"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "sqlalchemy>=2.0",
    "sqlalchemy-utils>=0.42",
    "psycopg[binary]>=3.3",
    "redis>=7.0",
    "pydantic>=2.0",
    "alembic>=1.14",
    "minio>=7.0",
    "python-magic>=0.4",
    "pyyaml>=6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/core"]
```

- [ ] **Step 2: Create packages/core/src/core/__init__.py**

```python
"""Bedrock core infrastructure package."""
```

- [ ] **Step 3: Create packages/core/src/core/database/__init__.py**

```python
"""Database infrastructure: Base, session management, multi-tenant support."""

from core.database.base import AuditMixin, Base
from core.database.session import db_session, scoped_session
from core.database.state import DatabaseRegistry, database_registry

__all__ = [
    "AuditMixin",
    "Base",
    "DatabaseRegistry",
    "database_registry",
    "db_session",
    "scoped_session",
]
```

- [ ] **Step 4: Create packages/core/src/core/database/base.py**

```python
"""SQLAlchemy DeclarativeBase and common mixins."""

from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    def __init__(self, **kwargs: object) -> None:
        valid_columns = {c.key for c in self.__table__.columns}
        filtered = {k: v for k, v in kwargs.items() if k in valid_columns}
        super().__init__(**filtered)

    def to_dict(self) -> dict[str, object]:
        """Convert model instance to dictionary, excluding embedding fields."""
        return {
            c.key: getattr(self, c.key)
            for c in self.__table__.columns
            if not c.key.endswith("_embedding")
        }


class AuditMixin:
    """Mixin providing automatic audit timestamp and user tracking fields."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    created_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
```

- [ ] **Step 5: Create packages/core/src/core/database/identifier.py**

```python
"""PostgreSQL SQL identifier safety utilities."""

from psycopg import sql as psycopg_sql
from sqlalchemy import TextClause, text


def build_search_path_sql(schema: str) -> TextClause:
    """Build safe SET search_path statement using psycopg.sql.Identifier."""
    stmt = psycopg_sql.SQL("SET search_path TO {schema}").format(
        schema=psycopg_sql.Identifier(schema)
    )
    return text(stmt.as_string(None))  # type: ignore[arg-type]


def build_create_schema_sql(schema: str) -> TextClause:
    """Build safe CREATE SCHEMA IF NOT EXISTS statement."""
    stmt = psycopg_sql.SQL("CREATE SCHEMA IF NOT EXISTS {schema}").format(
        schema=psycopg_sql.Identifier(schema)
    )
    return text(stmt.as_string(None))  # type: ignore[arg-type]
```

- [ ] **Step 6: Create packages/core/src/core/database/state.py**

```python
"""Database engine and session factory registry for multi-tenant support."""

from typing import ClassVar

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker


class DatabaseRegistry:
    """Multi-tenant database resource registry (schema isolation mode).

    Manages shared engine, base session factory, and tenant-to-schema mapping.
    """

    _shared_engine: ClassVar[AsyncEngine | None] = None
    _base_session_factory: ClassVar[async_sessionmaker[AsyncSession] | None] = None
    _schema_mapping: ClassVar[dict[str, str]] = {}

    @classmethod
    def register_shared_engine(
        cls,
        engine: AsyncEngine,
        factory: async_sessionmaker[AsyncSession],
    ) -> None:
        cls._shared_engine = engine
        cls._base_session_factory = factory

    @classmethod
    def register_tenant_schema(cls, tenant: str, schema: str) -> None:
        cls._schema_mapping[tenant] = schema

    @classmethod
    def get_schema_name(cls, tenant: str) -> str:
        schema = cls._schema_mapping.get(tenant)
        if schema is None:
            msg = f"Unknown tenant: {tenant}. Registered: {list(cls._schema_mapping.keys())}"
            raise ValueError(msg)
        return schema

    @classmethod
    def get_engine(cls) -> AsyncEngine:
        if cls._shared_engine is None:
            msg = "Database engine not initialized. Call initialize_db_engines() first."
            raise RuntimeError(msg)
        return cls._shared_engine

    @classmethod
    def get_base_session_factory(cls) -> async_sessionmaker[AsyncSession]:
        if cls._base_session_factory is None:
            msg = "Session factory not initialized."
            raise RuntimeError(msg)
        return cls._base_session_factory

    @classmethod
    def schema_mapping(cls) -> dict[str, str]:
        return dict(cls._schema_mapping)

    @classmethod
    def clear(cls) -> None:
        cls._shared_engine = None
        cls._base_session_factory = None
        cls._schema_mapping.clear()


database_registry = DatabaseRegistry()
```

- [ ] **Step 7: Create packages/core/src/core/database/session.py**

```python
"""Async database session management with multi-tenant schema isolation."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from core.context.request import try_current_tenant
from core.database.identifier import build_search_path_sql
from core.database.state import DatabaseRegistry

logger = logging.getLogger(__name__)


async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator for HTTP/WebSocket request-scoped sessions.

    Automatically switches to tenant schema and manages transaction
    (begin -> commit on success, rollback on error).
    """
    factory = DatabaseRegistry.get_base_session_factory()
    async with factory() as session:
        tenant = try_current_tenant()
        if tenant:
            schema = DatabaseRegistry.get_schema_name(tenant)
            await session.execute(build_search_path_sql(schema))

        async with session.begin():
            yield session


@asynccontextmanager
async def scoped_session(tenant: str) -> AsyncGenerator[AsyncSession, None]:
    """Create an isolated session for background tasks / LangGraph nodes.

    Does NOT auto-commit. Write operations must explicitly call session.commit().
    """
    factory = DatabaseRegistry.get_base_session_factory()
    async with factory() as session:
        schema = DatabaseRegistry.get_schema_name(tenant)
        await session.execute(build_search_path_sql(schema))
        try:
            yield session
        finally:
            await session.close()
```

- [ ] **Step 8: Verify Python syntax**

Run: `cd /Users/yaoguohh/Work/bairong && python -c "import ast; [ast.parse(open(f).read()) for f in __import__('glob').glob('packages/core/src/core/database/*.py')]" && echo "OK"`

Expected: `OK`

- [ ] **Step 9: Commit**

```bash
git add packages/core/
git commit -m "✨ feat: add packages/core database module with multi-tenant support"
```

---

## 任务 3：packages/core — 仓储模块

**文件：**
- Create: `packages/core/src/core/repository/__init__.py`
- Create: `packages/core/src/core/repository/pk_strategy.py`
- Create: `packages/core/src/core/repository/specification.py`
- Create: `packages/core/src/core/repository/base_repository.py`

- [ ] **Step 1: Create packages/core/src/core/repository/__init__.py**

```python
"""Repository infrastructure: generic CRUD, PK strategies, query specifications."""

from core.repository.base_repository import BaseRepository
from core.repository.pk_strategy import CompositePKStrategy, SinglePKStrategy
from core.repository.specification import PageRequest, PageResponse, SearchSpec

__all__ = [
    "BaseRepository",
    "CompositePKStrategy",
    "PageRequest",
    "PageResponse",
    "SearchSpec",
    "SinglePKStrategy",
]
```

- [ ] **Step 2: Create packages/core/src/core/repository/pk_strategy.py**

```python
"""Primary key strategies for BaseRepository: single and composite PK support."""

from typing import Any, Protocol, Sequence

from sqlalchemy import ColumnElement, and_
from sqlalchemy.orm import DeclarativeBase


class PrimaryKeyStrategy(Protocol):
    """Unified interface for primary key operations."""

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]: ...
    def extract_pk_value(self, instance: DeclarativeBase) -> Any: ...
    def get_unique_fields(self) -> list[str]: ...
    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]: ...


class SinglePKStrategy:
    """Strategy for models with a single primary key field (default: 'id')."""

    def __init__(self, pk_field: str = "id") -> None:
        self.pk_field = pk_field

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]:
        column = getattr(model, self.pk_field)
        if isinstance(pk_value, (list, tuple)):
            msg = f"SinglePKStrategy expects scalar value, got {type(pk_value)}"
            raise TypeError(msg)
        return column == pk_value  # type: ignore[return-value]

    def extract_pk_value(self, instance: DeclarativeBase) -> Any:
        return getattr(instance, self.pk_field)

    def get_unique_fields(self) -> list[str]:
        return [self.pk_field]

    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]:
        return [getattr(model, self.pk_field).desc()]


class CompositePKStrategy:
    """Strategy for models with composite primary keys."""

    def __init__(self, pk_fields: Sequence[str]) -> None:
        if len(pk_fields) < 2:
            msg = "CompositePKStrategy requires at least 2 fields"
            raise ValueError(msg)
        self.pk_fields = list(pk_fields)

    def build_where_clause(self, model: type[DeclarativeBase], pk_value: Any) -> ColumnElement[bool]:
        if not isinstance(pk_value, (list, tuple)) or len(pk_value) != len(self.pk_fields):
            msg = f"Expected tuple of {len(self.pk_fields)} values"
            raise TypeError(msg)
        conditions = [
            getattr(model, field) == value
            for field, value in zip(self.pk_fields, pk_value, strict=True)
        ]
        return and_(*conditions)

    def extract_pk_value(self, instance: DeclarativeBase) -> tuple[Any, ...]:
        return tuple(getattr(instance, field) for field in self.pk_fields)

    def get_unique_fields(self) -> list[str]:
        return list(self.pk_fields)

    def get_default_order_by(self, model: type[DeclarativeBase]) -> list[ColumnElement[Any]]:
        return [getattr(model, self.pk_fields[0]).desc()]
```

- [ ] **Step 3: Create packages/core/src/core/repository/specification.py**

```python
"""Query specification pattern: SearchSpec, PageRequest, PageResponse."""

from dataclasses import dataclass, field
from math import ceil
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SearchSpec:
    """Query specification for filtering and searching."""

    filters: dict[str, Any] = field(default_factory=dict)
    query: str | None = None
    order_by: list[str] = field(default_factory=list)


@dataclass
class PageRequest:
    """Pagination request parameters."""

    page: int = 1
    size: int = 20
    sort: list[tuple[str, str]] | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            self.page = 1
        if self.size < 1:
            self.size = 1
        if self.size > 1000:
            self.size = 1000

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size


@dataclass
class PageResponse(Generic[T]):
    """Paginated response wrapper."""

    content: list[T]
    page: int
    size: int
    total: int

    @property
    def total_pages(self) -> int:
        return ceil(self.total / self.size) if self.size > 0 else 0

    @classmethod
    def from_query_result(
        cls,
        content: list[T],
        total: int,
        page: int,
        size: int,
    ) -> "PageResponse[T]":
        return cls(content=content, page=page, size=size, total=total)
```

- [ ] **Step 4: Create packages/core/src/core/repository/base_repository.py**

```python
"""Generic BaseRepository providing standard CRUD operations."""

import logging
from typing import Any, Generic, TypeVar

from sqlalchemy import Select, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.repository.pk_strategy import PrimaryKeyStrategy, SinglePKStrategy
from core.repository.specification import PageRequest, PageResponse, SearchSpec

ModelT = TypeVar("ModelT")
logger = logging.getLogger(__name__)


class BaseRepository(Generic[ModelT]):
    """Base repository with generic CRUD operations.

    All methods receive session explicitly. Never creates session, never commits.
    """

    def __init__(self, model_class: type[ModelT]) -> None:
        self._model_class = model_class

    def _get_pk_strategy(self) -> PrimaryKeyStrategy:
        return SinglePKStrategy(self._default_pk_field())

    def _default_pk_field(self) -> str:
        return "id"

    def _get_searchable_fields(self) -> list[str]:
        """Override in subclass to define fields for text search."""
        return []

    # --- Read operations ---

    async def get_by_id(self, session: AsyncSession, pk_value: Any) -> ModelT | None:
        strategy = self._get_pk_strategy()
        stmt = select(self._model_class).where(
            strategy.build_where_clause(self._model_class, pk_value)  # type: ignore[arg-type]
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()  # type: ignore[return-value]

    async def exists(self, session: AsyncSession, pk_value: Any) -> bool:
        return await self.get_by_id(session, pk_value) is not None

    async def get_by_ids(self, session: AsyncSession, pk_values: list[Any]) -> list[ModelT]:
        pk_field = self._get_pk_strategy().get_unique_fields()[0]
        column = getattr(self._model_class, pk_field)
        stmt = select(self._model_class).where(column.in_(pk_values))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def find_by(self, session: AsyncSession, **filters: Any) -> list[ModelT]:
        stmt = select(self._model_class)
        stmt = self._apply_kwargs_filters(stmt, filters)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def count_by(self, session: AsyncSession, **filters: Any) -> int:
        stmt = select(func.count()).select_from(self._model_class)
        stmt = self._apply_kwargs_filters(stmt, filters)
        result = await session.execute(stmt)
        return result.scalar_one()  # type: ignore[return-value]

    async def search_paged(
        self,
        session: AsyncSession,
        page: int = 1,
        size: int = 20,
        query: str | None = None,
        **filters: Any,
    ) -> tuple[list[ModelT], int]:
        """Paginated search with text search and exact filters."""
        stmt = select(self._model_class)
        count_stmt = select(func.count()).select_from(self._model_class)

        # Apply text search
        if query:
            search_conditions = self._build_text_search_filters(query)
            if search_conditions is not None:
                stmt = stmt.where(search_conditions)
                count_stmt = count_stmt.where(search_conditions)

        # Apply exact filters
        stmt = self._apply_kwargs_filters(stmt, filters)
        count_stmt = self._apply_kwargs_filters(count_stmt, filters)

        # Count
        total_result = await session.execute(count_stmt)
        total = total_result.scalar_one()  # type: ignore[assignment]

        # Apply sorting and pagination
        strategy = self._get_pk_strategy()
        stmt = stmt.order_by(*strategy.get_default_order_by(self._model_class))  # type: ignore[arg-type]
        stmt = stmt.offset((page - 1) * size).limit(size)

        result = await session.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    async def search_with_spec(
        self,
        session: AsyncSession,
        spec: SearchSpec,
        pageable: PageRequest,
    ) -> PageResponse[ModelT]:
        """Search using specification pattern."""
        items, total = await self.search_paged(
            session,
            page=pageable.page,
            size=pageable.size,
            query=spec.query,
            **spec.filters,
        )
        return PageResponse.from_query_result(items, total, pageable.page, pageable.size)

    # --- Write operations ---

    async def create(self, session: AsyncSession, data: dict[str, Any] | ModelT) -> ModelT:
        if isinstance(data, dict):
            instance = self._model_class(**data)  # type: ignore[call-arg]
        else:
            instance = data
        session.add(instance)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def update(
        self,
        session: AsyncSession,
        pk_value: Any,
        update_data: dict[str, Any],
    ) -> ModelT | None:
        instance = await self.get_by_id(session, pk_value)
        if instance is None:
            return None
        for key, value in update_data.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        await session.flush()
        await session.refresh(instance)
        return instance

    async def delete(self, session: AsyncSession, pk_value: Any) -> bool:
        instance = await self.get_by_id(session, pk_value)
        if instance is None:
            return False
        await session.delete(instance)
        await session.flush()
        return True

    async def create_batch(self, session: AsyncSession, data_list: list[dict[str, Any]]) -> list[ModelT]:
        instances = [self._model_class(**data) for data in data_list]  # type: ignore[call-arg]
        session.add_all(instances)
        await session.flush()
        return instances

    async def delete_batch(self, session: AsyncSession, pk_values: list[Any]) -> int:
        pk_field = self._get_pk_strategy().get_unique_fields()[0]
        column = getattr(self._model_class, pk_field)
        stmt = delete(self._model_class).where(column.in_(pk_values))
        result = await session.execute(stmt)
        await session.flush()
        return result.rowcount  # type: ignore[return-value]

    # --- Internal helpers ---

    def _build_text_search_filters(self, query: str) -> Any | None:
        fields = self._get_searchable_fields()
        if not fields:
            return None
        conditions = []
        for field_name in fields:
            column = getattr(self._model_class, field_name, None)
            if column is not None:
                conditions.append(column.ilike(f"%{query}%"))
        return or_(*conditions) if conditions else None

    def _apply_kwargs_filters(self, stmt: Select[Any], filters: dict[str, Any]) -> Select[Any]:
        for key, value in filters.items():
            if value is None:
                continue
            if key.endswith("__in"):
                column_name = key[:-4]
                column = getattr(self._model_class, column_name, None)
                if column is not None:
                    stmt = stmt.where(column.in_(value))
            else:
                column = getattr(self._model_class, key, None)
                if column is not None:
                    stmt = stmt.where(column == value)
        return stmt
```

- [ ] **Step 5: Verify syntax**

Run: `cd /Users/yaoguohh/Work/bairong && python -c "import ast; [ast.parse(open(f).read()) for f in __import__('glob').glob('packages/core/src/core/repository/*.py')]" && echo "OK"`

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add packages/core/src/core/repository/
git commit -m "✨ feat: add generic BaseRepository with CRUD, search, and pagination"
```

---

## 任务 4：packages/core — 缓存、配置、上下文、存储模块

**文件：**
- Create: `packages/core/src/core/cache/__init__.py`
- Create: `packages/core/src/core/cache/redis.py`
- Create: `packages/core/src/core/cache/redis_service.py`
- Create: `packages/core/src/core/config/__init__.py`
- Create: `packages/core/src/core/config/loader.py`
- Create: `packages/core/src/core/context/__init__.py`
- Create: `packages/core/src/core/context/request.py`
- Create: `packages/core/src/core/storage/__init__.py`
- Create: `packages/core/src/core/storage/manager.py`
- Create: `packages/core/src/core/storage/minio_storage.py`

- [ ] **Step 1: Create cache module**

`packages/core/src/core/cache/__init__.py`:
```python
"""Cache infrastructure: Redis client and service."""

from core.cache.redis_service import RedisService

__all__ = ["RedisService"]
```

`packages/core/src/core/cache/redis.py`:
```python
"""Redis cache backend implementation."""

import json
from typing import Any

import redis


class RedisCache:
    """Redis-backed cache with JSON serialization."""

    def __init__(self, redis_client: redis.Redis[str]) -> None:
        self._client = redis_client

    async def get(self, key: str) -> Any | None:
        value = self._client.get(key)
        if value is None:
            return None
        return json.loads(value)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        serialized = json.dumps(value, ensure_ascii=False, default=str)
        if ttl:
            self._client.setex(key, ttl, serialized)
        else:
            self._client.set(key, serialized)

    async def delete(self, key: str) -> None:
        self._client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(self._client.exists(key))

    async def clear(self, pattern: str | None = None) -> None:
        if pattern is None:
            self._client.flushdb()
        else:
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
```

`packages/core/src/core/cache/redis_service.py`:
```python
"""Redis connection management and tenant-aware key operations."""

import logging
from functools import lru_cache
from typing import Any, AsyncGenerator

import redis.asyncio as aioredis

from core.context.request import try_current_tenant

logger = logging.getLogger(__name__)


class RedisService:
    """Redis service with tenant-isolated key prefixing."""

    def __init__(self, db: int | None = None) -> None:
        self._db = db or 0
        self._client: aioredis.Redis[str] | None = None

    def _initialize_client(self) -> aioredis.Redis[str]:
        from core.config.loader import ConfigLoader

        config = ConfigLoader.load()
        redis_config = config.get("redis", {})
        pool = aioredis.ConnectionPool(
            host=redis_config.get("host", "localhost"),
            port=redis_config.get("port", 6379),
            password=redis_config.get("password"),
            db=self._db,
            max_connections=20,
            decode_responses=True,
            health_check_interval=30,
        )
        return aioredis.Redis(connection_pool=pool)

    def _get_client(self) -> aioredis.Redis[str]:
        if self._client is None:
            self._client = self._initialize_client()
        return self._client

    def _build_key(self, key: str) -> str:
        tenant = try_current_tenant()
        if tenant:
            return f"{tenant}:{key}"
        return key

    def get_client(self) -> aioredis.Redis[str]:
        return self._get_client()

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        await self._get_client().set(self._build_key(key), value, ex=ex)

    async def get(self, key: str) -> str | None:
        return await self._get_client().get(self._build_key(key))  # type: ignore[return-value]

    async def delete(self, *keys: str) -> None:
        prefixed = [self._build_key(k) for k in keys]
        await self._get_client().delete(*prefixed)

    async def expire(self, key: str, time: int) -> None:
        await self._get_client().expire(self._build_key(key), time)

    async def scan_iter(self, match: str) -> AsyncGenerator[str, None]:
        async for key in self._get_client().scan_iter(match=self._build_key(match)):
            yield key  # type: ignore[misc]

    async def delete_by_pattern(self, pattern: str) -> None:
        keys_to_delete: list[str] = []
        async for key in self.scan_iter(pattern):
            keys_to_delete.append(key)
        if keys_to_delete:
            await self._get_client().delete(*keys_to_delete)

    async def close(self) -> None:
        if self._client:
            await self._client.close()


@lru_cache(maxsize=1)
def redis_service() -> RedisService:
    return RedisService()
```

- [ ] **Step 2: Create config module**

`packages/core/src/core/config/__init__.py`:
```python
"""Configuration loading infrastructure."""

from core.config.loader import ConfigLoader

__all__ = ["ConfigLoader"]
```

`packages/core/src/core/config/loader.py`:
```python
"""Configuration loader: YAML files with environment variable overrides."""

import logging
import os
from pathlib import Path
from typing import Any, ClassVar

import yaml

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Load configuration from YAML with environment variable override support.

    Priority: Environment variables > config.yaml
    Environment variables use BEDROCK_ prefix (e.g., BEDROCK_DATABASE_HOST).
    """

    _config: ClassVar[dict[str, Any] | None] = None

    @classmethod
    def load(cls) -> dict[str, Any]:
        if cls._config is not None:
            return cls._config
        cls._config = cls._load_yaml_config()
        return cls._config

    @classmethod
    def reload(cls) -> dict[str, Any]:
        cls._config = None
        return cls.load()

    @classmethod
    def _load_yaml_config(cls) -> dict[str, Any]:
        config_path = cls._resolve_config_path("config.yaml")
        if config_path is None:
            logger.warning("config.yaml not found, using empty config")
            return {}
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}
        logger.info("Loaded config from %s", config_path)
        return config

    @classmethod
    def _resolve_config_path(cls, filename: str) -> Path | None:
        env_path = os.environ.get("CONFIG_PATH")
        if env_path:
            p = Path(env_path)
            return p if p.exists() else None

        current = Path.cwd()
        candidate = current / filename
        if candidate.exists():
            return candidate

        for parent in current.parents:
            candidate = parent / filename
            if candidate.exists():
                return candidate
            if (parent / ".git").exists():
                break

        return None
```

- [ ] **Step 3: Create context module**

`packages/core/src/core/context/__init__.py`:
```python
"""Request context management via contextvars."""

from core.context.request import (
    RequestContext,
    RequestContextParams,
    clear_request_context,
    current_tenant,
    current_username,
    current_user_roles,
    get_request_context,
    set_request_context,
    try_current_tenant,
)

__all__ = [
    "RequestContext",
    "RequestContextParams",
    "clear_request_context",
    "current_tenant",
    "current_user_roles",
    "current_username",
    "get_request_context",
    "set_request_context",
    "try_current_tenant",
]
```

`packages/core/src/core/context/request.py`:
```python
"""Request context providing tenant, user, and role information via contextvars."""

from contextvars import ContextVar
from dataclasses import dataclass, field


@dataclass
class RequestContextParams:
    """Parameters for setting request context."""

    tenant: str
    username: str
    roles: list[str] = field(default_factory=list)
    request_id: str = ""


@dataclass
class RequestContext:
    """Immutable request context accessible throughout the request lifecycle."""

    tenant: str
    username: str
    roles: list[str]
    request_id: str

    def to_dict(self) -> dict[str, object]:
        return {
            "tenant": self.tenant,
            "username": self.username,
            "roles": self.roles,
            "request_id": self.request_id,
        }


_request_context: ContextVar[RequestContext | None] = ContextVar(
    "_request_context", default=None
)


def set_request_context(params: RequestContextParams) -> None:
    ctx = RequestContext(
        tenant=params.tenant,
        username=params.username,
        roles=params.roles,
        request_id=params.request_id,
    )
    _request_context.set(ctx)


def get_request_context() -> RequestContext:
    ctx = _request_context.get()
    if ctx is None:
        msg = "Request context not set. Are you inside an HTTP request?"
        raise RuntimeError(msg)
    return ctx


def try_current_tenant() -> str | None:
    ctx = _request_context.get()
    return ctx.tenant if ctx else None


def current_tenant() -> str:
    return get_request_context().tenant


def current_username() -> str:
    return get_request_context().username


def current_user_roles() -> list[str]:
    return get_request_context().roles


def clear_request_context() -> None:
    _request_context.set(None)
```

- [ ] **Step 4: Create storage module**

`packages/core/src/core/storage/__init__.py`:
```python
"""Object storage infrastructure."""

from core.storage.manager import StorageServiceRegistry, initialize_storage, storage_service

__all__ = ["StorageServiceRegistry", "initialize_storage", "storage_service"]
```

`packages/core/src/core/storage/manager.py`:
```python
"""Storage service singleton registry."""

import logging
from typing import Any, ClassVar, Protocol

logger = logging.getLogger(__name__)


class StorageService(Protocol):
    """Storage service interface."""

    async def upload_file(self, file_path: str, file_content: bytes, content_type: str = "application/octet-stream", metadata: dict[str, str] | None = None) -> str: ...
    async def download_file(self, file_path: str) -> bytes: ...
    async def delete_file(self, file_path: str) -> None: ...
    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str: ...
    async def file_exists(self, file_path: str) -> bool: ...


class StorageServiceRegistry:
    """Storage service singleton registry."""

    _instance: ClassVar[StorageService | None] = None

    @classmethod
    async def initialize(cls, config: dict[str, Any]) -> None:
        backend = config.get("backend", "minio")
        if backend == "minio":
            from core.storage.minio_storage import MinIOStorage

            cls._instance = MinIOStorage(config)
            await cls._instance.ensure_bucket()  # type: ignore[attr-defined]
        else:
            msg = f"Unsupported storage backend: {backend}"
            raise NotImplementedError(msg)
        logger.info("Storage service initialized: %s", backend)

    @classmethod
    def get(cls) -> StorageService:
        if cls._instance is None:
            msg = "Storage service not initialized. Call initialize() first."
            raise RuntimeError(msg)
        return cls._instance


async def initialize_storage(config: dict[str, Any]) -> None:
    await StorageServiceRegistry.initialize(config)


def storage_service() -> StorageService:
    return StorageServiceRegistry.get()
```

`packages/core/src/core/storage/minio_storage.py`:
```python
"""MinIO/S3-compatible object storage implementation."""

import io
import logging
from typing import Any

from minio import Minio

logger = logging.getLogger(__name__)


class MinIOStorage:
    """MinIO storage service implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        self._bucket = config.get("bucket", "bedrock")
        secure = config.get("secure", False)
        self.client = Minio(
            endpoint=config.get("endpoint", "localhost:9000"),
            access_key=config.get("access_key", "minioadmin"),
            secret_key=config.get("secret_key", "minioadmin"),
            secure=secure,
        )

    async def ensure_bucket(self) -> None:
        if not self.client.bucket_exists(self._bucket):
            self.client.make_bucket(self._bucket)
            logger.info("Created bucket: %s", self._bucket)

    async def upload_file(
        self,
        file_path: str,
        file_content: bytes,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        data = io.BytesIO(file_content)
        self.client.put_object(
            self._bucket,
            file_path,
            data,
            length=len(file_content),
            content_type=content_type,
            metadata=metadata,
        )
        return file_path

    async def download_file(self, file_path: str) -> bytes:
        response = self.client.get_object(self._bucket, file_path)
        try:
            return response.read()
        finally:
            response.close()
            response.release_conn()

    async def delete_file(self, file_path: str) -> None:
        self.client.remove_object(self._bucket, file_path)

    async def get_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        from datetime import timedelta

        return self.client.presigned_get_object(
            self._bucket,
            file_path,
            expires=timedelta(seconds=expires_in),
        )

    async def file_exists(self, file_path: str) -> bool:
        try:
            self.client.stat_object(self._bucket, file_path)
            return True
        except Exception:
            return False

    async def get_file_metadata(self, file_path: str) -> dict[str, Any]:
        stat = self.client.stat_object(self._bucket, file_path)
        return {
            "size": stat.size,
            "etag": stat.etag,
            "content_type": stat.content_type,
            "last_modified": stat.last_modified,
            "metadata": stat.metadata,
        }
```

- [ ] **Step 5: Verify all core modules syntax**

Run: `cd /Users/yaoguohh/Work/bairong && python -c "import ast, glob; files = glob.glob('packages/core/src/core/**/*.py', recursive=True); [ast.parse(open(f).read()) for f in files]; print(f'{len(files)} files OK')"``

Expected: `N files OK`

- [ ] **Step 6: Commit**

```bash
git add packages/core/src/core/cache/ packages/core/src/core/config/ packages/core/src/core/context/ packages/core/src/core/storage/
git commit -m "✨ feat: add cache, config, context, and storage core modules"
```

---

## 任务 5：apps/backend — 项目配置与通用工具

**文件：**
- Create: `apps/backend/pyproject.toml`
- Create: `apps/backend/config.yaml`
- Create: `apps/backend/Dockerfile`
- Create: `apps/backend/src/backend/__init__.py`
- Create: `apps/backend/src/backend/common/__init__.py`
- Create: `apps/backend/src/backend/common/response.py`
- Create: `apps/backend/src/backend/common/error_handler.py`
- Create: `apps/backend/src/backend/common/pagination.py`

- [ ] **Step 1: Create apps/backend/pyproject.toml**

```toml
[project]
name = "bedrock-backend"
version = "0.1.0"
requires-python = ">=3.13"
dependencies = [
    "bedrock-core",
    "fastapi==0.135.1",
    "uvicorn[standard]==0.41.0",
    "sqlalchemy==2.0.48",
    "alembic==1.18.4",
    "psycopg[binary]==3.3.3",
    "redis==7.1.0",
    "minio==7.2.20",
    "dependency-injector==4.48.3",
    "pydantic==2.12.5",
    "orjson==3.11.7",
    "pyyaml==6.0.3",
]

[dependency-groups]
dev = [
    "pyright>=1.1.400",
    "pytest>=9.0",
    "pytest-asyncio>=0.25",
    "httpx>=0.28",
    "ruff>=0.15",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/backend"]

[tool.ruff]
target-version = "py313"
line-length = 120
src = ["src"]

[tool.ruff.lint]
select = ["E", "W", "F", "B", "SIM", "I", "UP", "S", "RUF"]
ignore = ["S101", "B008"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "S106"]

[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "standard"
venvPath = "."
venv = ".venv"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 2: Create apps/backend/config.yaml**

```yaml
server:
  port: 8000
  name: bedrock

cache:
  backend: memory

redis:
  host: localhost
  port: 6379
  password: null

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
  bucket: bedrock

tenants:
  default:
    database:
      name: bedrock
```

- [ ] **Step 3: Create apps/backend/Dockerfile**

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src

RUN uv pip install --system -e packages/core -e apps/backend

COPY apps/backend/src apps/backend/src
COPY apps/backend/config.yaml apps/backend/config.yaml
COPY apps/backend/alembic apps/backend/alembic
COPY apps/backend/alembic.ini apps/backend/alembic.ini

WORKDIR /app/apps/backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create common __init__ files**

`apps/backend/src/backend/__init__.py`:
```python
"""Bedrock backend application."""
```

`apps/backend/src/backend/common/__init__.py`:
```python
"""Common utilities: response wrappers, error handlers, pagination."""
```

- [ ] **Step 5: Create apps/backend/src/backend/common/response.py**

```python
"""Standardized API response wrappers."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CommonResponse(BaseModel, Generic[T]):
    """Standard API response envelope."""

    code: int = 200
    message: str = "success"
    data: T | None = None


def success_response(data: Any = None, message: str = "success") -> CommonResponse[Any]:
    return CommonResponse(code=200, message=message, data=data)


def error_response(message: str, code: int = 500) -> CommonResponse[None]:
    return CommonResponse(code=code, message=message, data=None)


def not_found_response(message: str = "Resource not found") -> CommonResponse[None]:
    return CommonResponse(code=404, message=message, data=None)


def bad_request_response(message: str) -> CommonResponse[None]:
    return CommonResponse(code=400, message=message, data=None)


def pageable_success_response(
    content: list[Any],
    total: int,
    page: int,
    size: int,
    message: str = "success",
) -> CommonResponse[dict[str, Any]]:
    """Build paginated success response."""
    from math import ceil

    return CommonResponse(
        code=200,
        message=message,
        data={
            "content": content,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": ceil(total / size) if size > 0 else 0,
        },
    )
```

- [ ] **Step 6: Create apps/backend/src/backend/common/error_handler.py**

```python
"""Exception handling decorators for API endpoints."""

import logging
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from fastapi import HTTPException

from backend.common.response import CommonResponse, error_response

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def error_handler(operation: str) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]],
    Callable[P, Coroutine[Any, Any, R]],
]:
    """Decorator that converts exceptions to HTTPException."""

    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                raise
            except ValueError as e:
                logger.warning("%s failed: %s", operation, e)
                raise HTTPException(status_code=400, detail=str(e)) from e
            except Exception as e:
                logger.exception("%s error: %s", operation, e)
                raise HTTPException(status_code=500, detail=f"{operation}失败") from e

        return wrapper

    return decorator


def response_error_handler(operation: str) -> Callable[
    [Callable[P, Coroutine[Any, Any, CommonResponse[Any]]]],
    Callable[P, Coroutine[Any, Any, CommonResponse[Any]]],
]:
    """Decorator that converts exceptions to CommonResponse error format."""

    def decorator(
        func: Callable[P, Coroutine[Any, Any, CommonResponse[Any]]],
    ) -> Callable[P, Coroutine[Any, Any, CommonResponse[Any]]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> CommonResponse[Any]:
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                logger.warning("%s failed: %s", operation, e)
                return error_response(str(e), code=400)
            except Exception as e:
                logger.exception("%s error: %s", operation, e)
                return error_response(f"{operation}失败")

        return wrapper

    return decorator
```

- [ ] **Step 7: Create apps/backend/src/backend/common/pagination.py**

```python
"""Pagination models for FastAPI query parameters and responses."""

from math import ceil
from typing import Any, Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PageParams:
    """FastAPI Depends class for pagination query parameters."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(10, ge=1, le=100, description="Items per page"),
    ) -> None:
        self.page = page
        self.size = size


class PageResult(BaseModel, Generic[T]):
    """Generic paginated response model."""

    content: list[T]
    total: int
    page: int
    size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        content: list[Any],
        total: int,
        page: int,
        size: int,
    ) -> "PageResult[Any]":
        return cls(
            content=content,
            total=total,
            page=page,
            size=size,
            total_pages=ceil(total / size) if size > 0 else 0,
        )
```

- [ ] **Step 8: Commit**

```bash
git add apps/backend/
git commit -m "✨ feat: add backend project config and common utilities"
```

---

## 任务 6：apps/backend — 用户域（模型 + 数据结构 + 仓储）

**文件：**
- Create: `apps/backend/src/backend/domain/__init__.py`
- Create: `apps/backend/src/backend/domain/user/__init__.py`
- Create: `apps/backend/src/backend/domain/user/model/__init__.py`
- Create: `apps/backend/src/backend/domain/user/model/user.py`
- Create: `apps/backend/src/backend/domain/user/schema/__init__.py`
- Create: `apps/backend/src/backend/domain/user/schema/user_schema.py`
- Create: `apps/backend/src/backend/domain/user/repository/__init__.py`
- Create: `apps/backend/src/backend/domain/user/repository/user_repository.py`

- [ ] **Step 1: Create domain __init__ files**

`apps/backend/src/backend/domain/__init__.py`:
```python
"""Business domains."""
```

`apps/backend/src/backend/domain/user/__init__.py`:
```python
"""User management domain."""
```

- [ ] **Step 2: Create User model**

`apps/backend/src/backend/domain/user/model/__init__.py`:
```python
from backend.domain.user.model.user import User

__all__ = ["User"]
```

`apps/backend/src/backend/domain/user/model/user.py`:
```python
"""User ORM model."""

from datetime import datetime

from sqlalchemy import ARRAY, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database.base import AuditMixin, Base


class User(Base, AuditMixin):
    """User entity for the bedrock platform."""

    __tablename__ = "bedrock_user"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", index=True)
    roles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
```

- [ ] **Step 3: Create User schemas**

`apps/backend/src/backend/domain/user/schema/__init__.py`:
```python
from backend.domain.user.schema.user_schema import UserCreate, UserQuery, UserSchema, UserUpdate

__all__ = ["UserCreate", "UserQuery", "UserSchema", "UserUpdate"]
```

`apps/backend/src/backend/domain/user/schema/user_schema.py`:
```python
"""User Pydantic schemas for request/response validation."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    """Complete user response DTO."""

    id: str
    username: str
    display_name: str
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    status: str
    roles: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    created_by: str | None = None
    updated_by: str | None = None

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """User creation request."""

    username: str = Field(min_length=2, max_length=100)
    display_name: str = Field(min_length=1, max_length=255)
    email: str | None = None
    phone: str | None = None
    roles: list[str] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """User update request (all fields optional)."""

    display_name: str | None = None
    email: str | None = None
    phone: str | None = None
    avatar: str | None = None
    roles: list[str] | None = None


class UserQuery(BaseModel):
    """User search/filter parameters."""

    keyword: str | None = None
    status: str | None = None
    role: str | None = None
```

- [ ] **Step 4: Create User repository**

`apps/backend/src/backend/domain/user/repository/__init__.py`:
```python
from backend.domain.user.repository.user_repository import UserRepository

__all__ = ["UserRepository"]
```

`apps/backend/src/backend/domain/user/repository/user_repository.py`:
```python
"""User data access layer."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.user.model.user import User
from core.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User entity. Singleton, stateless."""

    def __init__(self) -> None:
        super().__init__(User)

    def _get_searchable_fields(self) -> list[str]:
        return ["username", "display_name", "email", "phone"]

    async def get_by_username(self, session: AsyncSession, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
```

- [ ] **Step 5: Commit**

```bash
git add apps/backend/src/backend/domain/
git commit -m "✨ feat: add User domain model, schema, and repository"
```

---

## 任务 7：apps/backend — 用户域（服务 + API）

**文件：**
- Create: `apps/backend/src/backend/domain/user/service/__init__.py`
- Create: `apps/backend/src/backend/domain/user/service/user_service.py`
- Create: `apps/backend/src/backend/domain/user/api/__init__.py`
- Create: `apps/backend/src/backend/domain/user/api/user.py`

- [ ] **Step 1: Create User service**

`apps/backend/src/backend/domain/user/service/__init__.py`:
```python
from backend.domain.user.service.user_service import UserService

__all__ = ["UserService"]
```

`apps/backend/src/backend/domain/user/service/user_service.py`:
```python
"""User business logic layer."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.user.model.user import User
from backend.domain.user.repository.user_repository import UserRepository
from backend.domain.user.schema.user_schema import UserCreate, UserSchema, UserUpdate
from core.context.request import current_username


class UserService:
    """Orchestrates user operations. Constructor-injected dependencies."""

    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def create_user(self, session: AsyncSession, data: UserCreate) -> UserSchema:
        existing = await self._repository.get_by_username(session, data.username)
        if existing is not None:
            msg = f"Username '{data.username}' already exists"
            raise ValueError(msg)

        user_data = {
            "id": str(uuid.uuid4()),
            "username": data.username,
            "display_name": data.display_name,
            "email": data.email,
            "phone": data.phone,
            "roles": data.roles,
            "status": "active",
            "created_by": current_username(),
            "updated_by": current_username(),
        }
        user = await self._repository.create(session, user_data)
        return UserSchema.model_validate(user)

    async def get_user(self, session: AsyncSession, user_id: str) -> UserSchema | None:
        user = await self._repository.get_by_id(session, user_id)
        if user is None:
            return None
        return UserSchema.model_validate(user)

    async def update_user(
        self,
        session: AsyncSession,
        user_id: str,
        data: UserUpdate,
    ) -> UserSchema | None:
        update_data = data.model_dump(exclude_unset=True)
        update_data["updated_by"] = current_username()
        user = await self._repository.update(session, user_id, update_data)
        if user is None:
            return None
        return UserSchema.model_validate(user)

    async def delete_user(self, session: AsyncSession, user_id: str) -> bool:
        return await self._repository.delete(session, user_id)

    async def search_users(
        self,
        session: AsyncSession,
        keyword: str | None = None,
        status: str | None = None,
        role: str | None = None,
        page: int = 1,
        size: int = 10,
    ) -> tuple[list[UserSchema], int]:
        filters: dict[str, str] = {}
        if status:
            filters["status"] = status

        users, total = await self._repository.search_paged(
            session,
            page=page,
            size=size,
            query=keyword,
            **filters,
        )
        schemas = [UserSchema.model_validate(u) for u in users]
        return schemas, total

    async def toggle_status(self, session: AsyncSession, user_id: str) -> UserSchema | None:
        user = await self._repository.get_by_id(session, user_id)
        if user is None:
            return None
        new_status = "disabled" if user.status == "active" else "active"
        updated = await self._repository.update(
            session,
            user_id,
            {"status": new_status, "updated_by": current_username()},
        )
        if updated is None:
            return None
        return UserSchema.model_validate(updated)
```

- [ ] **Step 2: Create User API**

`apps/backend/src/backend/domain/user/api/__init__.py`:
```python
from backend.domain.user.api.user import router as user_router

__all__ = ["user_router"]
```

`apps/backend/src/backend/domain/user/api/user.py`:
```python
"""User management REST API endpoints."""

from typing import Annotated, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.common.error_handler import error_handler
from backend.common.pagination import PageParams
from backend.common.response import (
    CommonResponse,
    not_found_response,
    pageable_success_response,
    success_response,
)
from backend.domain.user.schema.user_schema import UserCreate, UserUpdate
from backend.domain.user.service.user_service import UserService
from core.database.session import db_session

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get("")
@inject
@error_handler("search users")
async def search_users(
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
    pagination: Annotated[PageParams, Depends()],
    keyword: str | None = Query(None, description="Search keyword"),
    status: str | None = Query(None, description="Filter by status"),
    role: str | None = Query(None, description="Filter by role"),
) -> CommonResponse[Any]:
    users, total = await user_service.search_users(
        session,
        keyword=keyword,
        status=status,
        role=role,
        page=pagination.page,
        size=pagination.size,
    )
    return pageable_success_response(
        content=[u.model_dump() for u in users],
        total=total,
        page=pagination.page,
        size=pagination.size,
    )


@router.post("")
@inject
@error_handler("create user")
async def create_user(
    user_data: UserCreate,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.create_user(session, user_data)
    return success_response(user.model_dump())


@router.get("/{user_id}")
@inject
@error_handler("get user")
async def get_user(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.get_user(session, user_id)
    if user is None:
        return not_found_response("User not found")
    return success_response(user.model_dump())


@router.put("/{user_id}")
@inject
@error_handler("update user")
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.update_user(session, user_id, user_data)
    if user is None:
        return not_found_response("User not found")
    return success_response(user.model_dump())


@router.delete("/{user_id}")
@inject
@error_handler("delete user")
async def delete_user(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    deleted = await user_service.delete_user(session, user_id)
    if not deleted:
        return not_found_response("User not found")
    return success_response(message="User deleted")


@router.put("/{user_id}/status")
@inject
@error_handler("toggle user status")
async def toggle_user_status(
    user_id: str,
    user_service: Annotated[UserService, Depends(Provide["user_service"])],
    session: Annotated[AsyncSession, Depends(db_session)],
) -> CommonResponse[Any]:
    user = await user_service.toggle_status(session, user_id)
    if user is None:
        return not_found_response("User not found")
    return success_response(user.model_dump())
```

- [ ] **Step 3: Commit**

```bash
git add apps/backend/src/backend/domain/user/service/ apps/backend/src/backend/domain/user/api/
git commit -m "✨ feat: add User service and API endpoints"
```

---

## 任务 8：apps/backend — 容器 + 主入口 + 数据迁移

**文件：**
- Create: `apps/backend/src/backend/container.py`
- Create: `apps/backend/src/backend/main.py`
- Create: `apps/backend/alembic.ini`
- Create: `apps/backend/alembic/env.py`
- Create: `apps/backend/alembic/versions/.gitkeep`

- [ ] **Step 1: Create DI container**

`apps/backend/src/backend/container.py`:
```python
"""Flat dependency injection container for the bedrock application."""

from dependency_injector import containers, providers

from backend.domain.user.repository.user_repository import UserRepository
from backend.domain.user.service.user_service import UserService


class AppContainer(containers.DeclarativeContainer):
    """Root DI container. All providers are flat — no sub-containers."""

    config = providers.Configuration()

    # --- Repository ---
    user_repository = providers.Singleton(UserRepository)

    # --- Service ---
    user_service = providers.Singleton(UserService, repository=user_repository)
```

- [ ] **Step 2: Create main.py**

`apps/backend/src/backend/main.py`:
```python
"""FastAPI application entry point."""

import logging
import uuid
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.container import AppContainer
from backend.domain.user.api import user_router
from core.config.loader import ConfigLoader
from core.context.request import (
    RequestContextParams,
    clear_request_context,
    set_request_context,
)
from core.database.state import DatabaseRegistry

logger = logging.getLogger(__name__)


async def initialize_db_engines(config: dict) -> None:
    """Stage 1: Initialize database engines and register tenant schemas."""
    db_config = config.get("database", {})
    tenants = config.get("tenants", {})

    db_name = list(tenants.values())[0].get("database", {}).get("name", "bedrock") if tenants else "bedrock"
    url = (
        f"postgresql+psycopg://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )

    engine = create_async_engine(
        url,
        pool_size=db_config.get("pool_size", 20),
        max_overflow=db_config.get("max_overflow", 5),
        echo=False,
    )

    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    DatabaseRegistry.register_shared_engine(engine, factory)

    for tenant_name, tenant_config in tenants.items():
        schema = tenant_config.get("database", {}).get("name", tenant_name)
        DatabaseRegistry.register_tenant_schema(tenant_name, schema)
        logger.info("Registered tenant: %s -> schema: %s", tenant_name, schema)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    config = ConfigLoader.load()

    # Stage 1: Database
    await initialize_db_engines(config)
    logger.info("Database engines initialized")

    # Wire DI container
    container = AppContainer()
    container.wire(modules=["backend.domain.user.api.user"])
    app.state.container = container

    logger.info("Bedrock backend started on port %s", config.get("server", {}).get("port", 8000))

    yield

    # Shutdown
    engine = DatabaseRegistry.get_engine()
    await engine.dispose()
    DatabaseRegistry.clear()
    logger.info("Bedrock backend shut down")


app = FastAPI(
    title="Bedrock API",
    description="Company-level reference implementation backend",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """Set request context (tenant, user) for each request."""
    # Default tenant and user for demo; in production, extract from JWT
    set_request_context(
        RequestContextParams(
            tenant="default",
            username=request.headers.get("X-Username", "anonymous"),
            roles=request.headers.get("X-Roles", "").split(",") if request.headers.get("X-Roles") else [],
            request_id=str(uuid.uuid4()),
        )
    )
    try:
        response = await call_next(request)
        return response
    finally:
        clear_request_context()


@app.middleware("http")
async def log_requests_middleware(request: Request, call_next) -> Response:
    """Log request method, path, and response status."""
    import time

    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info("%s %s -> %d (%.1fms)", request.method, request.url.path, response.status_code, elapsed)
    return response


# Register routers
app.include_router(user_router, prefix="/api")


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "bedrock"}
```

- [ ] **Step 3: Create Alembic configuration**

`apps/backend/alembic.ini`:
```ini
[alembic]
script_location = alembic
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

`apps/backend/alembic/env.py`:
```python
"""Alembic migration environment with multi-tenant schema support."""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from core.config.loader import ConfigLoader
from core.database.base import Base

# Import all models so Alembic can detect them
from backend.domain.user.model.user import User  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    app_config = ConfigLoader.load()
    db_config = app_config.get("database", {})
    tenants = app_config.get("tenants", {})
    tenant = os.environ.get("ALEMBIC_TENANT", "default")
    db_name = tenants.get(tenant, {}).get("database", {}).get("name", "bedrock")
    return (
        f"postgresql+psycopg://{db_config.get('username', 'postgres')}"
        f":{db_config.get('password', 'postgres')}"
        f"@{db_config.get('host', 'localhost')}"
        f":{db_config.get('port', 5432)}"
        f"/{db_name}"
    )


def run_migrations_offline() -> None:
    context.configure(url=get_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(get_url())
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 4: Create versions directory**

```bash
mkdir -p apps/backend/alembic/versions
touch apps/backend/alembic/versions/.gitkeep
```

- [ ] **Step 5: Commit**

```bash
git add apps/backend/src/backend/container.py apps/backend/src/backend/main.py apps/backend/alembic.ini apps/backend/alembic/
git commit -m "✨ feat: add DI container, FastAPI main entry, and Alembic migration setup"
```

---

## 任务 9：apps/backend — 测试

**文件：**
- Create: `apps/backend/tests/conftest.py`
- Create: `apps/backend/tests/domain/__init__.py`
- Create: `apps/backend/tests/domain/user/__init__.py`
- Create: `apps/backend/tests/domain/user/conftest.py`
- Create: `apps/backend/tests/domain/user/test_user_service.py`
- Create: `apps/backend/tests/domain/user/test_user_api.py`

- [ ] **Step 1: Create test infrastructure**

`apps/backend/tests/conftest.py`:
```python
"""Global test fixtures."""
```

`apps/backend/tests/domain/__init__.py`:
```python
```

`apps/backend/tests/domain/user/__init__.py`:
```python
```

`apps/backend/tests/domain/user/conftest.py`:
```python
"""User domain test fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.domain.user.repository.user_repository import UserRepository
from backend.domain.user.service.user_service import UserService


@pytest.fixture
def mock_session() -> AsyncMock:
    session = AsyncMock()
    session.flush = AsyncMock()
    session.refresh = AsyncMock()
    return session


@pytest.fixture
def mock_user_repository() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(mock_user_repository: MagicMock) -> UserService:
    return UserService(repository=mock_user_repository)
```

- [ ] **Step 2: Create service tests**

`apps/backend/tests/domain/user/test_user_service.py`:
```python
"""Unit tests for UserService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.domain.user.schema.user_schema import UserCreate, UserUpdate
from backend.domain.user.service.user_service import UserService


@pytest.mark.asyncio
async def test_create_user_success(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_username = AsyncMock(return_value=None)

    mock_user = MagicMock()
    mock_user.id = "test-uuid"
    mock_user.username = "johndoe"
    mock_user.display_name = "John Doe"
    mock_user.email = "john@example.com"
    mock_user.phone = None
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.roles = ["user"]
    mock_user.last_login_at = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.created_by = "admin"
    mock_user.updated_by = "admin"
    mock_user_repository.create = AsyncMock(return_value=mock_user)

    with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
        result = await user_service.create_user(
            mock_session,
            UserCreate(username="johndoe", display_name="John Doe", email="john@example.com", roles=["user"]),
        )

    assert result.username == "johndoe"
    assert result.display_name == "John Doe"
    mock_user_repository.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_user_duplicate_username(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_username = AsyncMock(return_value=MagicMock())

    with pytest.raises(ValueError, match="already exists"):
        with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
            await user_service.create_user(
                mock_session,
                UserCreate(username="existing", display_name="Existing User"),
            )


@pytest.mark.asyncio
async def test_get_user_found(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user = MagicMock()
    mock_user.id = "user-1"
    mock_user.username = "johndoe"
    mock_user.display_name = "John Doe"
    mock_user.email = None
    mock_user.phone = None
    mock_user.avatar = None
    mock_user.status = "active"
    mock_user.roles = []
    mock_user.last_login_at = None
    mock_user.created_at = None
    mock_user.updated_at = None
    mock_user.created_by = None
    mock_user.updated_by = None
    mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)

    result = await user_service.get_user(mock_session, "user-1")
    assert result is not None
    assert result.username == "johndoe"


@pytest.mark.asyncio
async def test_get_user_not_found(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user_repository.get_by_id = AsyncMock(return_value=None)
    result = await user_service.get_user(mock_session, "nonexistent")
    assert result is None


@pytest.mark.asyncio
async def test_toggle_status(
    user_service: UserService,
    mock_user_repository: MagicMock,
    mock_session: AsyncMock,
) -> None:
    mock_user = MagicMock()
    mock_user.status = "active"
    mock_user_repository.get_by_id = AsyncMock(return_value=mock_user)

    toggled_user = MagicMock()
    toggled_user.id = "user-1"
    toggled_user.username = "johndoe"
    toggled_user.display_name = "John"
    toggled_user.email = None
    toggled_user.phone = None
    toggled_user.avatar = None
    toggled_user.status = "disabled"
    toggled_user.roles = []
    toggled_user.last_login_at = None
    toggled_user.created_at = None
    toggled_user.updated_at = None
    toggled_user.created_by = None
    toggled_user.updated_by = None
    mock_user_repository.update = AsyncMock(return_value=toggled_user)

    with patch("backend.domain.user.service.user_service.current_username", return_value="admin"):
        result = await user_service.toggle_status(mock_session, "user-1")

    assert result is not None
    assert result.status == "disabled"
    mock_user_repository.update.assert_called_once()
```

- [ ] **Step 3: Create API tests**

`apps/backend/tests/domain/user/test_user_api.py`:
```python
"""Integration tests for User API endpoints using httpx."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from backend.domain.user.schema.user_schema import UserSchema


@pytest.fixture
def mock_user_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
async def client(mock_user_service: MagicMock):
    from backend.container import AppContainer
    from backend.main import app

    container = AppContainer()
    container.user_service.override(mock_user_service)
    container.wire(modules=["backend.domain.user.api.user"])

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    container.unwire()


@pytest.mark.asyncio
async def test_search_users(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.search_users = AsyncMock(return_value=([], 0))

    response = await client.get("/api/users")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["content"] == []
    assert data["data"]["total"] == 0


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.create_user = AsyncMock(
        return_value=UserSchema(
            id="test-id",
            username="newuser",
            display_name="New User",
            status="active",
            roles=["user"],
        )
    )

    response = await client.post(
        "/api/users",
        json={"username": "newuser", "display_name": "New User", "roles": ["user"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "newuser"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, mock_user_service: MagicMock) -> None:
    mock_user_service.get_user = AsyncMock(return_value=None)

    response = await client.get("/api/users/nonexistent")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 404


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

- [ ] **Step 4: Commit**

```bash
git add apps/backend/tests/
git commit -m "🐞 test: add User domain unit and API integration tests"
```

---

## 任务 10：.claude/ — 开发规则

**文件：**
- Create: `.claude/rules/principles.md`
- Create: `.claude/rules/workflow.md`
- Create: `.claude/rules/quality.md`
- Create: `.claude/rules/git.md`
- Create: `.claude/rules/backend/python.md`
- Create: `.claude/rules/backend/conventions.md`
- Create: `.claude/rules/frontend/react.md`

Due to the volume of these files, each is adapted from existing项目规范 with all旧项目引用 and business-specific references removed.

- [ ] **Step 1: Create core rules (principles, workflow, quality, git)**

Create all four files with content adapted from the source. Key changes:
- Remove all旧项目引用
- Remove LangGraph/Chat/Knowledge specific mentions
- Replace paths with `bedrock` equivalents
- Remove Harbor registry references from git.md
- Update `.envrc` paths in git.md to use bedrock project root
- Keep all architecture principles, quality standards, and workflow intact

- [ ] **Step 2: Create backend rules (python.md, conventions.md)**

Key changes:
- `python.md`: Remove `from llm.xxx` import reference; keep `from domain.xxx`, `from core.xxx`; remove chat-graph and knowledge docs references; update doc references to bedrock paths
- `conventions.md`: Replace domain examples with `user`; remove chat/knowledge/analytics specific domains; keep directory placement rules, config management, and API endpoint checklist

- [ ] **Step 3: Create frontend rules (react.md)**

Key changes:
- Remove `apps/console/` path reference (bedrock only has frontend)
- Keep all React 19 + TypeScript + shadcn/ui conventions
- Update doc references

- [ ] **Step 4: Commit**

```bash
git add .claude/rules/
git commit -m "📔 docs: add Claude Code development rules migrated for bedrock"
```

---

## 任务 11：.claude/ — 项目技能

**文件：**
- Create: `.claude/skills/README.md`
- Create: `.claude/skills/enforcing-project-standards/SKILL.md`
- Create: `.claude/skills/enforcing-project-standards/FILTERS.md`
- Create: `.claude/skills/enforcing-project-standards/PATTERNS.md`
- Create: `.claude/skills/running-project-tests/SKILL.md`
- Create: `.claude/skills/delivering-changes/SKILL.md`
- Create: `.claude/skills/upgrading-dependencies/SKILL.md`

- [ ] **Step 1: Create skills README and enforcing-project-standards**

Migrate from existing standards. Key changes:
- `README.md`: Remove旧项目 skill references; list 4 retained skills
- `SKILL.md`: Remove Flutter checks; remove LangGraph/Chat specific architecture checks; keep Python/TypeScript/React checks
- `FILTERS.md`: Keep as-is (generic filtering rules)
- `PATTERNS.md`: Remove Flutter sections; remove旧项目 specific domain examples; keep SOLID, naming conventions, React patterns, layered architecture checks

- [ ] **Step 2: Create running-project-tests skill**

Key changes:
- Remove E2E chat test examples
- Replace with User domain test examples
- Update test directory paths
- Keep test pyramid structure and fixture patterns

- [ ] **Step 3: Create delivering-changes and upgrading-dependencies skills**

Key changes:
- `delivering-changes`: Replace ruff/pyright paths; remove Harbor deployment references
- `upgrading-dependencies`: Keep as-is (generic upgrade flow)

- [ ] **Step 4: Commit**

```bash
git add .claude/skills/
git commit -m "📔 docs: add Claude Code project skills for bedrock"
```

---

## 任务 12：.claude/ — 钩子 + 配置

**文件：**
- Create: `.claude/hooks/code-guard.sh`
- Create: `.claude/settings.json`

- [ ] **Step 1: Create code-guard.sh**

Migrate from existing standards. Key changes:
- Remove Phase 0 (freeze scope detection) — bedrock doesn't need scoped editing
- Keep Phase 1: Ruff format/check + Pyright for Python; ESLint for TypeScript
- Keep Phase 2: File modification tracking
- Update paths from `apps/backend/src` to match bedrock structure
- Make the script executable

```bash
chmod +x .claude/hooks/code-guard.sh
```

- [ ] **Step 2: Create settings.json**

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(pnpm:*)",
      "Bash(python:*)",
      "Bash(pip:*)",
      "Bash(uv:*)",
      "Bash(ruff:*)",
      "Bash(pyright:*)",
      "Bash(pytest:*)",
      "Bash(alembic:*)",
      "Bash(git:*)",
      "Bash(docker:*)",
      "Bash(npm:*)",
      "Bash(npx:*)",
      "Bash(ls:*)",
      "Bash(mkdir:*)",
      "Bash(cp:*)",
      "Bash(mv:*)",
      "Bash(cat:*)",
      "Bash(echo:*)",
      "Bash(curl:*)",
      "WebSearch",
      "WebFetch"
    ]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "command": ".claude/hooks/code-guard.sh \"$TOOL_INPUT\"",
        "timeout": 30000
      }
    ]
  },
  "enabledPlugins": [
    "code-review",
    "code-simplifier"
  ],
  "language": "zh-CN"
}
```

- [ ] **Step 3: Commit**

```bash
git add .claude/hooks/ .claude/settings.json
git commit -m "🔧 chores: add Claude Code hooks and settings configuration"
```

---

## 任务 13：CLAUDE.md + 文档

**文件：**
- Create: `CLAUDE.md`
- Create: `docs/backend/architecture.md`
- Create: `docs/backend/dependency-injection.md`
- Create: `docs/frontend/development.md`

- [ ] **Step 1: Create CLAUDE.md**

```markdown
# Bedrock

公司级规范示例项目，所有子服务的规范源头、学习入口和设计语言参考。

## 项目结构

```
bedrock/
├── apps/
│   ├── backend/          # FastAPI Python 后端 (8000)
│   └── frontend/         # React TypeScript 前端 (5173)
├── packages/
│   └── core/             # 共享基础设施（database、cache、config、context、storage）
├── .claude/              # Claude Code 规范体系
│   ├── rules/            # 开发规范（自动加载）
│   ├── skills/           # 项目技能（按需调用）
│   └── hooks/            # 代码守卫
└── docs/                 # 项目文档
```

## 快速启动

```bash
# 后端
cd apps/backend && python -m uvicorn backend.main:app --reload --port 8000

# 前端
pnpm --filter @bedrock/frontend dev

# 全栈
pnpm dev
```

## 后端架构

三层分层：API → Service → Repository

- **API**: `@inject` + `Depends(Provide["..."])` 注入 Service；`Depends(db_session)` 获取 Session
- **Service**: 构造器注入依赖；首参 `session: AsyncSession`；写操作调用 `flush()`
- **Repository**: Singleton 无状态；显式接收 `session`；不创建 Session、不 commit

示例域：`apps/backend/src/backend/domain/user/`

## 前端架构

- `features/` 按业务组织（components/hooks/api/types）
- `shared/` 全局共享（UI 组件、hooks、工具函数）
- `styles/` 设计系统（CSS 变量、设计 token）

## Rules 文件索引

| 文件 | 内容 | 加载方式 |
|------|------|---------|
| `principles.md` | 核心原则 | 全局 |
| `workflow.md` | 任务执行流 | 全局 |
| `quality.md` | 质量标准 | 全局 |
| `git.md` | Git 规范 | 全局 |
| `backend/python.md` | Python 规则 | 条件（编辑后端文件时） |
| `backend/conventions.md` | 结构约定 | 条件 |
| `frontend/react.md` | React 规则 | 条件（编辑前端文件时） |

## 文档

- 后端架构：@docs/backend/architecture.md
- 依赖注入：@docs/backend/dependency-injection.md
- 前端开发：@docs/frontend/development.md
```

- [ ] **Step 2: Create backend architecture doc**

Migrate `docs/backend/architecture.md` from existing standards:
- Remove all旧项目 references
- Remove LLM/Chat/Knowledge/Analytics domain examples
- Replace with User domain examples
- Keep request chain, 3-layer rules, session strategy, DI pattern, API routing rules
- Update import paths to bedrock conventions

- [ ] **Step 3: Create backend DI doc**

Migrate `docs/backend/dependency-injection.md` from existing standards:
- Simplify container examples to show User domain only
- Remove ChatService/ChatServiceDependencies Factory examples
- Keep core principles, session strategy, layering rules, common pitfalls

- [ ] **Step 4: Create frontend development doc**

Write a new doc covering:
- Tech stack (React 19, TypeScript 5.9, Tailwind 4, shadcn/ui)
- Project structure (app/features/shared/styles)
- Component conventions
- API request pattern (TanStack Query + axios)
- Type safety rules
- Design token usage

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md docs/backend/ docs/frontend/
git commit -m "📔 docs: add CLAUDE.md and backend/frontend architecture documentation"
```

---

## 任务 14：apps/frontend — 项目初始化

**文件：**
- Create: `apps/frontend/package.json`
- Create: `apps/frontend/vite.config.ts`
- Create: `apps/frontend/tsconfig.json`
- Create: `apps/frontend/tsconfig.app.json`
- Create: `apps/frontend/tsconfig.node.json`
- Create: `apps/frontend/eslint.config.js`
- Create: `apps/frontend/components.json`
- Create: `apps/frontend/index.html`

- [ ] **Step 1: Create package.json**

```json
{
  "name": "@bedrock/frontend",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint ."
  },
  "dependencies": {
    "@radix-ui/react-alert-dialog": "^1.1.15",
    "@radix-ui/react-avatar": "^1.1.11",
    "@radix-ui/react-dialog": "^1.1.15",
    "@radix-ui/react-dropdown-menu": "^2.1.16",
    "@radix-ui/react-label": "^2.1.8",
    "@radix-ui/react-popover": "^1.1.15",
    "@radix-ui/react-select": "^2.2.6",
    "@radix-ui/react-separator": "^1.1.8",
    "@radix-ui/react-slot": "^1.2.4",
    "@radix-ui/react-switch": "^1.2.6",
    "@radix-ui/react-tabs": "^1.1.13",
    "@radix-ui/react-toast": "^1.2.15",
    "@radix-ui/react-tooltip": "^1.2.8",
    "@tanstack/react-query": "^5.62.0",
    "axios": "^1.13.5",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "framer-motion": "^12.34.3",
    "lucide-react": "^0.575.0",
    "react": "^19.2.4",
    "react-dom": "^19.2.4",
    "react-hook-form": "^7.71.2",
    "react-router-dom": "^7.13.1",
    "sonner": "^2.0.7",
    "tailwind-merge": "^3.5.0",
    "zod": "^4.3.6"
  },
  "devDependencies": {
    "@eslint/js": "^10.0.1",
    "@tailwindcss/vite": "^4.2.1",
    "@types/node": "^25.3.0",
    "@types/react": "^19.2.14",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.4",
    "eslint": "^10.0.2",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.5.2",
    "globals": "^17.3.0",
    "tailwindcss": "^4.2.1",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.56.1",
    "vite": "^7.3.1"
  }
}
```

- [ ] **Step 2: Create vite.config.ts**

```typescript
import * as path from 'node:path'
import { fileURLToPath } from 'node:url'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { defineConfig } from 'vite'

const moduleUrl = (import.meta as unknown as { url: string }).url
const srcDir = path.resolve(path.dirname(fileURLToPath(moduleUrl)), 'src')

export default defineConfig({
  plugins: [tailwindcss(), react()],
  resolve: {
    alias: {
      '@': srcDir,
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    sourcemap: false,
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['lucide-react', '@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu', '@radix-ui/react-select'],
          'animation': ['framer-motion'],
        },
      },
    },
  },
})
```

- [ ] **Step 3: Create TypeScript configs**

`tsconfig.json`:
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

`tsconfig.app.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "useDefineForClassFields": true,
    "lib": ["ES2023", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "types": ["vite/client", "react", "react-dom", "node"],
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "useUnknownInCatchVariables": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitOverride": true,
    "noPropertyAccessFromIndexSignature": true,
    "allowUnusedLabels": false,
    "allowUnreachableCode": false,
    "resolveJsonModule": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "verbatimModuleSyntax": true
  },
  "include": ["src"]
}
```

`tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "types": ["node", "vite/client"],
    "baseUrl": ".",
    "paths": { "@/*": ["./src/*"] },
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create eslint.config.js and components.json**

`eslint.config.js`:
```javascript
import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'

export default tseslint.config(
  { ignores: ['dist'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
    },
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
      '@typescript-eslint/no-explicit-any': 'error',
      '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    },
  },
)
```

`components.json`:
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "default",
  "rsc": false,
  "tsx": true,
  "tailwind": {
    "config": "",
    "css": "src/index.css",
    "baseColor": "slate",
    "cssVariables": true,
    "prefix": ""
  },
  "aliases": {
    "components": "src/shared/components",
    "utils": "src/shared/lib/utils",
    "ui": "src/shared/components/ui",
    "lib": "src/shared/lib",
    "hooks": "src/shared/hooks"
  }
}
```

- [ ] **Step 5: Create index.html**

```html
<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Bedrock</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 6: Commit**

```bash
git add apps/frontend/
git commit -m "✨ feat: scaffold frontend project with React 19, TypeScript, Tailwind, shadcn/ui"
```

---

## 任务 15：apps/frontend — 共享基础设施 + 应用层

**文件：**
- Create: `apps/frontend/src/index.css`
- Create: `apps/frontend/src/main.tsx`
- Create: `apps/frontend/src/App.tsx`
- Create: `apps/frontend/src/shared/lib/utils.ts`
- Create: `apps/frontend/src/shared/lib/request.ts`
- Create: `apps/frontend/src/shared/types/api.ts`
- Create: `apps/frontend/src/shared/hooks/usePagination.ts`
- Create: `apps/frontend/src/app/providers/QueryProvider.tsx`
- Create: `apps/frontend/src/app/providers/ThemeProvider.tsx`
- Create: `apps/frontend/src/app/layouts/AppLayout.tsx`
- Create: `apps/frontend/src/app/routes/index.tsx`
- Create: `apps/frontend/src/styles/tokens/colors.css`

- [ ] **Step 1: Create entry point and global styles**

`src/index.css`:
```css
@import "tailwindcss";
@import "./styles/tokens/colors.css";

body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

`src/styles/tokens/colors.css`:
```css
:root {
  --color-primary: 222.2 47.4% 11.2%;
  --color-primary-foreground: 210 40% 98%;
  --color-background: 0 0% 100%;
  --color-foreground: 222.2 84% 4.9%;
  --color-muted: 210 40% 96.1%;
  --color-muted-foreground: 215.4 16.3% 46.9%;
  --color-border: 214.3 31.8% 91.4%;
  --color-ring: 222.2 84% 4.9%;
  --color-destructive: 0 84.2% 60.2%;
  --radius: 0.5rem;
}
```

`src/main.tsx`:
```tsx
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App'

createRoot(document.getElementById('root')!).render(<App />)
```

`src/App.tsx`:
```tsx
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryProvider } from '@/app/providers/QueryProvider'
import { AppLayout } from '@/app/layouts/AppLayout'
import { UserRoutes } from '@/app/routes'

export default function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/users" replace />} />
            <Route path="/users/*" element={<UserRoutes />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  )
}
```

- [ ] **Step 2: Create shared utilities**

`src/shared/lib/utils.ts`:
```typescript
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

`src/shared/lib/request.ts`:
```typescript
import axios from 'axios'
import type { ApiResponse } from '@/shared/types/api'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  config.headers.set('X-Username', 'admin')
  config.headers.set('X-Roles', 'admin')
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      console.error('API Error:', error.response?.data ?? error.message)
    }
    return Promise.reject(error)
  },
)

export async function request<T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  data?: unknown,
  params?: Record<string, unknown>,
): Promise<ApiResponse<T>> {
  const response = await api.request<ApiResponse<T>>({ method, url, data, params })
  return response.data
}

export { api }
```

`src/shared/types/api.ts`:
```typescript
export type ApiResponse<T> = {
  code: number
  message: string
  data: T | null
}

export type PageData<T> = {
  content: T[]
  total: number
  page: number
  size: number
  total_pages: number
}
```

`src/shared/hooks/usePagination.ts`:
```typescript
import { useState, useCallback } from 'react'

export function usePagination(initialPage = 1, initialSize = 10) {
  const [page, setPage] = useState(initialPage)
  const [size, setSize] = useState(initialSize)

  const goToPage = useCallback((newPage: number) => {
    setPage(Math.max(1, newPage))
  }, [])

  const nextPage = useCallback(() => {
    setPage((prev) => prev + 1)
  }, [])

  const prevPage = useCallback(() => {
    setPage((prev) => Math.max(1, prev - 1))
  }, [])

  const resetPage = useCallback(() => {
    setPage(initialPage)
  }, [initialPage])

  return { page, size, setSize, goToPage, nextPage, prevPage, resetPage }
}
```

- [ ] **Step 3: Create app providers and layout**

`src/app/providers/QueryProvider.tsx`:
```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import type { ReactNode } from 'react'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

export function QueryProvider({ children }: { children: ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
```

`src/app/providers/ThemeProvider.tsx`:
```tsx
import { createContext, useContext, useState, type ReactNode } from 'react'

type Theme = 'light' | 'dark'

const ThemeContext = createContext<{ theme: Theme; toggleTheme: () => void }>({
  theme: 'light',
  toggleTheme: () => {},
})

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>('light')
  const toggleTheme = () => setTheme((prev) => (prev === 'light' ? 'dark' : 'light'))

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      <div data-theme={theme}>{children}</div>
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext)
}
```

`src/app/layouts/AppLayout.tsx`:
```tsx
import { Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-gray-50">
      {/* Sidebar */}
      <aside className="hidden md:flex w-60 flex-col border-r bg-white p-4">
        <h1 className="text-xl font-bold mb-8">Bedrock</h1>
        <nav className="space-y-2">
          <a href="/users" className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm font-medium">
            User Management
          </a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
```

`src/app/routes/index.tsx`:
```tsx
import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

const UserListPage = lazy(() => import('@/features/user/components/UserTable'))

export function UserRoutes() {
  return (
    <Suspense fallback={<div className="text-center py-8">Loading...</div>}>
      <Routes>
        <Route index element={<UserListPage />} />
      </Routes>
    </Suspense>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/frontend/src/
git commit -m "✨ feat: add frontend shared infrastructure, providers, and app layout"
```

---

## 任务 16：apps/frontend — 用户功能模块

**文件：**
- Create: `apps/frontend/src/features/user/types/index.ts`
- Create: `apps/frontend/src/features/user/api/userApi.ts`
- Create: `apps/frontend/src/features/user/hooks/useUsers.ts`
- Create: `apps/frontend/src/features/user/components/UserTable.tsx`
- Create: `apps/frontend/src/features/user/components/UserForm.tsx`
- Create: `apps/frontend/src/features/user/components/UserStatusToggle.tsx`

- [ ] **Step 1: Create user types and API**

`src/features/user/types/index.ts`:
```typescript
export type User = {
  id: string
  username: string
  display_name: string
  email: string | null
  phone: string | null
  avatar: string | null
  status: 'active' | 'disabled'
  roles: string[]
  last_login_at: string | null
  created_at: string | null
  updated_at: string | null
}

export type UserCreate = {
  username: string
  display_name: string
  email?: string
  phone?: string
  roles?: string[]
}

export type UserUpdate = {
  display_name?: string
  email?: string
  phone?: string
  avatar?: string
  roles?: string[]
}

export type UserSearchParams = {
  keyword?: string
  status?: string
  role?: string
  page?: number
  size?: number
}
```

`src/features/user/api/userApi.ts`:
```typescript
import { request } from '@/shared/lib/request'
import type { ApiResponse, PageData } from '@/shared/types/api'
import type { User, UserCreate, UserSearchParams, UserUpdate } from '../types'

export const userApi = {
  search(params: UserSearchParams): Promise<ApiResponse<PageData<User>>> {
    return request('get', '/users', undefined, params as Record<string, unknown>)
  },

  getById(id: string): Promise<ApiResponse<User>> {
    return request('get', `/users/${id}`)
  },

  create(data: UserCreate): Promise<ApiResponse<User>> {
    return request('post', '/users', data)
  },

  update(id: string, data: UserUpdate): Promise<ApiResponse<User>> {
    return request('put', `/users/${id}`, data)
  },

  delete(id: string): Promise<ApiResponse<null>> {
    return request('delete', `/users/${id}`)
  },

  toggleStatus(id: string): Promise<ApiResponse<User>> {
    return request('put', `/users/${id}/status`)
  },
}
```

- [ ] **Step 2: Create user hooks**

`src/features/user/hooks/useUsers.ts`:
```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { userApi } from '../api/userApi'
import type { UserCreate, UserSearchParams, UserUpdate } from '../types'

const USER_QUERY_KEY = 'users'

export function useUsers(params: UserSearchParams) {
  return useQuery({
    queryKey: [USER_QUERY_KEY, params],
    queryFn: () => userApi.search(params),
    select: (response) => response.data,
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UserCreate) => userApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) => userApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => userApi.delete(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useToggleUserStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => userApi.toggleStatus(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}
```

- [ ] **Step 3: Create user components**

`src/features/user/components/UserStatusToggle.tsx`:
```tsx
import { useToggleUserStatus } from '../hooks/useUsers'
import type { User } from '../types'

export function UserStatusToggle({ user }: { user: User }) {
  const toggleMutation = useToggleUserStatus()

  return (
    <button
      type="button"
      onClick={() => toggleMutation.mutate(user.id)}
      disabled={toggleMutation.isPending}
      className={`px-2 py-1 text-xs rounded-full font-medium ${
        user.status === 'active'
          ? 'bg-green-100 text-green-700 hover:bg-green-200'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
      }`}
    >
      {user.status === 'active' ? 'Active' : 'Disabled'}
    </button>
  )
}
```

`src/features/user/components/UserForm.tsx`:
```tsx
import { useState } from 'react'
import { useCreateUser } from '../hooks/useUsers'
import type { UserCreate } from '../types'

export function UserForm({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateUser()
  const [form, setForm] = useState<UserCreate>({
    username: '',
    display_name: '',
    email: '',
    phone: '',
    roles: [],
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(form, {
      onSuccess: () => onClose(),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold mb-4">Create User</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">Username *</label>
            <input
              type="text"
              required
              value={form.username}
              onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Display Name *</label>
            <input
              type="text"
              required
              value={form.display_name}
              onChange={(e) => setForm((prev) => ({ ...prev, display_name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Email</label>
            <input
              type="email"
              value={form.email ?? ''}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value || undefined }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Phone</label>
            <input
              type="text"
              value={form.phone ?? ''}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value || undefined }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
          >
            {createMutation.isPending ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </div>
  )
}
```

`src/features/user/components/UserTable.tsx`:
```tsx
import { useState } from 'react'
import { useUsers, useDeleteUser } from '../hooks/useUsers'
import { UserForm } from './UserForm'
import { UserStatusToggle } from './UserStatusToggle'
import { usePagination } from '@/shared/hooks/usePagination'
import type { UserSearchParams } from '../types'
import { Search, Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'

export default function UserTable() {
  const { page, size, goToPage, nextPage, prevPage } = usePagination()
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const deleteMutation = useDeleteUser()

  const params: UserSearchParams = {
    page,
    size,
    keyword: keyword || undefined,
    status: statusFilter || undefined,
  }

  const { data, isLoading } = useUsers(params)

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">User Management</h1>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
        >
          <Plus className="w-4 h-4" />
          Create User
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search users..."
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); goToPage(1) }}
            className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); goToPage(1) }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="disabled">Disabled</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Username</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Display Name</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Email</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Roles</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">Loading...</td></tr>
            ) : data?.content.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">No users found</td></tr>
            ) : (
              data?.content.map((user) => (
                <tr key={user.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{user.username}</td>
                  <td className="px-4 py-3">{user.display_name}</td>
                  <td className="px-4 py-3 text-gray-500">{user.email ?? '-'}</td>
                  <td className="px-4 py-3"><UserStatusToggle user={user} /></td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {user.roles.map((role) => (
                        <span key={role} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">{role}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => deleteMutation.mutate(user.id)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>Total {data.total} users</span>
          <div className="flex items-center gap-2">
            <button type="button" onClick={prevPage} disabled={page <= 1} className="p-1 hover:bg-gray-100 rounded disabled:opacity-30">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>Page {page} / {data.total_pages}</span>
            <button type="button" onClick={nextPage} disabled={page >= data.total_pages} className="p-1 hover:bg-gray-100 rounded disabled:opacity-30">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Create Form Modal */}
      {showForm && <UserForm onClose={() => setShowForm(false)} />}
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add apps/frontend/src/features/
git commit -m "✨ feat: add User feature module with table, form, and API integration"
```

---

## 任务 17：最终安装与验证

- [ ] **Step 1: Install frontend dependencies**

```bash
cd /Users/yaoguohh/Work/bairong && pnpm install
```

Expected: Dependencies installed without errors.

- [ ] **Step 2: Install backend dependencies**

```bash
cd /Users/yaoguohh/Work/bairong && uv sync
```

Expected: Python dependencies resolved and installed.

- [ ] **Step 3: Verify frontend build**

```bash
cd /Users/yaoguohh/Work/bairong && pnpm --filter @bedrock/frontend build
```

Expected: Build completes successfully.

- [ ] **Step 4: Verify backend syntax**

```bash
cd /Users/yaoguohh/Work/bairong/apps/backend && python -c "import ast, glob; files = glob.glob('src/**/*.py', recursive=True); [ast.parse(open(f).read()) for f in files]; print(f'{len(files)} files OK')"
```

Expected: All files parse successfully.

- [ ] **Step 5: Run backend tests**

```bash
cd /Users/yaoguohh/Work/bairong/apps/backend && pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 6: Final commit with any fixes**

```bash
git add -A && git status
```

If changes exist, commit them.

---

## 后续扩展（计划外追加）

以下模块在原始 17 个任务完成后追加迁移：

### packages/core 补全

从已有项目迁移的核心基础设施模块：
- `logging/`: 生产级日志系统（彩色输出、请求 ID 追踪、智能异常过滤、性能计时）
- `exception/`: 统一异常层次（BusinessError、ResourceNotFoundError 等）
- `cache/` 升级: CacheBackend 抽象层 + MemoryCache + 工厂模式
- `schema/`: Pydantic Schema 混入（AuditSchemaMixin、DateTimeStr）
- `service/`: BaseCRUDService CRUD 服务基类 + hooks 模式
- `model/`: ORM 混入（AuditMixin、FTSMixin、UIConfigMixin、ResourceEntity 协议）
- `type/`: 类型系统（SchemaType、DescribableSchema、权限类型、通用类型别名）
- `utils/`: 通用工具扩展（中文分词 text.py/token.py）

### packages/llm（全新）

完整的 LLM 和向量检索库：
- `models/`: 多 Provider LLM 管理（OpenAI、DashScope、VolcEngine、Ollama）、Prompt 执行引擎、回调追踪
- `chains/`: 结构化输出链（自动 Provider 检测、JSON mode 降级）
- `vector/`: 向量检索全套
  - `embeddings/`: DashScope、VolcEngine 异步 Embedding
  - `rerankers/`: DashScope、VolcEngine 重排序
  - `retrievers/`: 向量检索、全文检索、RRF 混合检索
  - `fusion/`: RRF + 加权求和融合策略
  - `store/`: PostgreSQL + pgvector 存储
  - `services/`: VectorCRUDService 自动同步
- `prompt/`: Jinja2 模板环境
- `observability/`: LangSmith 追踪集成

### packages/knowledge（全新）

知识库域模型和数据访问层：
- `model/`: KnowledgeBase、Folder、Knowledge、Chunk、Section 五大域模型 + 批量操作模型
- `repository/`: 5 个仓储（知识库、目录、文档、分片、章节），支持树形操作和权限过滤
- `schema/`: 检索结果 Schema、语音处理 Schema

### 文档站点

- VitePress 文档站点（docs/.vitepress/）
- Claude Code 指南（docs/claude/: 架构解析、速查手册、定制指南）
