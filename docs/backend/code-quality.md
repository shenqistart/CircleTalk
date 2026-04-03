# 后端代码质量规范

> 版本: v1.0 | 工具链: Ruff 0.15 + Pyright 1.1 + Pytest 9

## 配置概览

配置文件：`apps/backend/pyproject.toml`

基于 Ruff 的 **29 个规则集**，覆盖代码风格、安全审计、复杂度控制、类型注解、异常处理等维度。配合 Pyright `standard` 模式的类型检查，形成完整的静态分析体系。

## 基础配置

```toml
[tool.ruff]
target-version = "py313"      # Python 3.13，支持 match-case 等现代语法
line-length = 120              # 行宽上限
fix = true                     # 自动修复可修复的问题
src = ["src"]                  # 源码根目录（影响导入排序的判断）
```

## 规则集总览

29 个规则集按用途分为六大类：

### 基础代码质量

| 规则集 | 代号 | 说明 |
|--------|------|------|
| pycodestyle | E, W | PEP 8 风格检查 |
| pyflakes | F | 未使用变量、未定义名称等基础错误 |
| flake8-bugbear | B | 常见 bug 模式（可变默认参数等） |
| flake8-simplify | SIM | 可简化的代码模式 |
| pyupgrade | UP | 使用现代 Python 语法（f-string、`\|` union 等） |
| flake8-comprehensions | C4 | 推导式优化（`list()` → `[]`） |
| Ruff 特有规则 | RUF | Ruff 专属检查（中文字符、冗余代码等） |

### 复杂度控制

| 规则集 | 代号 | 说明 |
|--------|------|------|
| mccabe | C90 | 圈复杂度上限 **10** |
| pylint | PL | 函数参数上限 **10**（适配 DI 场景）、嵌套深度等 |

### 安全审计

| 规则集 | 代号 | 说明 |
|--------|------|------|
| flake8-bandit | S | 硬编码密码、SQL 注入、不安全函数等安全问题 |
| flake8-debugger | T10 | 禁止残留 debugger 导入 |
| flake8-2020 | YTT | 检测 `sys.version` 误用 |

### 类型与注解

| 规则集 | 代号 | 说明 |
|--------|------|------|
| flake8-annotations | ANN | 函数参数和返回值必须有类型注解 |
| pygrep-hooks | PGH | 禁止 blanket `type: ignore` |

### 代码结构

| 规则集 | 代号 | 说明 |
|--------|------|------|
| isort | I | 导入排序（stdlib → third-party → local） |
| flake8-unused-arguments | ARG | 未使用的函数参数 |
| flake8-use-pathlib | PTH | 推荐 `pathlib` 替代 `os.path` |
| flake8-return | RET | return 语句优化（消除冗余赋值） |
| flake8-pie | PIE | 杂项优化（冗余 pass、不必要的 spread 等） |
| flake8-executable | EXE | 可执行权限检查 |
| flake8-import-conventions | ICN | 标准导入别名（`import numpy as np`） |
| refurb | FURB | 现代 Python 重构建议 |

### 异常与错误处理

| 规则集 | 代号 | 说明 |
|--------|------|------|
| flake8-errmsg | EM | 异常消息不直接内联字符串字面量 |
| tryceratops | TRY | 异常处理最佳实践（避免 broad except 等） |

### 代码卫生

| 规则集 | 代号 | 说明 |
|--------|------|------|
| flake8-pytest-style | PT | Pytest 最佳实践 |
| eradicate | ERA | 检测注释掉的代码 |
| flake8-todos | TD | TODO 注释规范 |
| flake8-fixme | FIX | FIXME 注释规范 |

## 中文支持

项目注释和文档使用中文，通过 `allowed-confusables` 配置避免 RUF003 对全角标点的误报：

```toml
allowed-confusables = ["，", "。", "！", "？", "：", "；", "（", "）", "【", "】", "《", "》", ...]
```

## 测试目录豁免

`tests/**/*.py` 下的测试文件豁免 23 条规则，覆盖以下场景：

| 场景 | 豁免规则 |
|------|----------|
| 断言使用 | S101 |
| 测试用硬编码密码 | S105, S106 |
| 魔法数字 | PLR2004 |
| Pytest 风格 | PT006, PT017 |
| 未使用变量/参数（fixture） | B007, ARG001, ARG002, F841, RUF059 |
| 类型注解（测试代码可省略） | ANN001, ANN002, ANN003, ANN201, ANN202, ANN401 |
| 异常消息格式 | EM101, EM102, TRY003 |
| 注释掉的代码 | ERA001 |
| 中文测试数据 | RUF001 |
| 按需导入 | PLC0415 |

## 格式化配置

```toml
[tool.ruff.format]
quote-style = "double"              # 双引号
indent-style = "space"              # 空格缩进
skip-magic-trailing-comma = false   # 保留尾逗号的展开格式
line-ending = "auto"                # 自动行尾
docstring-code-format = true        # 格式化 docstring 中的代码块
```

## Pyright 配置

```toml
[tool.pyright]
pythonVersion = "3.13"
typeCheckingMode = "standard"   # 标准模式（介于 basic 和 strict 之间）
```

关键检查项：
- 类型不匹配、缺失返回类型
- `None` 安全（可能为 None 的值未检查就使用）
- 导入解析错误
- 未定义的变量和属性

## Pytest 配置

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"                          # 自动处理 async 测试
asyncio_default_fixture_loop_scope = "function" # 每个测试函数独立事件循环
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-v --tb=short"
markers = [
    "no_setup: 不需要应用初始化的测试（如导入测试）",
    "integration: 集成测试（需要外部服务）",
    "slow: 慢速测试（如真实 LLM 调用）",
]
```

## 执行方式

```bash
# Ruff 检查
cd apps/backend && uv run ruff check src/

# Ruff 自动修复
cd apps/backend && uv run ruff check src/ --fix

# Ruff 格式化
cd apps/backend && uv run ruff format src/

# Pyright 类型检查
cd apps/backend && uv run pyright src/

# 运行测试
cd apps/backend && uv run pytest
```

## 统一标准

本配置遵循全局后端 Lint 统一标准，各子服务保持一致。当前 bedrock 作为规范示例项目，省略了以下业务相关的豁免配置：

| 省略项 | 原因 |
|--------|------|
| 无 LangGraph 节点延迟导入豁免 | bedrock 暂无 LangGraph 模块 |
| 无 LangChain 工具参数豁免 | bedrock 暂无 LangChain 工具 |
| 无 `--junitxml` 报告输出 | bedrock 暂未接入 CI 报告收集 |

各子服务新增规则时应先在独立分支验证，确认无破坏性影响后再同步。
