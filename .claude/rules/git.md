# Git 工作流规范

本文件定义 Git 相关的标准流程和规范。

## Git Worktree 使用手册

### Claude Code 原生支持

Claude Code 内置 worktree 支持，无需手动操作：

| 方式 | 说明 |
|------|------|
| `claude --worktree` (`-w`) | 启动时自动创建隔离 worktree |
| `EnterWorktree` 工具 | 会话中途创建 worktree |
| Subagent `isolation: "worktree"` | Agent 在隔离环境执行 |

退出时自动提示保留或清理。

## 操作验证（rebase/squash/cherry-pick）

- 每步操作后运行 `git status` + `git diff --staged` 验证 staging 状态
- 完成后 `git diff <base>..HEAD --stat` 确认无文件丢失
- 不假设文件已正确 staged，不跳过验证步骤

## 提交规范

格式：`<type>(<scope>): <description>`

scope 可选，用于标识变更所属模块。

### 类型

| 类型 | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | BUG 修复 |
| `refactor` | 代码重构 |
| `test` | 测试新增或修改 |
| `docs` | 文档更新 |
| `deps` | 依赖升级 |
| `chore` | 杂项（配置、脚本、工具链等） |

### Scope 约定

Monorepo 按模块划分 scope，跨模块变更可省略：

| Scope | 对应路径 |
|-------|----------|
| `backend` | apps/backend |
| `frontend` | apps/frontend |
| `desktop` | apps/desktop |
| `core` | packages/core |
| `llm` | packages/llm |
| `knowledge` | packages/knowledge |

也可用更细粒度的业务域作为 scope（如 `user`、`auth`、`chat`）。

### 提交消息格式

```
<type>(<scope>): <简短标题>

<详细描述（可选，说明主要变更点）>
```

### 示例

```
feat(backend): 知识库搜索接口与权限校验
fix(frontend): 修复技能面板在移动端的布局溢出
refactor(core): 提取通用分页逻辑到 BasePaginator
test(backend): 补充用户服务单元测试
docs: 补充前端构建工具选型决策
chore: 同步统一 Lint 规范
```

### 约束

- type 使用小写英文短名
- 标题简洁，聚焦 "why" 而非 "what"
- 详细描述可选，用于说明主要变更点
- **禁止添加 Co-Authored-By 签名**
