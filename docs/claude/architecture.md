---
title: "项目配置架构解析"
---

# 项目配置架构解析

> 前置知识：熟悉 Claude Code 基本概念（Rules、Skills、Hooks、Settings）。

本文解析 Bedrock 项目的 Claude Code 配置全貌，帮助开发者理解各配置文件的职责、加载机制和协作关系。

## 1. 配置全景图

### 项目级 vs 用户级

| 层级 | 路径 | 版本控制 | 作用范围 |
|------|------|----------|----------|
| **项目级** | `.claude/settings.json` | Git 跟踪 | 所有开发者共享的权限、Hooks、插件 |
| **项目级（本地）** | `.claude/settings.local.json` | gitignore | 个人累积的权限白名单（自动生成） |
| **用户级** | `~/.claude/settings.json` | 无 | 全局偏好、跨项目插件、安全钩子 |

项目级定义"团队规范"，用户级定义"个人工具链"。`settings.local.json` 是 Claude Code 在用户确认权限时自动追加的记录，不需要手动维护。

### 配置文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `CLAUDE.md` | 入口文件 | 项目结构、@ 引用、文档索引 |
| `.claude/settings.json` | Settings | 权限、Hooks、插件、语言 |
| `.claude/settings.local.json` | Settings (local) | 个人权限累积（gitignore） |
| `.claude/rules/principles.md` | Rule (核心) | 不可变原则 |
| `.claude/rules/workflow.md` | Rule (核心) | 任务执行流程 |
| `.claude/rules/quality.md` | Rule (核心) | 质量与性能标准 |
| `.claude/rules/git.md` | Rule (核心) | Git 工作流与提交规范 |
| `.claude/rules/backend/python.md` | Rule (条件) | Python 后端规范 |
| `.claude/rules/backend/conventions.md` | Rule (目录级) | 后端结构约定 |
| `.claude/rules/frontend/react.md` | Rule (条件) | React 前端规范 |
| `.claude/rules/frontend/converter.md` | Rule (条件) | Converter 服务规范 |
| `.claude/rules/frontend/conventions.md` | Rule (目录级) | 前端结构约定 |
| `.claude/skills/enforcing-project-standards/` | Skill | 代码审查门禁 |
| `.claude/skills/delivering-changes/` | Skill | 提交流水线 |
| `.claude/skills/running-project-tests/` | Skill | 测试基础设施 |
| `.claude/skills/upgrading-dependencies/` | Skill | 依赖升级 |
| `.claude/skills/auditing-security/` | Skill | 安全审计 |
| `.claude/skills/reviewing-weekly-progress/` | Skill | 周回顾 |
| `.claude/hooks/code-guard.sh` | Hook | 编辑后 lint + 模块追踪 |
| `~/.claude/hooks/safe-guard.sh` | Hook (用户级) | 全局危险命令拦截 |
| `~/.claude/skills/generating-commit-messages/` | Skill (个人) | 规范提交消息生成 |
| `~/.claude/skills/squashing-commits/` | Skill (个人) | 提交历史整理 |
| `~/.claude/skills/researching-with-sources/` | Skill (个人) | 多源信息检索 |
| `~/.claude/skills/thinking-before-coding/` | Skill (个人) | 编码前轻量方案分析 |

## 2. 分层加载机制

### 配置优先级链（5 层）

Claude Code 按以下顺序合并配置，后者覆盖前者：

```
1. Claude Code 内置默认值
2. 用户级 Settings    (~/.claude/settings.json)
3. 项目级 Settings    (.claude/settings.json)
4. 项目级本地 Settings (.claude/settings.local.json)
5. CLAUDE.md + Rules  (运行时注入 System Prompt)
```

权限取并集（allow 列表合并），Hooks 按层级叠加（用户级 + 项目级均生效）。

### CLAUDE.md 的 @ 引用策略

`CLAUDE.md` 通过 `@` 前缀控制文档的加载时机：

**常驻加载**（每次对话都注入 System Prompt）：

```markdown
- @docs/backend/architecture.md        — 后端架构与开发规范
- @docs/backend/dependency-injection.md — 依赖注入指南
```

**按需加载**（无 `@` 前缀，Claude 需要时用 Read 工具读取）：

```markdown
- docs/backend/chat-graph.md            — Chat Graph 开发指南
- docs/backend/knowledge/index.md       — Knowledge RAG 总览
- docs/frontend/development.md          — 前端开发指南
  ... (十余篇)
```

设计思路：常驻文件控制在 2 篇核心架构文档，避免 Context Window 浪费；其余文档按需读取，保证信息可达但不占用常驻空间。

### Rules 条件加载

Rules 通过 YAML frontmatter 的 `paths` 字段实现条件加载——仅当编辑匹配路径的文件时才注入：

```yaml
---
paths: apps/backend/**/*.py
---
```

无 `paths` 字段的 Rule 文件为核心规则，每次对话都加载。

## 3. Rules 体系解析

### 核心规则（4 个，无条件加载）

| 文件 | 职责 | 关键要点 |
|------|------|----------|
| `principles.md` | 不可变原则 | 质量第一、思考先行、DI > Factory > Inheritance、SOLID/DRY/YAGNI |
| `workflow.md` | 任务执行流程 | 检索优先、需求澄清、代码审查门禁（`/enforcing-project-standards` 必须执行） |
| `quality.md` | 质量标准 | 禁止 emoji 注释、重构阈值（函数 >80 行、嵌套 >3 层、重复 >3 次）、单测 <60s |
| `git.md` | Git 工作流 | Worktree 使用、.venv 共享/node_modules 独立、提交格式 `<emoji> <type>: <desc>` |

### 条件规则（3 个，paths frontmatter 加载）

| 文件 | paths frontmatter | 核心约束 |
|------|-------------------|----------|
| `backend/python.md` | `apps/backend/**/*.py` | Pyright 零错、Ruff 零警告、类型注解必需、禁止 `# noqa` |
| `frontend/react.md` | `apps/frontend/**/*.{ts,tsx}`, `apps/console/**/*.{ts,tsx}` | 禁止 `any`、strict mode、React 19 + shadcn/ui + Tailwind 4.x |
| `frontend/converter.md` | `apps/converter/**/*.ts` | strict: true、ESLint TypeScript recommended |

### 目录级规则（2 个，无 paths frontmatter）

以下规则放在 `rules/` 子目录中，没有 `paths` frontmatter。Claude Code 会基于目录结构自动关联加载：

| 文件 | 关联目录 | 核心约束 |
|------|----------|----------|
| `backend/conventions.md` | `apps/backend/` | 目录放置、pydantic-settings 配置、API 端点检查清单 |
| `frontend/conventions.md` | `apps/frontend/`, `apps/console/` | 页面/组件放置规则、i18n 必须 |

### 协作关系

```
principles.md (不可变原则)
    ├── workflow.md (执行流程，引用 enforcing-project-standards skill)
    ├── quality.md (质量标准，被 enforcing-project-standards skill 消费)
    └── git.md (Git 规范，被 delivering-changes skill 消费)

backend/python.md ──→ @docs/backend/architecture.md (常驻加载)
                  ──→ @docs/backend/session-signatures.md (按需)

frontend/react.md ──→ @docs/frontend/development.md (按需)
```

核心规则定义"做什么"和"怎么判断"，条件规则定义"具体怎么做"，Skills 执行具体动作时引用两者。

## 4. Skills 体系解析

Claude Code 的 Skills 来自三个层级，合并生效：

| 层级 | 路径 | 作用域 | 管理方式 |
|------|------|--------|----------|
| **项目 Skills** | `.claude/skills/` | 仅本项目 | Git 版本控制，团队共享 |
| **个人 Skills** | `~/.claude/skills/` | 所有项目 | 个人维护，不入项目 Git |
| **插件 Skills** | 插件内置 | 按插件启用范围 | `enabledPlugins` 配置 |

### 项目 Skills（6 个）

| Skill | Priority | 触发词示例 | 职责 |
|-------|----------|-----------|------|
| `enforcing-project-standards` | high | 审查代码、code review、重构 | 代码审查门禁（7 步流程） |
| `delivering-changes` | high | 提交、发PR、deliver | Lint→Test→Commit→PR 流水线 |
| `running-project-tests` | high | 运行测试、pytest | 测试金字塔、fixtures、模板 |
| `upgrading-dependencies` | medium | 升级依赖、outdated | pnpm/pip 升级 + 验证 |
| `auditing-security` | medium | 安全审计、OWASP | 攻击面扫描 + OWASP Top 10 |
| `reviewing-weekly-progress` | low | 周回顾、weekly review | git history + session 分析 |

### Skill 触发机制

Claude Code 根据 SKILL.md 的 `description` 字段进行语义匹配，自动识别并建议相关 Skill。无需额外配置触发规则——只要 `description` 写得充分，Claude 就能在合适的场景自动激活。

### enforcing-project-standards 详解

作为项目唯一的代码审查门禁，执行 7 步流程：

1. **Plan 对齐验证** — 检查实现是否与计划一致（遗漏 → P0，偏离 → P1）
2. **范围识别** — 确定审查文件（指定文件 / `git diff --name-only`）
3. **静态分析** — ruff + pyright（后端）、eslint（前端）
4. **多维度检查** — Plan 对齐、静态、逻辑、架构、规范五个维度
5. **重构检测** — 函数 >80 行、嵌套 >3 层、重复 >3 次
6. **架构检查** — 分层依赖、DI 规范、Session 传递
7. **命名检查 + 代码清理** — 命名规范、未使用导入、调试代码

置信度过滤机制：

| 分数 | 分类 | 处理 |
|------|------|------|
| 95-100 | P0 | 必须修复（编译错误、Plan 遗漏） |
| 90-94 | P0 | 必须修复（逻辑错误） |
| 80-89 | P1 | 建议修复（架构/安全） |
| 70-79 | P1 | 建议修复（规范违反） |
| <70 | -- | 不输出（置信度不足） |

支持文件：`FILTERS.md`（高信号过滤规则）、`PATTERNS.md`（重构模式速查）、`FLUTTER.md`（移动端补充）。

### 项目级插件

| 插件 | 来源 | 职责 |
|------|------|------|
| `code-review` | claude-plugins-official | PR 变更审查 |
| `code-simplifier` | claude-plugins-official | 代码重构简化 |
| `frontend-design` | claude-plugins-official | 前端设计组件生成 |

与项目 Skills 的分工：`enforcing-project-standards` 管开发中审查，`code-review` 管 PR 审查，`code-simplifier` 管代码清理。

### 用户级插件

用户级插件配置在 `~/.claude/settings.json`，不随项目入 Git，需每位开发者自行安装。

| 插件 | 来源 | 职责 |
|------|------|------|
| `superpowers` | claude-plugins-official | 方法论 Skills 套件（覆盖软件开发全生命周期） |
| `pyright-lsp` | claude-plugins-official | Pyright LSP 集成（实时类型检查、跳转定义） |

#### superpowers 工作流

superpowers 提供 **3 个用户可直接调用的入口 Skill** + 多个工作流内部自动触发的辅助 Skill：

**入口 Skills（用户通过 `/` 命令调用）**

| 入口 Skill | 调用方式 | 产出 |
|-----------|----------|------|
| `brainstorming` | `/superpowers:brainstorming` | 需求探索 → 多方案对比 → 设计文档（spec） |
| `writing-plans` | `/superpowers:writing-plans` | 设计文档 → 分步实现计划（含文件清单、代码、测试） |
| `executing-plans` | `/superpowers:executing-plans` | 按计划分批执行，每批设 checkpoint 审查 |

三者构成核心工作流链：`brainstorming → writing-plans → executing-plans`。

**内部自动触发的辅助 Skills（无需手动调用）**

以下 Skills 由入口 Skill 在工作流执行过程中自动调用：

| 辅助 Skill | 自动触发时机 | 功能 |
|-----------|-------------|------|
| `subagent-driven-development` | executing-plans 选择 subagent 模式时 | 每 Task 独立 subagent + 双阶段 review |
| `test-driven-development` | subagent 实施 Task 时 | Red → Green → Refactor 循环 |
| `systematic-debugging` | 遇到 Bug/测试失败时 | 假设 → 验证 → 修复 |
| `verification-before-completion` | 即将完成 Task 时 | 运行验证命令，证据先于断言 |
| `requesting-code-review` | Task 完成后 | 发起代码审查 |
| `receiving-code-review` | 收到审查反馈后 | 技术验证而非盲从 |
| `using-git-worktrees` | 需要隔离开发时 | 创建 worktree |
| `dispatching-parallel-agents` | 2+ 个无依赖 Task 时 | 并行调度 agent |
| `finishing-a-development-branch` | 所有 Task 完成后 | merge / PR / cleanup 决策 |
| `using-superpowers` | 每次会话启动时（自动） | 检测可用 Skills 并引导使用 |

#### superpowers 与项目 Skills 的协作

```
superpowers 入口 (用户调用)         内部自动触发              项目 Skills (规范)
─────────────────────────         ──────────────          ──────────────────
/brainstorming
    ↓
/writing-plans
    ↓
/executing-plans ──→ TDD ─────────────────────────→ /running-project-tests
    │            ──→ verification ─────────────────→ /enforcing-project-standards
    │            ──→ finishing-branch ─────────────→ /delivering-changes
    └──────────────→ systematic-debugging (按需)      /auditing-security
```

| 维度 | superpowers | 项目 Skills |
|------|-------------|-------------|
| 关注点 | "怎么做"——通用方法论和流程框架 | "做什么"——项目特有规范和检查标准 |
| 调用方式 | 3 个入口手动调用，其余自动触发 | 触发词匹配 / 手动 `/skill` |
| 作用域 | 所有项目通用 | 仅本项目 |
| 配置位置 | `~/.claude/settings.json` | `.claude/skills/` |

### 个人 Skills（`~/.claude/skills/`）

个人 Skills 存放在用户主目录下，对所有项目生效，不入项目 Git。适合放个人工作习惯和跨项目通用流程。

当前配置的 4 个个人 Skills：

| Skill | 触发场景 | 功能 |
|-------|----------|------|
| `generating-commit-messages` | 提交代码变更时 | 分析 git diff，生成符合项目提交规范的 commit message（emoji + type + desc），自动暂存并执行提交 |
| `squashing-commits` | 清理 git 历史时 | 将多个提交压缩/重组为逻辑清晰的提交历史，支持全合一、按类型分组、按功能分组等多种方案 |
| `researching-with-sources` | 调研最佳实践、对比工具、查询库文档时 | 多源信息检索（WebSearch + Exa + Context7），综合分析对比，带来源引用 |
| `thinking-before-coding` | 即将实现模糊需求时 | brainstorming 的轻量版（3 分钟），提出 2-3 种方案后再编码，适合 ≤3 文件的日常任务 |

#### 三层 Skills 协作示例

```
用户: "优化一下搜索性能"
    ↓
thinking-before-coding (个人)     ── 3 分钟分析，提出 2-3 方案
    ↓ 用户选定方案
TDD (superpowers 插件)            ── 按 Red→Green→Refactor 实施
    ↓ 每轮完成
enforcing-project-standards (项目) ── 代码审查门禁
    ↓ 准备提交
generating-commit-messages (个人)  ── 生成规范 commit message
```

#### 个人 Skills vs 项目 Skills

| 维度 | 个人 Skills | 项目 Skills |
|------|-------------|-------------|
| 路径 | `~/.claude/skills/` | `.claude/skills/` |
| 作用域 | 所有项目 | 仅本项目 |
| 版本控制 | 无（个人维护） | Git 跟踪（团队共享） |
| 内容偏向 | 个人工作习惯、通用流程 | 项目特有规范、工具链 |
| 新成员需求 | 推荐安装（非必需） | 自动可用（Git 克隆即得） |

## 5. Hooks 工作流

### 设计思路

项目仅使用一个 Hook：`code-guard.sh`（PostToolUse: Edit|Write），负责编辑后的 lint 检查和模块追踪。

### code-guard.sh 详解

**触发**: PostToolUse，matcher `Edit|Write`（每次文件编辑后）

3 个阶段顺序执行：

| 阶段 | 功能 | 退出码影响 |
|------|------|-----------|
| Phase 0: freeze-scope | 检查文件是否在锁定范围外 | `exit 2` 阻止 |
| Phase 1: lint-check | 后端 ruff + pyright，前端 eslint | 有错误 `exit 2` |
| Phase 2: file-tracking | 记录编辑文件 + 模块识别（去重） | 无 |

**Phase 0 — Freeze Scope**

通过 `.claude/state/$SESSION_ID/freeze-scope.txt` 锁定编辑范围，防止 Claude 在执行特定任务时编辑范围外的文件。

**Phase 1 — Lint & Type Check**

| 文件类型 | 检查工具 | 行为 |
|----------|---------|------|
| `.py`（apps/backend/） | ruff format + ruff check + pyright（15s timeout） | 有错误 `exit 2`，stderr 反馈给 Claude 自动修复 |
| `.ts`/`.tsx` | 项目内 eslint binary（非 npx） | 有错误 `exit 2` |
| 其他 | 跳过 | — |

`exit 2` 不能撤销已完成的编辑，但会将 stderr 反馈给 Claude，提示其自动修复。

**Phase 2 — File Tracking**

写入 `.claude/state/$SESSION_ID/` 下的状态文件：

| 文件 | 写入策略 | 用途 |
|------|---------|------|
| `edited-files.log` | 每次追加（保留时间线） | 记录所有编辑过的文件 |
| `module-impact.log` | 去重写入（同模块只记一次） | 记录受影响模块 + 推荐测试命令 |
| `freeze-scope.txt` | 用户手动创建 | 锁定编辑范围 |

模块识别覆盖：chat、knowledge、analytics、metadata、permission、search、common、adapter、frontend、console、converter、docs、claude-config 等。

### 用户级安全钩子

```json
// ~/.claude/settings.json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": "/Users/yaoguohh/.claude/hooks/safe-guard.sh",
        "timeout": 5,
        "statusMessage": "Safety check..."
      }]
    }]
  }
}
```

`safe-guard.sh` 在 PreToolUse 阶段拦截危险 bash 命令，作为全局安全网，独立于项目配置。

## 6. Settings 配置要点

### settings.json vs settings.local.json

| 配置项 | `settings.json` (团队共享) | `settings.local.json` (个人) |
|--------|---------------------------|------------------------------|
| 权限白名单 | 精心设计的通用工具集 | 自动累积的一次性权限 |
| Hooks | 1 个项目 Hook（code-guard） | 无 |
| 插件 | 3 个项目插件 | 同步复制（可有差异） |
| 语言 | `"chinese"` | 无 |
| Git 跟踪 | 是 | 否 |

### 权限白名单设计

`settings.json` 的 `permissions.allow` 按用途分组：

```jsonc
// 开发工具
"Bash(pnpm *)", "Bash(python *)", "Bash(pip *)", "Bash(uv *)",
"Bash(npm *)", "Bash(npx *)", "Bash(git *)", "Bash(curl *)",
"Bash(ruff *)", "Bash(pyright *)", "Bash(pytest *)",
"Bash(alembic *)", "Bash(docker *)", "Bash(kubectl *)", "Bash(gh *)",

// 文件操作（节选）
"Bash(ls)", "Bash(ls *)", "Bash(find *)", "Bash(grep *)",
"Bash(cat *)", "Bash(mkdir *)", "Bash(rm *)", "Bash(mv *)", "Bash(cp *)",
// ... 完整列表见 .claude/settings.json

// Web 访问（限定域名）
"WebSearch",
"WebFetch(domain:github.com)",
"WebFetch(domain:pypi.org)",
"WebFetch(domain:docs.python.org)",

// MCP 工具（通配符）
"mcp__context7__*", "mcp__exa__*", "mcp__chrome-devtools__*",

// Skills（显式列举）
"Skill(/enforcing-project-standards)", "Skill(/delivering-changes)", ...
```

设计原则：
- `defaultMode: "acceptEdits"` — 文件编辑默认允许，减少确认次数
- 开发工具用通配符（`Bash(pnpm *)`），Web 访问限定域名，Skill 显式列举
- 未在白名单中的操作需用户确认，确认后自动追加到 `settings.local.json`

### MCP 服务器

通过 `"enableAllProjectMcpServers": true` 启用所有项目级 MCP 服务器：

| MCP Server | 用途 |
|------------|------|
| context7 | 第三方库文档检索（最新版 API/示例） |
| exa | Web 搜索引擎（深度搜索） |
| chrome-devtools | 浏览器开发者工具集成 |

### 插件配置

**项目级**（`.claude/settings.json`）：

```json
{
  "enabledPlugins": {
    "code-review@claude-plugins-official": true,
    "code-simplifier@claude-plugins-official": true,
    "frontend-design@claude-plugins-official": true
  }
}
```

**用户级**（`~/.claude/settings.json`）：

```json
{
  "enabledPlugins": {
    "superpowers@claude-plugins-official": true,
    "pyright-lsp@claude-plugins-official": true
  }
}
```

两级插件合并生效。superpowers 和 pyright-lsp 放在用户级是因为它们是通用工具，不限于本项目。

### language 配置

```json
{ "language": "chinese" }
```

Claude Code 的所有输出（解释、建议、报告）使用中文，代码和技术术语保持英文。
