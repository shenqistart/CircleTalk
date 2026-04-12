# Review Patterns Reference

## 后端三层详细规则

### API 层 (domain/api/)

**允许：** 参数校验、响应封装 success_response()、@inject + Depends(Provide[...]) 注入 Service、Depends(db_session) 获取 Session

**禁止：** 业务逻辑、直接调 Repository、直接操作 DB

```python
@router.get("/users")
@inject                      # @inject 紧贴函数
async def get_users(
    session: AsyncSession = Depends(db_session),
    service: UserService = Depends(Provide["user_service"]),
):
    return success_response(await service.list(session))
```

路由顺序：静态 `/batch` 在参数化 `/{id}` 前。

### Service 层 (domain/service/)

**允许：** 业务编排、调用 Repository（构造器注入）、flush() 写操作

**禁止：** commit、创建 Session、返回 HTTP Response

```python
class UserService:
    def __init__(self, repo: UserRepository):
        self._repo = repo

    async def create(self, session: AsyncSession, data: CreateUserSchema):
        user = User(**data.model_dump())
        await self._repo.add(session, user)
        await session.flush()
        return user
```

### Repository 层 (domain/repository/)

**允许：** CRUD、查询构建、显式接收 session

**禁止：** commit、flush、创建 Session、业务逻辑、import API/Service

```python
class UserRepository:  # Singleton
    async def get_by_id(self, session: AsyncSession, user_id: str):
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
```

### Session 流转

```
HTTP Request → db_session 创建 Session
  → API Depends(db_session) 获取 → 传 Service(首参) → 传 Repository(首参)
  → Service 写操作 flush()
  → 成功 auto commit / 异常 auto rollback
```

后台任务：`scoped_session(tenant)`。

### 常见后端错误

| 错误 | 正确 |
|------|------|
| Repository commit | Service flush, middleware commit |
| `from src.xxx` | `from domain.xxx` / `from core.xxx` |
| `os.environ` | pydantic-settings Settings 类 |
| 参数化路由在前 | 静态路由在前 |
| 返回裸数据 | success_response() |

---

## 前端分层

```
features/{domain}/ → shared/ → styles/
  components/hooks/api/types
```

| 目录 | 规则 |
|------|------|
| features/ | 按业务域，自包含，禁止跨 feature 导入 |
| shared/ | 全局共享 UI/hooks/utils，不依赖 features |
| styles/ | 设计 token、CSS 变量 |

依赖方向：features/ → shared/ → styles/。禁止反向。

### Electron 桌面端

| 进程 | 规则 |
|------|------|
| Main | 窗口管理/IPC；禁止 UI 逻辑和阻塞操作 |
| Preload | contextBridge 暴露具名方法；禁止透传 ipcRenderer |
| Renderer | React UI（同前端规范）；禁止 Node.js API |

安全基线：contextIsolation:true / nodeIntegration:false / sandbox:true

---

## React 设计模式（精选 6 类）

### 1. 职责分离 (82)
组件 > 50 行混合状态+渲染 → 提取 Hook；直接调 API → 走 Hook/api

### 2. Hook 提取 (80)
useState+useEffect 同一关注点 → useXxx；2+ 组件共享 → 共享 Hook

### 3. 状态设计 (85)
可计算值存 state → useMemo；多 useState 同步更新 → useReducer

### 4. Effect 纪律 (82)
无依赖数组 → 补；事件处理可做 → 移出 Effect；缺 cleanup → 补

### 5. 组合 (78)
props > 10 → 拆；布尔 props > 3 → 拆独立组件；条件分支 > 4 → Record 映射

### 6. 错误处理 (80)
API 无 try/catch → 补；无 ErrorBoundary → 路由级补

---

## SOLID

| 原则 | 违反信号 |
|------|---------|
| S 单一职责 | 类名含 "And/Manager/Helper" |
| O 开闭 | 频繁改已有代码 |
| L 里氏替换 | isinstance 泛滥 |
| I 接口隔离 | 实现类有空方法 |
| D 依赖倒置 | 直接 import 具体类 |

优先级：依赖注入 > 工厂模式 > 继承

## 坏味道

| 坏味道 | 重构 |
|--------|------|
| 重复 > 3 次 | 提取函数/类 |
| 函数 > 80 行 | 拆分职责 |
| 嵌套 > 3 层 | 早返回 |
| 参数 > 5 个 | 参数对象 |
| 条件复杂 | 策略模式 |

## 命名

**Python：** 类 PascalCase / 函数 snake_case / 私有 _ / 常量 UPPER_SNAKE
**TypeScript：** 组件 PascalCase / Hook use 前缀 / 函数 camelCase

## 静态分析命令

```bash
# 后端全套
cd apps/backend && ruff format src/ && ruff check --fix src/ && pyright src/

# 前端
cd apps/frontend && pnpm lint && pnpm build

# 桌面端
cd apps/desktop && pnpm lint && pnpm build
```

约束：pyright/ruff/eslint 零错误；禁止 noqa/type:ignore（Pydantic **kwargs 除外）；禁止 @ts-ignore/eslint-disable。
