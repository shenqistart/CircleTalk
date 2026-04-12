---
name: enforcing-project-standards
description: "Use when reviewing code quality, verifying architecture compliance, or running quality gates after task completion. Covers backend layering (FastAPI DI/Session/flush), frontend patterns (React features/shared), Electron safety, and confidence-based filtering."
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(ruff*)
  - Bash(pyright*)
  - Bash(pnpm*)
  - Bash(git*)
  - Bash(npx eslint*)
  - Bash(cd*)
---

# Bedrock Code Review Gate

## Anti-Rationalization

| 借口 | 现实 |
|------|------|
| "ruff/pyright 过了就行" | 不覆盖分层、Session、DI 规则 |
| "只改了一行" | 一行足以破坏分层或引入反向依赖 |
| "赶时间" | 跳过审查 = 违规 |
| "之前审查过了" | 每个 task/batch 独立审查 |

## Review Flow

### Step 1 -- 范围

指定文件直接审查 / 未指定用 `git diff --name-only` / 全量需显式指定

### Step 2 -- Plan 对齐（无 plan 则跳过）

遗漏 → P0 (95) / 偏离 → P1 (85) / 溢出 → P1 (80)

### Step 3 -- 静态分析

```bash
# 后端
cd apps/backend && ruff format src/ && ruff check --fix src/ && pyright src/
# 前端
cd apps/frontend && pnpm lint && pnpm build
```

### Step 4 -- 多维度检查

| 维度 | 置信度 |
|------|--------|
| 静态（ruff/pyright/eslint/tsc） | 95-100 |
| 逻辑（空指针/资源泄漏/死代码） | 90-95 |
| 架构（分层/Session/DI） | 80-90 |
| 安全（密钥/注入/Electron 安全基线） | 85-95 |
| 规范（CLAUDE.md + rules/） | 75-85 |

### Step 5 -- 过滤 + 输出

置信度 < 70 不输出。详见 FILTERS.md。

## 项目规则速查

**后端三层：** API → Service → Repository → Model

| 层 | 关键规则 |
|----|---------|
| API | @inject + Depends(Provide[...])；Depends(db_session) 获取 Session |
| Service | 首参 session:AsyncSession；写操作 flush()；不 commit |
| Repository | Singleton；显式接收 session；不 commit、不创建 Session |

**前端：** features/{domain}/ 按业务组织 → shared/ 全局共享 → styles/ 设计 token

**桌面端：** contextIsolation:true / nodeIntegration:false / Preload 只暴露具名方法

## Confidence & Handling

| 级别 | 分数 | 处理 |
|------|------|------|
| P0 | 90+ | 必须修复，修复后重跑验证。**禁止跳过。** |
| P1 | 70-89 | 成本低直接修，成本高报告用户。 |
| 设计建议 | - | 仅报告，不阻塞。 |

## Output Format

```
### Plan 对齐
- [OK] / [MISS] / [DRIFT]

### P0 -- 必须修复
- [file:line] (95) 问题 → 修复建议 | 来源: rule

### P1 -- 建议修复
- [file:line] (85) 问题 → 修复建议 | 来源: rule

### 设计建议
- 场景 → 推荐模式

结论: PASS / FAIL
```

## Deep Dive

- **FILTERS.md** -- 过滤规则 + 置信度映射（含项目特有 12 条后端 + 5 条前端信号）+ 输出前检查清单
- **PATTERNS.md** -- 三层详细规则 + Session 流转 + 前端分层 + React 模式 + SOLID + 命名 + 静态分析命令
