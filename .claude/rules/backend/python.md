---
paths: apps/backend/**/*.py
---

# Python 后端开发规范

本规则仅在编辑 `apps/backend/` 下的 Python 文件时生效。

## 质量标准

- Pyright 零错误、Ruff 零警告
- 函数必须有类型注解
- **禁止** `# noqa` 和 `# type: ignore`（Pydantic `**kwargs` 解包除外）

## 导入规范

- **禁止** `from src.xxx` 前缀
- 使用 `from domain.xxx`、`from core.xxx`

## 分层职责

| 层 | 职责 |
|----|------|
| **API** | `@inject` + `Depends(Provide["..."])` 注入 Service；静态路由在参数化路由前 |
| **Service** | 构造函数注入依赖，方法首参 `session: AsyncSession`，写操作调用 `flush()`，commit 由 db_session 自动处理 |
| **Repository** | Singleton 无状态；所有方法显式接收 `session`；不创建 Session，不 commit |

## 常见陷阱

| 场景 | 错误 | 正确 |
|------|------|------|
| Session | Repository 内部获取 | Service 注入，Repository 显式接收 |
| 事务 | 手动 commit 或 Repository 管理 | db_session 自动管理事务，Service 调用 `flush()` |
| 依赖 | `from main import app` | `@inject` + `Depends(Provide[...])` |
| 响应 | 直接返回数据 | `success_response()` |
| async/await | 对同步方法加 `await` | 修改前确认目标函数是 sync 还是 async |
| 路由 | 参数化路由在前 | 静态路由（`/batch`）在前 |

## 校验

- 单文件 lint 由 PostToolUse hook 自动执行（ruff check）
- 全量检查：`/enforcing-project-standards`（ruff + pyright）

## 详细文档

- @docs/backend/architecture.md
- @docs/backend/dependency-injection.md
