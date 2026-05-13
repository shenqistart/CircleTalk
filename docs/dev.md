---
title: "本地开发与体验"
---

# 本地开发与体验

本文说明如何在本地启动 Bedrock，并体验圆桌对话决策参谋。

## 流程图

```text
当前代码已合入并通过本地门禁
  ↓
选择体验方式
  ├─ 只看前端流程
  │    ↓
  │  启动 Vite 前端
  │    ↓
  │  打开 /roundtable，使用 mock fallback 体验页面与基础流程
  │
  └─ 体验真实后端 + 数据库闭环
       ↓
     准备本地 Postgres
       ↓
     执行 Alembic migration
       ↓
     启动 FastAPI backend
       ↓
     启动 Vite frontend
       ↓
     打开 /roundtable，体验创建 session、Text Stream、三件套、追问与刷新恢复
```

## 前置要求

- Python 3.13+
- `uv`
- Node.js 22.12+，推荐直接使用仓库 `.nvmrc`
- `pnpm`
- 如需真实后端持久化：Postgres

当前 Vite 版本对 Node 有要求。如果使用 Node 21.6.1，自动启动 dev server 时会触发 `crypto.hash is not a function`。建议每次前端开发或 E2E 前先执行：

```bash
nvm use
```

## 快速体验前端

如果只是想先看 UI 和交互入口，可以只启动前端。当前圆桌 API 客户端在后端不可用时会 fallback 到 mock 数据。

```bash
pnpm dev:frontend
```

打开：

```text
http://localhost:5173/roundtable
```

这种方式适合快速查看页面、人物列表、推荐/手选人物和创建 mock session。完整的讨论流、数据库恢复和追问持久化需要真实后端。

## 真实本地闭环

真实闭环需要本地 Postgres。默认配置来自 `apps/backend/config.yaml`：

```text
host=localhost
port=5432
user=postgres
password=postgres
database=bedrock
```

## Docker 本地开发环境

如果本机已启动 Docker Desktop，可以用 Docker Compose 一次性启动 Postgres 和 backend：

```bash
docker compose -f docker-compose.dev.yml up --build
```

这个命令会：

1. 启动 `bedrock-postgres`，暴露 `localhost:5432`。
2. 构建 `apps/backend/Dockerfile`。
3. 等待 Postgres healthcheck 通过。
4. 执行 `alembic upgrade head`。
5. 启动 FastAPI backend，暴露 `localhost:8000`。

然后另开一个终端启动前端：

```bash
pnpm dev:frontend
```

打开：

```text
http://localhost:5173/roundtable
```

停止本地 Docker 环境：

```bash
docker compose -f docker-compose.dev.yml down
```

如果要清空数据库数据：

```bash
docker compose -f docker-compose.dev.yml down -v
```

> 如果出现 `Cannot connect to the Docker daemon`，先启动 Docker Desktop，再重试。

### 1. 准备数据库

```bash
createdb -U postgres bedrock
```

如果数据库已存在，可以跳过这一步。

### 2. 执行迁移

```bash
cd apps/backend
uv run --package bedrock-backend alembic upgrade head
```

如需先检查 SQL：

```bash
cd apps/backend
uv run --package bedrock-backend alembic upgrade head --sql
```

### 3. 启动后端

```bash
cd apps/backend
uv run --package bedrock-backend uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```bash
curl http://localhost:8000/health
```

接口调试入口：

```text
http://localhost:8000/docs
```

FastAPI 会自动提供 Swagger UI，可在页面里直接查看接口 schema、填写参数并发送请求。也可以访问：

```text
http://localhost:8000/redoc
http://localhost:8000/openapi.json
```

### 4. 启动前端

另开一个终端：

```bash
pnpm dev:frontend
```

打开：

```text
http://localhost:5173/roundtable
```

Vite 已配置 `/api` 代理到 `http://localhost:8000`，本地不需要额外配置 `VITE_API_BASE_URL`。

## 圆桌体验路径

1. 打开 `/roundtable`。
2. 输入一个真实决策题。
3. 点击推荐人物，或手动选择 1 个到全部人物。
4. 创建圆桌会话。
5. 点击开始讨论流。
6. 查看 Opening / Rebuttal / Closing 与主持人三件套。
7. 提交继续追问。
8. 刷新页面，确认 session、selected personas、transcript、artifacts 和 follow-up 能恢复。

默认圆桌编排使用 request-scoped deterministic fallback，因此本地体验不需要配置真实 LLM API key。

## 启用真实 LLM

如需让每个人物生成不同观点，可以启用圆桌专用 OpenAI-compatible LLM 配置。未启用、未提供 key，或调用失败时，系统会自动回退到 deterministic fallback。

本地 Docker 启动前可在 shell 中配置：

```bash
export ROUNDTABLE_LLM_ENABLED=true
export ROUNDTABLE_LLM_MODEL=gpt-4o-mini
export ROUNDTABLE_LLM_API_KEY=<your-api-key>
# 可选：OpenAI 官方可不填；DeepSeek、DashScope、Volcengine 等兼容服务填自己的 base URL
export ROUNDTABLE_LLM_BASE_URL=
docker compose -f docker-compose.dev.yml up --build
```

也可以把这些变量写入本地 `.env`，Docker Compose 会自动读取根目录 `.env` 中的变量替换。

支持的变量：

```text
ROUNDTABLE_LLM_ENABLED=true
ROUNDTABLE_LLM_MODEL=<model-name>
ROUNDTABLE_LLM_API_KEY=<api-key>
ROUNDTABLE_LLM_BASE_URL=<optional-openai-compatible-base-url>
ROUNDTABLE_LLM_TEMPERATURE=0.7
ROUNDTABLE_LLM_MAX_TOKENS=700
ROUNDTABLE_LLM_TIMEOUT=30
```

Render 部署时，在 backend service 的 Environment 中设置同名变量，并把 `ROUNDTABLE_LLM_ENABLED` 改为 `true`。

## OMX 验证流程

OMX 侧常用两种验证入口：

- `$ultraqa`：单目标 QA 循环，适合跑测试 / 构建 / lint / 自定义 smoke，失败后进入诊断和修复循环。
- `team-verify -> team-fix`：团队模式里的验证和修复阶段，适合多 worker 并行实现后的收口。

当前仓库已经有可重复的 API E2E smoke：

```bash
scripts/e2e-roundtable-api.sh
```

它默认访问：

```text
http://localhost:8000/api
```

覆盖：

1. 人物列表加载。
2. 创建圆桌 session。
3. 讨论 Text Stream。
4. 完成态 session 恢复。
5. 追问 Text Stream。
6. 追问消息持久化恢复。

如果要验证 Render 后端，可以覆盖 `API_BASE_URL`：

```bash
API_BASE_URL=https://<render-backend-url>/api scripts/e2e-roundtable-api.sh
```

浏览器级 E2E 已使用 Playwright 固化在前端包里：

```bash
pnpm --filter @bedrock/frontend test:e2e
```

默认访问 `http://localhost:5173`，并使用本机 Google Chrome channel。可通过环境变量覆盖：

```bash
E2E_BASE_URL=http://localhost:5173 PLAYWRIGHT_CHROMIUM_CHANNEL=chrome pnpm --filter @bedrock/frontend test:e2e
```

这套测试会真实点击页面，覆盖输入决策题、全选人物、创建 session、启动讨论流、提交追问和按 session URL 恢复。OMX 可用 `$ultraqa --custom "pnpm --filter @bedrock/frontend test:e2e"` 跑同一套浏览器流程。

## 常用验证命令

```bash
uv run --package bedrock-backend pytest apps/backend -q
uv run --package bedrock-llm pytest packages/llm/tests/roundtable -q
uv run --package bedrock-backend ruff check apps/backend/src apps/backend/tests apps/backend/alembic packages/llm/src packages/llm/tests
uv run --package bedrock-backend pyright apps/backend/src/backend/domain apps/backend/src/backend/config apps/backend/src/backend/main.py packages/llm/src/llm/roundtable
pnpm --filter @bedrock/frontend exec eslint . --format json
pnpm --filter @bedrock/frontend build
pnpm --filter @bedrock/frontend test:e2e
scripts/e2e-roundtable-api.sh
```

## 常见问题

### Postgres 连接失败

如果看到 `localhost:5432 refused connection`，说明本地 Postgres 没启动，或账号/密码/数据库名与 `apps/backend/config.yaml` 不一致。

### 前端请求后端失败

确认后端在 `8000` 端口运行：

```bash
curl http://localhost:8000/health
```

确认前端在 `5173` 端口运行：

```text
http://localhost:5173/roundtable
```

### ESLint stylish formatter 报 `util.styleText is not a function`

这是 Node 版本与 ESLint formatter 的兼容问题。可以先用 JSON formatter 验证：

```bash
pnpm --filter @bedrock/frontend exec eslint . --format json
```

长期建议切换到 Node 22.12+。

## Render 部署

仓库根目录提供了 `render.yaml`，可作为 Render Blueprint 使用。

### Blueprint 包含

- `bedrock-postgres`: Render Postgres
- `bedrock-backend`: Docker Web Service

backend 会读取 Render 注入的 `DATABASE_URL`，并在 deploy 前执行：

```bash
cd /app/apps/backend && alembic upgrade head
```

### Render 操作步骤

1. 将仓库推到 GitHub。
2. 在 Render 控制台选择 **New + → Blueprint**。
3. 选择本仓库。
4. Render 会读取根目录 `render.yaml`。
5. 创建后等待 Postgres 和 backend 部署完成。
6. 打开 backend service 的 URL，检查：

```text
https://<render-backend-url>/health
```

返回类似：

```json
{"status":"ok","service":"bedrock"}
```

### 前端连接 Render backend

本地前端可临时指向 Render backend：

```bash
VITE_API_BASE_URL=https://<render-backend-url>/api pnpm dev:frontend
```

生产部署到 Vercel 时，在 Vercel 项目里配置：

```text
VITE_API_BASE_URL=https://<render-backend-url>/api
```
