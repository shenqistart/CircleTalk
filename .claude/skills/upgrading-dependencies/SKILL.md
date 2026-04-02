---
description: "Upgrade project dependencies: frontend pnpm, backend uv/pip"
---

# Upgrading Dependencies

## 核心原则

- 只升级直接依赖
- Minor/Patch 直接升级
- Major 需要确认

## 3 步流程

### 1. 检查过期

**前端：**
```bash
pnpm outdated
```

**后端：**
```bash
cd apps/backend && uv pip list --outdated
```

### 2. 执行升级

**前端：**
```bash
pnpm update [package]
```

**后端：**
修改 `pyproject.toml` 中的版本约束，然后：
```bash
uv sync
```

### 3. 验证

```bash
# 前端
pnpm build && pnpm lint

# 后端
cd apps/backend && ruff check src/ && pyright src/ && pytest
```

## 输出格式

| Package | Current | Latest | Type | Status |
|---------|---------|--------|------|--------|
| react | 19.0.0 | 19.2.4 | minor | ✅ upgraded |
