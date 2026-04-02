---
description: "Run project tests: unit tests, integration tests, smart module selection"
---

# Running Project Tests

## 测试金字塔

```
     E2E
    /    \
  Integration
  /          \
    Unit Tests
```

## 目录结构

```
apps/backend/tests/
├── conftest.py              # 全局 fixtures
└── domain/
    └── user/
        ├── conftest.py      # 模块 fixtures
        ├── test_user_service.py
        └── test_user_api.py
```

## 运行命令

```bash
# 全部测试
cd apps/backend && pytest

# 特定模块
pytest tests/domain/user/ -v

# 特定测试
pytest tests/domain/user/test_user_service.py::test_create_user_success -v

# 带覆盖率
pytest --cov=backend --cov-report=term-missing
```

## 智能选择

根据变更文件自动选择测试：
- `domain/user/**` → `tests/domain/user/`
- `common/**` → 全部测试

## 约束

- 单元测试运行不超过 60s
- 测试必须独立，不依赖执行顺序
- Mock 外部依赖，不 mock 业务逻辑
