# 前端代码质量规范

> 版本: v1.0 | 工具链: ESLint 10 + TypeScript ESLint 8 + TypeScript 5.9

## 配置概览

配置文件：`apps/frontend/eslint.config.js`

基于 `typescript-eslint` 的 **recommendedTypeChecked** 配置集，启用类型感知的静态检查，在 `tseslint.configs.recommended` 基础上增加了 Promise 误用检测、类型安全守卫等关键规则。

```
js.configs.recommended
  └── tseslint.configs.recommendedTypeChecked  ← 类型检查增强
        └── 项目自定义规则（~40 条）
```

## 规则体系

### 代码质量

基础编码规范，防止低质量代码进入仓库。

| 规则 | 级别 | 说明 |
|------|------|------|
| `no-console` | error | 仅允许 `console.error` / `console.warn` |
| `no-debugger` | error | 禁止 debugger |
| `no-alert` | error | 禁止 alert |
| `no-var` | error | 使用 `let` / `const` |
| `prefer-const` | error | 不重新赋值则用 `const` |
| `prefer-arrow-callback` | error | 回调使用箭头函数 |
| `prefer-template` | error | 使用模板字符串 |
| `no-param-reassign` | error | 禁止修改函数参数 |
| `no-implicit-coercion` | error | 禁止隐式类型转换 |
| `require-await` | error | async 函数必须包含 await |
| `no-return-await` | error | 禁止 `return await`（冗余） |
| `no-nested-ternary` | warn | 避免嵌套三元表达式 |
| `max-depth` | warn(4) | 嵌套深度上限 |
| `max-lines-per-function` | warn(300) | 函数行数上限（跳过空行和注释） |
| `complexity` | warn(20) | 圈复杂度上限 |

### TypeScript 核心规则

类型安全的关键防线，全部 error 级别。

| 规则 | 说明 |
|------|------|
| `no-explicit-any` | 禁止 `any` 类型 |
| `no-floating-promises` | Promise 必须被 `await` 或显式处理 |
| `no-misused-promises` | 禁止将 Promise 用在非预期位置（如条件判断） |
| `await-thenable` | 只能 `await` thenable 对象 |
| `switch-exhaustiveness-check` | switch 必须穷举所有联合类型分支 |

### TypeScript Unsafe 规则

对 `any` 传播的追踪，降级为 warn 以降低迁移成本。

| 规则 | 说明 |
|------|------|
| `no-unsafe-assignment` | 将 any 赋值给有类型的变量 |
| `no-unsafe-call` | 调用 any 类型的值 |
| `no-unsafe-member-access` | 访问 any 类型的属性 |
| `no-unsafe-return` | 从函数返回 any |
| `no-unsafe-argument` | 将 any 传入有类型的参数 |

### TypeScript 风格规则

| 规则 | 级别 | 说明 |
|------|------|------|
| `explicit-function-return-type` | off | 允许类型推断 |
| `strict-boolean-expressions` | off | 允许 truthy/falsy 判断 |
| `no-unnecessary-condition` | warn | 检测永远为真/假的条件 |
| `prefer-nullish-coalescing` | warn | 推荐 `??` 替代 `\|\|` |
| `prefer-optional-chain` | warn | 推荐 `?.` 替代 `&&` 链 |
| `prefer-readonly` | warn | 不修改的属性标记 readonly |

### 命名规范

通过 `@typescript-eslint/naming-convention` 强制执行：

| 目标 | 允许格式 | 示例 |
|------|----------|------|
| 变量 | camelCase, PascalCase, UPPER_CASE | `userName`, `UserCard`, `API_BASE` |
| 函数 | camelCase, PascalCase | `getUser`, `UserCard` |
| 类型/接口/枚举 | PascalCase | `UserResponse`, `Theme` |
| 接口 | PascalCase（禁止 `I` 前缀） | `User`（非 ~~`IUser`~~） |

### 导入规范

| 规则 | 级别 | 说明 |
|------|------|------|
| `consistent-type-imports` | warn | 类型导入使用 `import type` |
| `consistent-type-exports` | warn | 类型导出使用 `export type` |
| `no-duplicate-imports` | error | 禁止重复导入同一模块 |
| `sort-imports` | error | 同一 import 语句内成员按字母排序 |
| `no-unused-vars` | error | 未使用的变量（`_` 前缀豁免） |

### React 规则

| 规则 | 级别 | 说明 |
|------|------|------|
| `react-hooks/exhaustive-deps` | error | Hook 依赖数组必须完整 |
| `react-refresh/only-export-components` | error | 文件仅导出组件（HMR 兼容） |

## 类型检查启用

ESLint 配置启用了 `parserOptions.projectService`，这意味着 ESLint 能读取 `tsconfig.json` 进行类型分析。以下规则依赖此能力：

- `no-floating-promises` — 需要知道表达式是否为 Promise
- `no-misused-promises` — 需要知道回调签名
- `await-thenable` — 需要知道对象是否实现了 thenable
- `no-unsafe-*` 系列 — 需要追踪 `any` 的传播路径

## 执行方式

```bash
# 检查
pnpm --filter @bedrock/frontend lint

# 自动修复（sort-imports 等可自动修复的规则）
npx eslint . --fix

# CI 集成
pnpm --filter @bedrock/frontend lint --max-warnings 0
```

## 统一标准

本配置遵循全局前端 Lint 统一标准，各子服务保持一致。当前 bedrock 作为规范示例项目，省略了以下业务相关的文件覆盖：

| 省略项 | 原因 |
|--------|------|
| 无 logger.ts 文件覆盖 | bedrock 暂无 logger 模块 |
| 无 vite.config.ts 文件覆盖 | 同上 |

各子服务新增规则时应先在独立分支验证，确认无破坏性影响后再同步。
