---
title: "速查手册"
---

# Claude Code 速查手册

> 日常开发快速查阅。详细原理参见 [项目配置架构解析](./architecture.md)，定制方法参见 [进阶定制指南](./customization.md)。

## 1. 日常开发 Workflow

```text
启动 claude          编码 & 调试         审查质量             提交 & 发布
───────────────── → ───────────────── → ───────────────── → ─────────────────
claude / claude -w   正常对话开发         /enforcing-         /delivering-
claude -c (继续)     ! pnpm dev (验证)    project-standards   changes
@file 引用文件       /compact (压缩上下文) P0/P1 必须修复       lint→test→commit→PR
```

| 阶段 | 常用命令 / Skill | 说明 |
|------|-----------------|------|
| 需求分析 | `/brainstorming` | 需求探索，产出设计文档 |
| 方案设计 | `/writing-plans` | 设计文档转实现计划 |
| 编码实现 | `/executing-plans`、`/subagent-driven-development` | 按计划分批执行，或多 subagent 并行 |
| 测试 | `/running-project-tests`、`/test-driven-development` | 运行测试 / TDD 流程 |
| 审查 | `/enforcing-project-standards` | 7 步代码审查 + P0/P1 分级 |
| 调试 | `/systematic-debugging` | 系统化调试 |
| 提交 | `/delivering-changes` | lint → test → commit → PR 流水线 |
| 安全 | `/auditing-security` | OWASP Top 10 扫描 |
| 复盘 | `/reviewing-weekly-progress` | git history 分析 + 建议 |

## 2. 常用命令速查

### CLI 启动参数

| 命令 | 说明 |
|------|------|
| `claude` | 启动交互式 REPL |
| `claude -c` | 继续最近对话 |
| `claude -p "query"` | 一次性执行后退出 |
| `claude -w` / `claude --worktree` | 在 worktree 隔离环境启动 |
| `claude --model sonnet` | 指定模型（sonnet / opus / haiku） |
| `claude --add-dir ../other` | 添加额外工作目录 |
| `claude -r "id" "query"` | 按 ID 恢复会话 |

### Slash 命令

| 类别 | 命令 | 说明 |
|------|------|------|
| **核心** | `/help` | 帮助信息 |
| | `/clear` | 清空对话历史 |
| | `/compact [focus]` | 压缩上下文，可指定保留重点 |
| | `/exit` | 退出 |
| **会话** | `/resume` | 恢复历史会话 |
| | `/rewind` | 回退到上一轮对话 |
| | `/memory` | 编辑 CLAUDE.md 记忆 |
| | `/context` | 查看/管理上下文 |
| | `/tasks` | 查看后台任务 |
| **配置** | `/config` | 编辑配置 |
| | `/permissions` | 查看/编辑权限 |
| | `/model` | 切换模型 |
| | `/approved` | 查看已授权工具列表 |
| | `/denied` | 查看已拒绝工具列表 |
| **开发** | `/review` | 代码审查 |
| | `/pr_comments` | 查看 PR 评论 |
| **插件** | `/plugin` | 管理插件 |
| | `/skill` | 查看/触发 Skill |
| **状态** | `/status` | 当前状态 |
| | `/cost` | Token 用量与费用 |
| | `/stats` | 会话统计 |
| | `/doctor` | 诊断配置问题 |

### 快速前缀

| 前缀 | 功能 | 示例 |
|------|------|------|
| `/` | Slash 命令 | `/help` |
| `#` | 添加记忆到 CLAUDE.md | `# 记住用 pnpm` |
| `!` | 直接执行 bash | `! pnpm test` |
| `@` | 文件路径引用（自动完成） | `@src/main.ts` |

## 3. 键盘快捷键

### 通用控制

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+C` | 取消当前操作 |
| `Ctrl+D` | 退出 Claude Code |
| `Ctrl+L` | 清屏 |
| `Ctrl+O` | 切换详细模式（Verbose） |
| `Esc` `Esc` | 回滚上一步操作 |

### 模式切换

| 快捷键 | 功能 |
|--------|------|
| `Shift+Tab` / `Alt+M` | 权限模式切换（Auto-Accept / Plan / Normal） |
| `Option+P` / `Alt+P` | 切换模型 |

### 多行输入

| 快捷键 | 说明 |
|--------|------|
| `\` + `Enter` | 通用换行 |
| `Option+Enter` | macOS 换行 |
| `Shift+Enter` | 需先执行 `/terminal-setup` |
| `Ctrl+J` | 插入换行符 |

### Vim 模式

执行 `/vim` 启用。详见 [官方文档](https://docs.anthropic.com/en/docs/claude-code)。

## 4. 项目 Skills 速查

### 项目 Skills（`.claude/skills/`）

| Skill | 触发词 | 功能 | 何时用 |
|-------|--------|------|--------|
| `/enforcing-project-standards` | 审查代码、review、检查质量、重构 | 7 步代码审查 + P0/P1 分级 | 完成编码后 |
| `/running-project-tests` | 运行测试、写测试、pytest | 测试基础设施 + fixtures | 写/跑测试 |
| `/upgrading-dependencies` | 升级依赖、更新包、upgrade | pnpm/pip 升级 + 验证 | 升级依赖 |
| `/delivering-changes` | 提交、发 PR、push | lint → test → commit → PR 流水线 | 代码准备好后 |
| `/auditing-security` | 安全审计、OWASP | OWASP Top 10 扫描 | 新 API 上线前 |
| `/reviewing-weekly-progress` | 周回顾、retro | git history 分析 + 建议 | 周五复盘 |

### superpowers 插件 Skills（用户级安装）

> 需在 `~/.claude/settings.json` 中启用 superpowers 插件。安装方式见 [进阶定制指南](./customization.md#_5-用户级推荐配置)。

**3 个入口 Skills（用户直接调用）**

| 调用方式 | 功能 | 何时用 |
|----------|------|--------|
| `/superpowers:brainstorming` | 需求探索 → 多方案对比 → 设计文档 | 新功能开始前 |
| `/superpowers:writing-plans` | 设计文档 → 分步实现计划 | 设计审批后 |
| `/superpowers:executing-plans` | 按计划分批执行，每批设 checkpoint | 开始实现 |

核心链路：`brainstorming → writing-plans → executing-plans`

**内部自动触发的辅助 Skills（无需手动调用）**

| Skill | 自动触发时机 | 功能 |
|-------|-------------|------|
| `subagent-driven-development` | executing-plans 选 subagent 模式 | 每 Task 独立 subagent + 双阶段 review |
| `test-driven-development` | subagent 实施 Task | Red → Green → Refactor |
| `systematic-debugging` | 遇到 Bug/测试失败 | 假设 → 验证 → 修复 |
| `verification-before-completion` | 即将完成 Task | 运行验证命令确认 |
| `finishing-a-development-branch` | 所有 Task 完成 | merge / PR / cleanup 决策 |

### 个人 Skills（`~/.claude/skills/`）

| Skill | 功能 | 何时用 |
|-------|------|--------|
| `/generating-commit-messages` | 分析 diff 生成规范 commit message | 提交代码时 |
| `/squashing-commits` | 压缩/重组提交历史 | 清理 git history |
| `/researching-with-sources` | 多源检索（Exa + Context7 + WebSearch） | 调研/对比/查文档 |
| `/thinking-before-coding` | brainstorming 轻量版，3 分钟出方案 | 需求模糊、≤3 文件改动 |

## 5. Git Worktree 速查

### 启动方式

| 方式 | 命令 | 说明 |
|------|------|------|
| CLI 启动 | `claude -w` | 自动创建隔离 worktree |
| 会话中 | `EnterWorktree` 工具 | 中途切到 worktree |
| Subagent | `isolation: "worktree"` | Agent 在隔离环境执行 |

### 依赖共享策略

| 依赖 | 策略 | 说明 |
|------|------|------|
| `.venv` (2.3G) | 主目录共享 | `.envrc` 自动指向主目录 venv |
| `node_modules` | 按需独立安装 | `pnpm install`（hardlink，几乎不占磁盘） |
| `pnpm-lock.yaml` | 跟随分支 | 禁止 symlink node_modules |

### 生命周期命令

```bash
# 创建
git worktree add .worktrees/feature-name -b feature/feature-name

# 进入 & 初始化
cd .worktrees/feature-name && direnv allow
pnpm install                  # 仅改前端时需要

# 开发
claude

# 清理
cd /path/to/main-project && git worktree remove .worktrees/feature-name
```

## 6. 故障速查

| 问题 | 原因 | 解决 |
|------|------|------|
| Skill 未触发 | description 缺少触发词 | 补充触发词到 SKILL.md description |
| 条件规则未加载 | paths glob 不匹配 | 检查 frontmatter paths 是否覆盖目标文件 |
| Hook 报错 | 脚本无执行权限 | `chmod +x .claude/hooks/<script>.sh` |
| pyright 找不到 venv | direnv 未 allow | worktree 中执行 `direnv allow` |
| 权限被拒 | 未在 allow 列表 | 添加到 settings.json permissions.allow |
| ruff/pyright 命令找不到 | PATH 未配置 | 使用 `$RUFF_BIN` / `$PYRIGHT_BIN` 或确认 direnv |
| settings.local.json 膨胀 | 交互式授权累积 | 定期清理无用 allow 条目 |
| Worktree pip 依赖缺失 | 主目录新增了依赖 | 在主目录执行 pip install |
