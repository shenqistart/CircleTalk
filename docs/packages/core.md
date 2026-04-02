# Core 基础设施

> 版本: v1.0

`packages/core` 提供所有业务服务共享的基础设施层，包含 13 个模块。

## 模块总览

| 模块 | 职责 | 关键导出 |
|------|------|----------|
| `database` | 多租户数据库管理、异步 Session | `Base`, `db_session()`, `scoped_session()`, `DatabaseRegistry` |
| `repository` | 通用 CRUD + 分页 + 规约查询 | `BaseRepository[ModelT]`, `SearchSpec`, `PageRequest`, `PageResponse` |
| `cache` | 多后端缓存抽象（内存 / Redis） | `CacheBackend`, `MemoryCache`, `RedisCache`, `get_cache()`, `RedisService` |
| `config` | YAML 配置加载 + 环境变量覆盖 | `ConfigLoader` |
| `context` | 请求上下文（租户、用户、角色） | `RequestContext`, `set_request_context()`, `current_tenant()` |
| `exception` | 业务异常层次结构 | `BusinessError`, `PermissionDeniedError`, `ResourceNotFoundError` |
| `logging` | 分阶段日志、请求上下文注入、性能计时 | `configure_logging()`, `get_logger()`, `alog_timing()`, `timed()` |
| `model` | ORM Mixin（审计、全文检索、UI 配置） | `AuditMixin`, `TimestampMixin`, `FTSMixin`, `UIConfigMixin` |
| `schema` | Pydantic 基础 Schema Mixin | `AuditSchemaMixin`, `MetadataSchemaMixin`, `DateTimeStr` |
| `service` | 通用 CRUD Service + 钩子方法 | `BaseCRUDService[ModelType, SchemaType]` |
| `storage` | 对象存储抽象（MinIO 后端） | `StorageService`, `MinIOStorage`, `StorageServiceRegistry` |
| `type` | 共享类型定义（JSON、权限、ABAC） | `JSONValue`, `Action`, `ResourceType`, `ResourceContext` |
| `utils` | 通用工具函数（环境、文件、文本、分词） | `EnvUtils`, `temporary_file()`, `tokenize_for_fts()` |

## 目录结构

```
packages/core/src/core/
├── database/          # Base, db_session, scoped_session, DatabaseRegistry
├── repository/        # BaseRepository, PrimaryKeyStrategy, SearchSpec
├── cache/             # CacheBackend, MemoryCache, RedisCache, RedisService
├── config/            # ConfigLoader
├── context/           # RequestContext, contextvars 管理
├── exception/         # BusinessError 层次结构
├── logging/           # 日志配置、过滤器、计时装饰器
├── model/             # AuditMixin, FTSMixin, UIConfigMixin
├── schema/            # Pydantic Mixin
├── service/           # BaseCRUDService
├── storage/           # MinIOStorage, StorageServiceRegistry
├── type/              # 共享类型与权限枚举
└── utils/             # 环境、文件、文本工具
```

## 核心设计模式

### 多租户数据库

通过 PostgreSQL Schema 隔离实现多租户。`DatabaseRegistry` 管理共享 Engine 和 Session 工厂，`db_session()` 用于 HTTP 请求（自动 commit），`scoped_session(tenant)` 用于后台任务（显式 commit）。

### Repository 层

`BaseRepository[ModelT]` 提供泛型 CRUD，通过策略模式支持单主键和复合主键。`SearchSpec` + `PageRequest` 实现规约查询和分页。所有方法显式接收 `session`，不管理事务。

### 缓存抽象

`CacheBackend` 定义统一接口（get/set/delete/clear/exists），通过 `get_cache()` 工厂按配置选择后端（内存 / Redis）。`RedisService` 提供租户感知的 key 前缀隔离。

### 日志系统

分阶段初始化（early → main），支持 Spring Boot 风格的彩色输出。`RequestContextFilter` 自动注入 request_id，`alog_timing()` / `timed()` 提供异步/同步性能计时。
