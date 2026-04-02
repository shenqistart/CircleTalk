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

格式：`<emoji> <type>: <description>`

| Emoji | 类型 | 说明 |
|-------|------|------|
| ✨ | New Features | 新功能 |
| 🐞 | Bug Fixes | BUG修复 |
| 🔨 | Dependency Upgrades | 依赖升级 |
| 📔 | Documentation | 更新文档 |
| ♻️ | Refactor | 代码重构 |
| 🔧 | Chores | 杂项（配置、脚本、工具链等） |

### 提交消息格式

```
<emoji> <type>: <简短标题>

<详细描述（可选，说明主要变更点）>
```

### 约束

- 标题简洁，聚焦 "why" 而非 "what"
- 详细描述可选，用于说明主要变更点
- **禁止添加 Co-Authored-By 签名**
