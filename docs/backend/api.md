# FastAPI 接口文档

本文档基于当前 `backend.main:app` 的 OpenAPI 输出与路由源码整理。运行后端后也可以直接访问：

- Swagger UI：`http://localhost:8000/docs`
- ReDoc：`http://localhost:8000/redoc`
- OpenAPI JSON：`http://localhost:8000/openapi.json`

## 基础约定

- 默认后端地址：`http://localhost:8000`
- API 前缀：`/api`
- JSON 请求头：`Content-Type: application/json`
- 当前 CORS 允许所有来源，见 `apps/backend/src/backend/main.py`
- 请求上下文可通过 Header 传入：
  - `X-Username`：当前用户名，默认 `anonymous`
  - `X-Roles`：逗号分隔角色列表，默认空列表

## 响应格式

用户管理接口使用统一响应信封：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

圆桌对话接口直接返回业务 DTO；流式接口返回 `text/plain; charset=utf-8` 文本流，不包统一响应信封。

校验失败时 FastAPI 返回标准 `422`：

```json
{
  "detail": [
    {
      "loc": ["body", "field"],
      "msg": "Field required",
      "type": "missing"
    }
  ]
}
```

## 健康检查

### GET `/health`

检查后端服务是否可访问。

**响应示例**

```json
{
  "status": "ok",
  "service": "bedrock"
}
```

## 用户管理

用户管理接口位于 `apps/backend/src/backend/domain/api/user.py`，统一返回 `CommonResponse`。

### GET `/api/users`

分页查询用户。

**Query 参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| `keyword` | string | 否 | - | 搜索关键词 |
| `status` | string | 否 | - | 按状态筛选 |
| `role` | string | 否 | - | 按角色筛选 |
| `page` | integer | 否 | `1` | 页码，最小 1 |
| `size` | integer | 否 | `10` | 每页条数，1-100 |

**响应示例**

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "content": [
      {
        "id": "user-id",
        "username": "admin",
        "display_name": "Admin",
        "email": "admin@example.com",
        "phone": null,
        "avatar": null,
        "status": "active",
        "roles": ["admin"],
        "last_login_at": null,
        "created_at": "2026-05-12T00:00:00Z",
        "updated_at": "2026-05-12T00:00:00Z",
        "created_by": "anonymous",
        "updated_by": "anonymous"
      }
    ],
    "total": 1,
    "page": 1,
    "size": 10,
    "total_pages": 1
  }
}
```

### POST `/api/users`

创建用户。

**请求体**

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `username` | string | 是 | 长度 2-100 |
| `display_name` | string | 是 | 长度 1-255 |
| `email` | string/null | 否 | - |
| `phone` | string/null | 否 | - |
| `roles` | string[] | 否 | 默认 `[]` |

**请求示例**

```json
{
  "username": "newuser",
  "display_name": "New User",
  "email": "newuser@example.com",
  "phone": null,
  "roles": ["user"]
}
```

**响应说明**

- 成功：`code=200`，`data` 为用户对象。
- 用户名重复：当前 service 会抛出业务异常，由全局错误处理包装。

### GET `/api/users/{user_id}`

获取单个用户。

**Path 参数**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `user_id` | string | 用户 ID |

**响应说明**

- 成功：`code=200`，`data` 为用户对象。
- 不存在：HTTP 仍为 `200`，响应体 `code=404`，`message="用户不存在"`。

### PUT `/api/users/{user_id}`

更新用户。所有字段均可选。

**请求体**

| 字段 | 类型 | 必填 |
| --- | --- | --- |
| `display_name` | string/null | 否 |
| `email` | string/null | 否 |
| `phone` | string/null | 否 |
| `avatar` | string/null | 否 |
| `roles` | string[]/null | 否 |

**请求示例**

```json
{
  "display_name": "Updated User",
  "email": "updated@example.com",
  "roles": ["admin", "user"]
}
```

### DELETE `/api/users/{user_id}`

删除用户。

**响应说明**

- 成功：`code=200`，`message="用户已删除"`。
- 不存在：HTTP 仍为 `200`，响应体 `code=404`。

### PUT `/api/users/{user_id}/status`

切换用户状态。

**响应说明**

- 若当前 `status` 为 `active`，切换为 `disabled`。
- 其他状态切换为 `active`。
- 成功返回更新后的用户对象。

## 圆桌对话

圆桌对话接口位于 `apps/backend/src/backend/domain/api/roundtable.py`。普通接口返回 camelCase DTO；stream 接口返回纯文本流。

### GET `/api/roundtable/personas`

获取可选人物列表。后端会先 seed 内置 persona，再从数据库读取。

**响应示例**

```json
[
  {
    "id": "socrates",
    "displayName": "苏格拉底",
    "skillName": "nuwa-skill/socrates",
    "summary": "通过追问拆解概念、前提与未明说的假设。",
    "selectionReason": null
  }
]
```

### POST `/api/roundtable/personas/recommend`

根据决策题自动推荐 3-5 位人物。

**请求体**

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `decisionPrompt` | string | 是 | 长度 1-4000 |

**请求示例**

```json
{
  "decisionPrompt": "我是否应该从大公司离职创业？"
}
```

**响应示例**

```json
[
  {
    "id": "drucker",
    "displayName": "彼得·德鲁克",
    "skillName": "nuwa-skill/drucker",
    "summary": "目标、责任、组织绩效、客户价值与可执行管理动作。",
    "selectionReason": "与「我是否应该从大公司离职创业？」的问题视角互补，可提供目标、责任、组织绩效、客户价值与可执行管理动作。"
  }
]
```

### POST `/api/roundtable/sessions`

创建圆桌会话。若 `personaIds` 为空，后端自动推荐人物；若传入 `personaIds`，手动选择优先。

**请求体**

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `decisionPrompt` | string | 是 | 长度 1-4000 |
| `personaIds` | string[] | 否 | 默认 `[]` |

**请求示例**

```json
{
  "decisionPrompt": "我是否应该从大公司离职创业？",
  "personaIds": ["socrates", "munger"]
}
```

**响应示例**

```json
{
  "session": {
    "id": "session-id",
    "decisionPrompt": "我是否应该从大公司离职创业？",
    "status": "ready",
    "selectedPersonas": [
      {
        "id": "socrates",
        "displayName": "苏格拉底",
        "skillName": "nuwa-skill/socrates",
        "summary": "通过追问拆解概念、前提与未明说的假设。",
        "selectionReason": "用户显式选择，优先于自动推荐。",
        "selectionSource": "manual",
        "sequence": 1
      }
    ],
    "transcript": [
      {
        "id": "message-id",
        "role": "user",
        "content": "我是否应该从大公司离职创业？",
        "roundName": "system",
        "sequence": 1,
        "createdAt": "2026-05-12T00:00:00Z",
        "personaId": null,
        "personaName": null
      }
    ],
    "artifacts": null,
    "createdAt": "2026-05-12T00:00:00Z",
    "updatedAt": "2026-05-12T00:00:00Z"
  },
  "recommendedPersonas": []
}
```

### GET `/api/roundtable/sessions/{session_id}`

恢复圆桌会话，返回已选人物、完整 transcript 和三件套 artifacts。

**Path 参数**

| 参数 | 类型 | 说明 |
| --- | --- | --- |
| `session_id` | string | 圆桌会话 ID |

**状态值**

`status` 可能为：

- `draft`
- `ready`
- `streaming`
- `completed`
- `error`
- `cancelled`

**消息字段**

`transcript[].role` 可能为：`moderator`、`persona`、`user`、`system`。

`transcript[].roundName` 可能为：`opening`、`rebuttal`、`closing`、`synthesis`、`follow_up`、`system`。

### POST `/api/roundtable/sessions/{session_id}/stream`

启动圆桌讨论文本流。后端会：

1. 将 session 状态更新为 `streaming`
2. 调用 roundtable orchestrator 生成 Opening/Rebuttal/Closing/Synthesis
3. 每生成一条 message，写入数据库并向客户端 yield 一个纯文本 chunk
4. 生成 artifact，写入数据库
5. 将 session 状态更新为 `completed`

**响应**

- Content-Type：`text/plain; charset=utf-8`
- Body：多段纯文本 chunk
- 客户端断开时，后端会将 session 标记为 `cancelled`

**curl 示例**

```bash
curl -N -X POST "http://localhost:8000/api/roundtable/sessions/$SESSION_ID/stream"
```

**前端消费位置**

`apps/frontend/src/features/roundtable/hooks/useRoundtableChat.ts` 的 `consumeTextStream()`。

### POST `/api/roundtable/sessions/{session_id}/follow-up/stream`

基于已有 transcript、artifacts 和 selected personas 提交追问。

**请求体**

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| `question` | string | 是 | 长度 1-4000 |

**请求示例**

```json
{
  "question": "如果我只能先做一个低成本实验，应该选哪个？"
}
```

**响应**

- Content-Type：`text/plain; charset=utf-8`
- Body：主持人追问回答文本

**curl 示例**

```bash
curl -N -X POST "http://localhost:8000/api/roundtable/sessions/$SESSION_ID/follow-up/stream" \
  -H "Content-Type: application/json" \
  -d '{"question":"如果我只能先做一个低成本实验，应该选哪个？"}'
```

## 主要数据结构

### RoundtablePersonaSchema

| 字段 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string | 是 |
| `displayName` | string | 是 |
| `skillName` | string | 是 |
| `summary` | string | 是 |
| `selectionReason` | string/null | 否 |

### SelectedPersonaSchema

继承 `RoundtablePersonaSchema`，并增加：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `selectionSource` | `auto`/`manual` | 是 | 自动推荐或用户手选 |
| `sequence` | integer | 是 | 展示顺序 |

### RoundtableSessionSchema

| 字段 | 类型 | 必填 |
| --- | --- | --- |
| `id` | string | 是 |
| `decisionPrompt` | string | 是 |
| `status` | string | 是 |
| `selectedPersonas` | SelectedPersonaSchema[] | 是 |
| `transcript` | RoundtableMessageSchema[] | 是 |
| `artifacts` | DecisionArtifactSchema/null | 否 |
| `createdAt` | datetime | 是 |
| `updatedAt` | datetime | 是 |

### DecisionArtifactSchema

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `memo` | string | 是 | 决策备忘录 |
| `recommendation` | string | 是 | 推荐结论 |
| `reasons` | string[] | 是 | 推荐理由 |
| `debateMap` | object[] | 是 | 多方观点辩论地图 |

## 本地调试流程

1. 启动后端：

```bash
pnpm dev:backend
```

2. 打开 Swagger：

```text
http://localhost:8000/docs
```

3. 创建圆桌 session：

```bash
curl -X POST "http://localhost:8000/api/roundtable/sessions" \
  -H "Content-Type: application/json" \
  -d '{"decisionPrompt":"我是否应该从大公司离职创业？","personaIds":[]}'
```

4. 使用返回的 `session.id` 启动 stream：

```bash
curl -N -X POST "http://localhost:8000/api/roundtable/sessions/$SESSION_ID/stream"
```
