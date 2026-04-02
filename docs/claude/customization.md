---
title: "进阶定制指南"
---

# 进阶定制指南

> 前置阅读：[项目配置架构解析](./architecture.md)

本文面向需要新增或修改 Claude Code 项目配置的开发者，覆盖 Rules、Skills、Hooks、Settings 的定制方法，以及用户级推荐配置。

## 1. 新增 Rule

### 基础规则 vs 条件规则

| 类型 | frontmatter | 加载时机 | 适用场景 |
|------|-------------|----------|----------|
| 基础规则 | 无 `paths` 字段（或无 frontmatter） | 每次对话都加载 | 全局原则、工作流、质量标准 |
| 条件规则 | 有 `paths` 字段 | 仅当编辑匹配路径的文件时加载 | 特定技术栈、特定模块的规范 |

基础规则文件放在 `.claude/rules/` 根目录，条件规则按技术栈分子目录（如 `backend/`、`frontend/`）。

### paths 语法

`paths` 字段支持 glob 模式，可以是单个字符串或字符串数组：

| 语法 | 含义 | 示例 |
|------|------|------|
| `*` | 匹配单层任意文件名 | `*.py` 匹配当前目录的 Python 文件 |
| `**` | 匹配任意层级目录 | `apps/backend/**/*.py` 匹配所有嵌套的 Python 文件 |
| `*.{ts,tsx}` | 匹配多个扩展名 | `apps/frontend/src/**/*.{ts,tsx}` |
| 数组形式 | 匹配多个路径模式 | 见下方多路径示例 |

**单路径**（字符串形式）：

```yaml
---
paths: apps/backend/src/**/*.py
---
```

**多路径**（数组形式）：

```yaml
---
paths:
  - apps/frontend/src/**/*.ts
  - apps/frontend/src/**/*.tsx
  - apps/console/src/**/*.ts
  - apps/console/src/**/*.tsx
---
```

### 实操示例：为新模块添加条件规则

假设项目新增了一个 `apps/mobile/` Flutter 模块，需要添加专属规范：

1. 创建文件 `.claude/rules/mobile/flutter.md`：

```markdown
---
paths: apps/mobile/**/*.dart
---

# Flutter 移动端规范

## 状态管理
- 使用 Riverpod 进行状态管理
- 禁止在 Widget 内直接调用 API

## 代码风格
- 运行 `dart format` 格式化
- 运行 `dart analyze` 零警告
```

2. 验证：在 Claude Code 中编辑 `apps/mobile/` 下的 `.dart` 文件，该规则会自动注入到 System Prompt。

## 2. 新增 Skill

### SKILL.md 格式规范

每个 Skill 目录下必须有 `SKILL.md` 文件，其 YAML frontmatter 定义元数据：

| 字段 | 必需 | 类型 | 说明 |
|------|------|------|------|
| `name` | 是 | string | Skill 唯一标识，与目录名一致 |
| `description` | 是 | string | 功能描述，Claude 据此判断是否匹配。建议包含触发词 |
| `allowed-tools` | 否 | string[] | Skill 执行时可使用的工具白名单。未指定则继承全局权限 |

`allowed-tools` 常用值：

| 工具 | 格式 | 说明 |
|------|------|------|
| 文件读取 | `Read` | 读取文件内容 |
| 文件搜索 | `Glob` | 按模式搜索文件 |
| 内容搜索 | `Grep` | 按正则搜索文件内容 |
| Shell 命令 | `Bash(cmd*)` | 允许执行特定命令，`*` 匹配任意参数 |

### 目录结构

以 `enforcing-project-standards` 为例，展示一个多文件 Skill 的组织方式：

```
.claude/skills/enforcing-project-standards/
├── SKILL.md       # 入口文件：元数据 + 核心审查流程（7 步）
├── FILTERS.md     # 高信号过滤规则（should report / should NOT report）
├── PATTERNS.md    # 重构模式参考（置信度映射、Bad smell → 重构技术）
└── FLUTTER.md     # 移动端专项审查规则
```

`SKILL.md` 是唯一必需文件。额外的 `.md` 文件作为补充知识，Claude 在执行 Skill 时会自动读取同目录下的所有文件。

简单 Skill 只需一个 `SKILL.md` 即可：

```
.claude/skills/upgrading-dependencies/
└── SKILL.md
```

### 实操示例：创建一个简单 Skill

创建一个"数据库迁移"Skill：

1. 创建目录和文件 `.claude/skills/database-migration/SKILL.md`：

```markdown
---
name: database-migration
description: "执行数据库迁移操作，包括创建迁移脚本、升级/降级数据库、检查迁移状态。触发词：迁移、migration、alembic。"
allowed-tools:
  - Bash(alembic*)
  - Bash(python*)
  - Read
  - Glob
  - Grep
---

# 数据库迁移技能

## 核心流程

1. 检查当前迁移状态：`alembic current`
2. 查看待执行的迁移：`alembic history --verbose`
3. 根据用户需求执行操作

## 创建新迁移

```bash
cd apps/backend
alembic revision --autogenerate -m "描述"
```

## 安全检查

- 执行 `alembic upgrade head` 前，先用 `--sql` 预览 SQL
- 降级操作必须确认用户意图
```

2. 在 `.claude/settings.json` 的 `permissions.allow` 中添加：

```json
"Skill(/database-migration)"
```

### 调试技巧

- **Skill 未触发**：检查 `description` 是否包含足够的触发词（Claude Code 2.1 基于 description 语义匹配，无需额外触发规则）
- **工具权限不足**：检查 `allowed-tools` 是否覆盖了 Skill 需要的工具，同时确认 `settings.json` 的 `permissions.allow` 中有对应的 `Skill(/name)` 条目
- **手动触发**：在对话中输入 `/skill-name` 可强制触发，用于验证 Skill 内容是否正确
- **查看加载状态**：在对话中输入 `/skills` 可查看所有已加载的 Skill 列表

## 3. 新增 Hook

### 事件类型

| 事件 | 触发时机 | 可阻止 | 典型用途 |
|------|----------|--------|----------|
| `PreToolUse` | 工具调用前 | 是（exit 2） | 拦截危险命令、权限检查 |
| `PostToolUse` | 工具调用后 | 否 | Lint 检查、文件追踪（本项目使用） |
| `UserPromptSubmit` | 用户提交消息时 | 是（exit 2） | 输入预处理 |
| `Stop` | 主代理停止时 | 否 | 会话清理 |
| `SubagentStop` | 子代理停止时 | 否 | 子任务汇总 |

### 输入输出协议

**输入**：Hook 通过 stdin 接收 JSON 数据，格式因事件类型而异：

| 事件 | stdin JSON 格式 |
|------|-----------------|
| `UserPromptSubmit` | `{ "session_id": "...", "prompt": "..." }` |
| `PreToolUse` | `{ "session_id": "...", "tool_name": "Bash", "tool_input": {...} }` |
| `PostToolUse` | `{ "session_id": "...", "tool_name": "Edit", "tool_input": {...}, "file_path": "..." }` |
| `Stop` | `{ "session_id": "..." }` |

**输出**：

| 退出码 | 含义 | 适用事件 |
|--------|------|----------|
| `0` | 通过（允许操作继续） | 所有事件 |
| `2` | 阻止操作 | 仅 `PreToolUse`、`UserPromptSubmit` |
| 其他 | 忽略（视为通过） | 所有事件 |

stderr 输出会显示给用户作为反馈信息。利用这一机制，Hook 可以在不阻止操作的情况下提供建议（exit 0 + stderr 输出），或在阻止操作时给出原因（exit 2 + stderr 输出）。

### 配置格式

Hook 在 `settings.json` 的 `hooks` 字段中配置：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "path/to/hook.sh",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

| 字段 | 说明 |
|------|------|
| `matcher` | 过滤条件。`PreToolUse`/`PostToolUse` 匹配工具名（如 `"Bash"`、`"Edit\|Write"`），留空则匹配所有 |
| `type` | 固定值 `"command"` |
| `command` | 脚本路径。支持 `$CLAUDE_PROJECT_DIR` 环境变量指向项目根目录 |
| `timeout` | 超时时间（秒） |
| `statusMessage` | 可选，执行时显示的状态消息 |

### 实操示例：PreToolUse 拦截钩子

创建一个拦截 `rm -rf /` 等危险命令的 Hook：

1. 创建脚本 `.claude/hooks/danger-guard.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail

# 从 stdin 读取 JSON
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# 仅处理 Bash 工具
if [[ "$TOOL_NAME" != "Bash" ]]; then
  exit 0
fi

COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# 检查危险模式
DANGEROUS_PATTERNS=(
  "rm -rf /"
  "rm -rf /*"
  "DROP DATABASE"
  "DROP TABLE"
  "> /dev/sda"
)

for pattern in "${DANGEROUS_PATTERNS[@]}"; do
  if echo "$COMMAND" | grep -qiF "$pattern"; then
    echo "BLOCKED: detected dangerous command pattern: $pattern" >&2
    exit 2
  fi
done

exit 0
```

2. 设置执行权限：

```bash
chmod +x .claude/hooks/danger-guard.sh
```

3. 在 `.claude/settings.json` 中注册：

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/danger-guard.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## 4. 修改 Settings

### 权限白名单语法

| 格式 | 说明 | 示例 |
|------|------|------|
| `Bash(cmd *)` | 允许某命令的所有参数 | `Bash(pnpm *)` |
| `Bash(cmd arg *)` | 允许命令+首参的所有子参数 | `Bash(git push *)` |
| `WebSearch` | 允许 Web 搜索 | `WebSearch` |
| `WebFetch(domain:host)` | 允许访问某域名 | `WebFetch(domain:github.com)` |
| `Skill(/name)` | 允许使用某 Skill | `Skill(/enforcing-project-standards)` |
| `mcp__server__*` | 允许某 MCP 服务器所有工具 | `mcp__context7__*` |

注意：Skill 在 `allowed-tools` 中使用的是 `Bash(cmd*)` 格式（无空格），而 `settings.json` 的 `permissions.allow` 中使用 `Bash(cmd *)` 格式（有空格）。两者语法略有不同。

### 分工原则

| 配置项 | `settings.json` (Git 跟踪) | `settings.local.json` (gitignore) |
|--------|---------------------------|-----------------------------------|
| 权限白名单 | 团队共享的通用工具权限 | 个人累积的一次性确认（自动生成） |
| Hooks | 项目 Hook 定义 | 不使用 |
| 插件 | 项目级插件 | 不使用（用户级插件放 `~/.claude/settings.json`） |
| 语言 | `"chinese"` | 不使用 |
| 手动维护 | 是 | 否（Claude Code 自动追加） |

`settings.local.json` 由 Claude Code 在用户确认权限时自动追加，无需手动维护。当权限列表过长时可以清理，Claude Code 会在下次需要时重新询问。

### 新增 MCP 服务器

1. 在项目根目录创建或编辑 `.mcp.json`：

```json
{
  "mcpServers": {
    "new-server": {
      "command": "npx",
      "args": ["-y", "@some-org/mcp-server"],
      "env": {
        "API_KEY": "..."
      }
    }
  }
}
```

2. 确保 `.claude/settings.json` 中已启用项目 MCP 服务器：

```json
{
  "enableAllProjectMcpServers": true
}
```

3. 在 `permissions.allow` 中添加工具权限：

```json
"mcp__new-server__*"
```

4. 重启 Claude Code 使配置生效。

## 5. 用户级推荐配置

### ~/.claude/settings.json 推荐模板

以下模板基于项目实际使用的用户级配置：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "includeCoAuthoredBy": false,
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": true
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/safe-guard.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

各字段说明：

| 字段 | 说明 |
|------|------|
| `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` | 启用 Agent Teams 实验功能（多 agent 协作） |
| `includeCoAuthoredBy` | 设为 `false` 禁止在 commit 中添加 Co-Authored-By 签名（顶层字段） |
| `enabledPlugins` | 用户级插件，所有项目共享 |
| `hooks.PreToolUse` | 全局安全钩子，拦截危险 bash 命令 |

### superpowers 插件 Skills 说明

superpowers 插件提供一套方法论 Skills，覆盖软件开发全生命周期。

**3 个入口 Skills（用户通过 `/` 命令直接调用）：**

| 入口 Skill | 调用方式 | 产出 |
|-----------|----------|------|
| `brainstorming` | `/superpowers:brainstorming` | 需求探索 → 多方案对比 → 设计文档 |
| `writing-plans` | `/superpowers:writing-plans` | 设计文档 → 分步实现计划 |
| `executing-plans` | `/superpowers:executing-plans` | 按计划分批执行，每批设 checkpoint |

三者构成核心链路：`brainstorming → writing-plans → executing-plans`。

**内部自动触发的辅助 Skills（无需手动调用）：**

以下 Skills 由入口 Skill 在工作流执行过程中按需自动调用：

| 辅助 Skill | 自动触发时机 | 功能 |
|-----------|-------------|------|
| `subagent-driven-development` | executing-plans 选择 subagent 模式 | 每 Task 独立 subagent + 双阶段 review |
| `test-driven-development` | subagent 实施 Task 时 | Red → Green → Refactor 循环 |
| `systematic-debugging` | 遇到 Bug / 测试失败时 | 假设 → 验证 → 修复 |
| `verification-before-completion` | 即将完成 Task 时 | 运行验证命令，证据先于断言 |
| `requesting-code-review` | Task 完成后 | 发起代码审查 |
| `receiving-code-review` | 收到审查反馈后 | 技术验证而非盲从 |
| `using-git-worktrees` | 需要隔离开发时 | 创建 worktree |
| `dispatching-parallel-agents` | 2+ 个无依赖 Task 时 | 并行调度 agent |
| `finishing-a-development-branch` | 所有 Task 完成后 | merge / PR / cleanup 决策 |

### 项目 Skills vs 插件 Skills 的关系

两者互补，职责不重叠：

| 维度 | 项目 Skills | 插件 Skills (superpowers) |
|------|-------------|--------------------------|
| 定义位置 | `.claude/skills/` | 插件内置 |
| 作用范围 | 仅本项目 | 所有项目 |
| 关注点 | "做什么"——项目特有的规范、工具链、检查标准 | "怎么做"——通用方法论和流程框架 |
| 典型协作 | `running-project-tests` 定义本项目的 fixtures 和测试结构 | `test-driven-development` 提供 TDD 方法论框架 |
| 另一例 | `enforcing-project-standards` 定义本项目的审查维度和阈值 | `requesting-code-review` 提供审查请求流程 |

在实践中，一个典型工作流可能是：先用 `/writing-plans`（superpowers）产出实现计划，再用 `/executing-plans`（superpowers）分批执行，每批完成后自动触发 `/enforcing-project-standards`（项目 Skill）做代码审查。

### 插件安装/卸载

**安装**：在 `~/.claude/settings.json` 的 `enabledPlugins` 中添加插件标识：

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true
  }
}
```

插件标识格式为 `name@source`，官方插件的 source 统一为 `claude-plugins-official`。

**卸载**：将对应条目设为 `false` 或删除即可。

**项目级 vs 用户级**：项目级配置在 `.claude/settings.json`，用户级配置在 `~/.claude/settings.json`，均使用对象格式（`{ "name": true }`）。两级插件合并生效。

### 个人 Skills（~/.claude/skills/）

除了插件 Skills，还可以在 `~/.claude/skills/` 下放置个人 Skills，对所有项目生效。

推荐安装的 4 个个人 Skills：

| Skill | 功能 | 触发场景 |
|-------|------|----------|
| `generating-commit-messages` | 分析 git diff 生成规范 commit message，自动暂存并提交 | 提交代码变更时 |
| `squashing-commits` | 压缩/重组提交历史（全合一、按类型、按功能等方案） | 清理 git 历史 |
| `researching-with-sources` | 多源信息检索（WebSearch + Exa + Context7），带来源引用 | 调研最佳实践、对比工具、查库文档 |
| `thinking-before-coding` | brainstorming 的轻量版（3 分钟），提出 2-3 种方案再编码 | 需求模糊、≤3 文件的日常任务 |

创建方式与项目 Skills 相同，只是放在 `~/.claude/skills/` 而非 `.claude/skills/`。

## 6. 维护注意事项

### Git 入库策略

| 文件/目录 | 入 Git | 说明 |
|-----------|--------|------|
| `CLAUDE.md` | 是 | 项目入口，所有开发者共享 |
| `.claude/settings.json` | 是 | 团队共享的权限、Hooks、插件 |
| `.claude/rules/` | 是 | 项目规范 |
| `.claude/skills/` | 是 | 项目 Skills |
| `.claude/hooks/` | 是 | 项目 Hooks 脚本 |
| `CLAUDE.local.md` | 否 | 个人补充说明（gitignore） |
| `.claude/settings.local.json` | 否 | 个人权限累积（自动生成，gitignore） |
| `.claude/state/` | 否 | 运行时状态（session 数据，gitignore） |

### 验证方法

| 验证项 | 方法 |
|--------|------|
| Rule 是否加载 | 编辑对应路径文件，观察 Claude 回复是否遵循规则 |
| Skill 是否可用 | 输入 `/skills` 查看列表，或输入 `/skill-name` 手动触发 |
| Hook 是否生效 | 触发对应事件，观察 statusMessage 是否显示 |
| Hook 脚本权限 | `ls -la .claude/hooks/` 确认有 `x` 执行权限 |
| settings.json 语法 | Claude Code 启动时会报错；也可用 `jq . .claude/settings.json` 验证 JSON 格式 |
| MCP 服务器连接 | 启动 Claude Code 后输入 `/mcp` 查看服务器状态 |

### 常见问题排查

| 问题 | 排查方向 |
|------|----------|
| Skill 未触发 | 检查 `description` 触发词是否充分、`permissions.allow` 中是否有 `Skill(/name)` |
| Hook 不执行 | 检查脚本执行权限（`chmod +x`）、`settings.json` 中 `command` 路径是否正确、`timeout` 是否过短 |
| Hook exit 2 不生效 | 仅 `PreToolUse` 和 `UserPromptSubmit` 支持阻止，`PostToolUse`/`Stop` 的 exit 2 无效 |
| 条件规则未加载 | 确认 `paths` 字段的 glob 模式与实际编辑的文件路径匹配 |
| MCP 工具无权限 | 在 `permissions.allow` 中添加 `mcp__server-name__*` |
| settings.local.json 过大 | 可安全删除，Claude Code 会在需要时重新生成 |
| 插件未生效 | 确认插件标识拼写正确，重启 Claude Code |
