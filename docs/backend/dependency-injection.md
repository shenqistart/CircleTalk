# 依赖注入架构指南

> 版本: v1.0

## 1. 核心原则

- 扁平容器：所有 Provider 挂在根容器 `AppContainer`
- 显式依赖：`providers.Factory/Singleton` 必须传入全部依赖
- 显式 Session：入口获取 `AsyncSession`，贯穿 Service → Repository
- 装饰器顺序：路由装饰器在外，`@inject` 紧贴函数

## 2. 容器设计

位置：`apps/backend/src/backend/container.py`

```python
class AppContainer(containers.DeclarativeContainer):
    user_repository = providers.Singleton(UserRepository)
    user_service = providers.Singleton(UserService, repository=user_repository)
```

## 3. Session 获取

| 场景 | 获取方式 | 事务管理 |
|------|----------|----------|
| HTTP | `Depends(db_session)` | 自动 commit |
| 后台任务 | `scoped_session(tenant)` | 显式 commit |

## 4. 分层规则

- API → Service → Repository → Model
- 禁止反向依赖
- Service 不访问容器
- Repository 不管理事务

## 5. 常见陷阱

- Provider 未传依赖 → 运行时实例不完整
- Service `__init__` 误加 `@inject`
- 路由装饰器顺序错误
- `scoped_session` 写操作忘记 `commit()`
