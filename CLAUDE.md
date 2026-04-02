# Bedrock

公司级规范示例项目，所有子服务的规范源头、学习入口和设计语言参考。

## 项目结构

```
bedrock/
├── apps/
│   ├── backend/                # FastAPI Python 后端 (8000)
│   │   └── src/backend/
│   │       ├── main.py         # 启动 + 路由
│   │       ├── container.py    # DI 容器
│   │       ├── common/         # error_handler / pagination / response
│   │       └── domain/         # 业务域
│   │           ├── api/        # API 端点
│   │           ├── model/      # ORM 模型
│   │           ├── repository/ # 数据访问
│   │           ├── schema/     # Pydantic Schema
│   │           └── service/    # 业务逻辑
│   └── frontend/               # React TypeScript 前端 (5173)
│       └── src/
│           ├── app/            # layouts / providers / routes
│           ├── features/       # 按业务划分（user/ 为示例）
│           ├── shared/         # hooks / lib / types
│           └── styles/         # 设计 token
├── packages/
│   ├── core/                   # 共享基础设施
│   │   # database / repository / cache / config / context / storage
│   │   # exception / logging / model / schema / service / type / utils
│   ├── llm/                    # LLM 能力封装
│   │   # models / chains / vector / prompt / observability
│   └── knowledge/              # 知识库
│       # model / repository / schema
├── .claude/                    # Claude Code 规范体系
│   ├── rules/                  # 开发规范（自动加载）
│   ├── skills/                 # 项目技能（按需调用）
│   └── hooks/                  # 代码守卫
└── docs/                       # 项目文档（VitePress）
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

示例域：`apps/backend/src/backend/domain/`（以 user 为示例）

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
- Core 基础设施：docs/packages/core.md
- LLM 能力封装：docs/packages/llm.md
- Knowledge 知识库：docs/packages/knowledge.md
