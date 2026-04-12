# High-Signal Filtering Rules

## 应报告

### 1. 编译/类型错误 (95-100)
pyright/TS 报错、语法错误、导入/循环导入

### 2. 逻辑错误 (90-95)
空指针/None、未处理异常、资源泄漏、死代码

### 3. 架构违反 (80-90)

**后端特有信号：**

| 违反 | 置信度 |
|------|--------|
| Repository 内 commit/创建 Session | 90 |
| Service 缺少 session 首参 | 88 |
| Service 内 commit（应由 middleware 管理） | 88 |
| API 直接调用 Repository | 88 |
| Service 写操作未 flush | 85 |
| API 缺少 @inject | 85 |
| DI 未注册（新增 Service/Repository 未在 container.py 注册） | 85 |
| 使用 `from src.xxx`（应 `from domain.xxx`） | 80 |
| 使用 `os.environ`（应 pydantic-settings） | 80 |
| 路由顺序错误（参数化在静态前） | 78 |
| 响应未封装 success_response() | 78 |
| 反向依赖（内层 import 外层） | 85 |

**前端特有信号：**

| 违反 | 置信度 |
|------|--------|
| 组件直接 fetch/axios | 82 |
| 使用 `any` 类型 | 82 |
| features/ 跨域直接导入 | 80 |
| 使用 `@ts-ignore` / `eslint-disable` | 80 |

**Electron 特有信号：**

| 违反 | 置信度 |
|------|--------|
| nodeIntegration:true 或 contextIsolation:false | 95 |
| Preload 透传 ipcRenderer | 88 |
| Renderer 访问 Node.js API | 85 |

### 4. 安全 (85-95)
硬编码密钥、SQL 注入、未验证输入、敏感信息泄漏

### 5. 规范违反 (75-85)
命名违反、`# noqa` / `# type: ignore`（Pydantic **kwargs 除外）

## 不应报告

| 类别 | 原因 |
|------|------|
| 风格问题 | linter 已处理 |
| 潜在问题 | "可能会"/"或许" -- 不确定不报 |
| 主观建议 | "我觉得" -- 无规则支撑不输出 |
| 已存在问题 | 非当前变更引入 |
| 有意抑制 | 已标记 noqa 等 |

## 置信度映射

| 具体项 | 置信度 | 级别 |
|--------|--------|------|
| 语法错误 | 100 | P0 |
| pyright/TS 报错 | 98 | P0 |
| 导入错误 | 95 | P0 |
| 硬编码密钥 / Electron nodeIntegration:true | 95 | P0 |
| 空指针/None | 92 | P0 |
| SQL 注入 | 92 | P0 |
| 未处理异常 | 90 | P0 |
| Repository commit/创建 Session | 90 | P0 |
| 资源泄漏 | 88 | P1 |
| Service 缺 session 首参 | 88 | P1 |
| API 直调 Repository | 88 | P1 |
| Repository flush（flush 应由 Service 负责） | 85 | P1 |
| Preload 透传 ipcRenderer | 88 | P1 |
| 反向依赖 | 85 | P1 |
| 死代码 | 85 | P1 |
| 未验证输入 | 85 | P1 |
| 分层穿透 / 组件直调 API | 82 | P1 |
| from src.xxx / os.environ | 80 | P1 |
| 命名规范 | 75 | P1 |
| 函数 > 80 行 / 嵌套 > 3 层 / 重复 > 3 次 | 70-72 | P1 |

## 输出前检查清单

- [ ] 有规则支撑？
- [ ] 在审查范围内？
- [ ] 未被 linter 覆盖？
- [ ] 无抑制注释？
- [ ] 置信度 >= 70？
- [ ] 可操作？

全部通过后方可输出。
