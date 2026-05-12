# 圆桌对话决策参谋

> 状态: 首版集成中  
> 依据: `.omx/plans/prd-roundtable-dialogue-professional-stack-20260511T231230Z.md` 与 `.omx/plans/test-spec-roundtable-dialogue-professional-stack-20260511T231230Z.md`

## 目标体验

圆桌对话决策参谋把一个决策题拆成“人物选择/推荐 → 多轮圆桌 → 主持人三件套 → 继续追问”的闭环：

1. 用户输入决策题。
2. 用户可手动选择人物；如果未选择，系统推荐 3-5 个多样化人物并给出 reason。
3. 后端按 Opening / Rebuttal / Closing 编排 persona 发言。
4. 主持人生成 memo、recommendation、reasons、debate map。
5. session、selected personas、transcript、artifacts、follow-up messages 持久化，刷新后可恢复。

## 首版技术边界

| 层 | 首版决策 | 约束 |
| --- | --- | --- |
| Frontend | Vite React + AI SDK UI | 使用 Text Stream 模式；v1 不消费 UIMessage typed parts |
| Backend | FastAPI + domain service/repository | `POST /sessions` 先建 session，stream endpoint 只负责文本流 |
| LLM | `packages/llm` 持有 DeepAgents adapter | backend 通过 `bedrock-llm` 调用，不直接依赖 `deepagents` |
| Persistence | Render Postgres / SQLAlchemy / Alembic | `DATABASE_URL` 优先，runtime 与 Alembic 共用 resolver |
| Deployment | Vercel frontend + Render backend | preview/production smoke 是发布门禁 |

## API 合同

首版推荐两步流式：

1. `POST /api/roundtable/sessions`
   - 请求: `{ decisionPrompt, personaIds? }`
   - 响应: `{ session, recommendedPersonas }`
   - 手动传入 `personaIds` 时，必须以用户选择为准，不得用自动推荐覆盖。
2. `POST /api/roundtable/sessions/{session_id}/stream`
   - 返回纯文本流，供 AI SDK Text Stream consumer 展示。
   - stream 完成后，前端调用 `GET /api/roundtable/sessions/{session_id}` 拉取最终 transcript/artifacts/status。
3. `POST /api/roundtable/sessions/{session_id}/follow-up/stream`
   - 必须复用数据库中的 transcript、artifacts、selected personas。
   - follow-up 追加写入 transcript，建议 `roundName="follow_up"`。

## 当前代码质量审查记录

- `apps/frontend/src/features/roundtable/api/roundtableApi.ts` 已提供本地 demo fallback，仅用于后端未就绪时的本地 UI 联调；验收、回归和部署 smoke 必须连接真实 backend/DB/stream，不能用 fallback 结果替代。
- API base URL 统一去除结尾 `/`，请求 path 统一补前导 `/`，避免 `VITE_API_BASE_URL` 配置为 `https://api.example.com/` 时生成双斜杠 URL。
- mock session 只生成一次 `sessionId` 并复用于 transcript message id，保证刷新/恢复调试时 id 关系稳定。
- 当前 worktree 只包含 roundtable frontend API/types；backend roundtable domain、LLM roundtable package、migration、AI SDK hook/components 尚未出现在本工作树，不能宣称端到端完成。
- 评审发现当前前端还缺少 roundtable 页面挂载、AI SDK Text Stream consumer、abort/error/refetch 处理、follow-up stream API，以及真实恢复测试；这些应作为后续实现任务进入验收门禁。

## 验收清单

### 本地静态检查

```bash
pnpm --filter @bedrock/frontend lint
pnpm --filter @bedrock/frontend build
uv run --package bedrock-llm pytest packages/llm
uv run --package bedrock-backend pytest apps/backend
uv run --package bedrock-backend ruff check apps/backend/src apps/backend/tests
cd apps/backend && alembic upgrade head
```

### 浏览器 smoke

1. 打开圆桌页面。
2. 输入决策题，不手动选择人物，确认推荐 3-5 个且显示 reason。
3. 开始讨论，确认 Opening/Rebuttal/Closing 或等价多轮展示。
4. 确认三件套展示。
5. 刷新 session 页面，确认 selected personas、transcript、artifacts 恢复。
6. 提交 follow-up，刷新后确认 follow-up messages 仍存在。
7. 手动选择 1 个和全部候选人物各跑一次，确认自动推荐没有覆盖用户选择。

### 部署 smoke

```bash
curl "$RENDER_BACKEND_URL/health"
curl "$VERCEL_PREVIEW_URL/api/health"
curl -N -X POST "$RENDER_BACKEND_URL/api/roundtable/sessions/$SESSION_ID/stream"
```

发布门禁：Vercel build、Render health、Alembic migration、DeepAgents import/init、短 roundtable stream、Postgres 写入 session/session_personas/messages/artifacts 全部通过。
