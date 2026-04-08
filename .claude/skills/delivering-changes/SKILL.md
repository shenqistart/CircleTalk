---
description: "Deliver changes: preflight check, lint, test, commit, PR creation"
---

# Delivering Changes

代码准备提交时使用的交付流水线。

## 5 步流水线

```
Preflight → Lint → Test → Commit → PR
```

### Step 1: Preflight

```bash
git status
git diff --staged
```

检查是否有未暂存的文件。

### Step 2: Static Check

**Python：**
```bash
cd apps/backend && ruff format src/ && ruff check --fix src/ && pyright src/
```

**TypeScript：**
```bash
cd apps/frontend && pnpm lint
```

如有错误，自动修复后重新检查。

### Step 3: Test

```bash
cd apps/backend && pytest -v
```

确认所有测试通过。

### Step 4: Commit

根据变更内容生成提交消息：
- 使用 `type(scope): description` 格式（Conventional Commits）
- 标题简洁聚焦 "why"
- 可选详细描述

### Step 5: PR（可选）

```bash
gh pr create --title "标题" --body "描述"
```

## 错误恢复

| 阶段 | 失败处理 |
|------|----------|
| Lint | 自动修复，重新检查 |
| Test | 分析失败原因，修复后重跑 |
| Commit | 检查 hook 错误，修复后重新提交 |
