# 后端架构与开发规范

> 版本: v1.0

## 1. 总览

- 请求链路：客户端 → Middleware(认证/租户) → API(@inject + Depends(db_session)) → Service(session 首参，调用 flush) → Repository(session 形参) → DB
- 依赖注入：扁平 `AppContainer`（`apps/backend/src/backend/container.py`），`providers.Singleton/Factory` 显式传入全部依赖，Service 不使用 `@inject`
- Session/事务：`db_session` 使用 `session.begin()` 自动管理事务；后台任务使用 `scoped_session(tenant)` 并显式 commit；Service 调用 `flush()` 确保数据可见性
- 多租户：Schema 隔离模式，所有租户共享一个数据库，通过 `SET search_path` 切换 schema
- 导入规范：禁止 `src.` 前缀，使用 `domain/core` 显式路径

## 2. 目录与分层

```
bedrock/
├── apps/
│   ├── backend/
│   │   └── src/backend/
│   │       ├── main.py        # 启动 + 路由
│   │       ├── container.py   # DI 容器
│   │       ├── common/        # 响应/异常/分页
│   │       └── domain/        # 业务域
│   │           └── user/      # 用户管理示例
│   └── frontend/
└── packages/
    └── core/                  # 共享基础设施
```

分层职责：
- **API**：`@inject` + `Depends(Provide["..."])` 注入 Service，`Depends(db_session)` 获取 Session；静态路由在参数化路由前
- **Service**：构造函数注入依赖，方法首参 `session: AsyncSession`，写操作调用 `flush()`
- **Repository**：Singleton，无状态；所有方法显式接收 `session`；不创建 Session，不 commit

## 3. 依赖注入（AppContainer）

```python
class AppContainer(containers.DeclarativeContainer):
    user_repository = providers.Singleton(UserRepository)
    user_service = providers.Singleton(UserService, repository=user_repository)
```

规范：
- Provider 必须显式传入依赖
- 仅 API 入口使用 `@inject` + `Provide["..."]`
- Service 自身不加 `@inject`

## 4. Session 与事务策略

| 场景 | 获取方式 | 事务管理 |
|------|----------|----------|
| HTTP/WebSocket | `Depends(db_session)` | 自动 commit |
| 后台任务（写操作） | `scoped_session(tenant)` | 需显式 `commit()` |

## 5. API/路由规范

- 路由装饰器在外层，`@inject` 紧贴函数
- 响应统一 `success_response` / `pageable_success_response`
- 路由顺序：静态路径优先于参数化路径

## 6. 常见陷阱

| 场景 | 错误 | 正确 |
|------|------|------|
| Session | Repository 内部创建 | API 用 `db_session`，后台用 `scoped_session(tenant)` |
| 事务 | 手动 commit | db_session 自动管理，Service 调用 `flush()` |
| 依赖 | `from main import app` | 容器显式配置 Provider |
| 路由 | 参数化路由在前 | 静态路由在前 |
