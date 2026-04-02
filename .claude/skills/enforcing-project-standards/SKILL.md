---
description: "Code review gate: plan alignment + static analysis + architecture layering + naming conventions"
---

# Enforcing Project Standards

代码审计技能：plan 对齐、静态分析、多维度检查、高信噪比过滤。

## 何时执行

- 每个 task/batch 完成后（必须）
- PR 创建前
- 用户主动调用

## 反合理化

| 你的想法 | 实际 |
|---------|------|
| "只改了一行" | 一行也可能破坏架构 |
| "之前审查过了" | 每个 task 必须独立审查 |
| "赶时间" | 跳过审查 = 违规 |

## 执行步骤

### 1. 范围识别

确认本次变更涉及的文件和模块。

### 2. 静态分析

**Python 后端：**
```bash
cd apps/backend && ruff format src/ && ruff check --fix src/ && pyright src/
```

**TypeScript 前端：**
```bash
cd apps/frontend && pnpm lint && pnpm build
```

### 3. 多维度检查

| 维度 | 检查内容 |
|------|----------|
| **Plan** | 实现是否与 plan 对齐？有无遗漏或多余？ |
| **Static** | ruff/pyright/eslint/tsc 零错误？ |
| **Logic** | 业务逻辑是否正确？边界情况？ |
| **Architecture** | 分层是否正确？依赖方向？ |
| **Standards** | 命名规范？响应格式？路由顺序？ |

### 4. 高信噪比过滤

仅报告置信度 >= 70 的发现。参考 FILTERS.md。

### 5. 架构检查

**后端：** API → Service → Repository → Model，禁止反向依赖。
**前端：** Components → Hooks → API → Types。

### 6. 输出格式

```
## 审查结果

**范围：** [涉及的文件/模块]

### P0（必须修复）
- [文件:行号] 问题描述（置信度 95+）

### P1（应修复）
- [文件:行号] 问题描述（置信度 80-94）

### 设计建议
- 建议内容（置信度 70-79，不阻塞）

**结论：** PASS / FAIL
```
