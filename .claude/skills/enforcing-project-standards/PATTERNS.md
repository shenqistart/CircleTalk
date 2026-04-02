# 检查模式参考

## 设计优先级

依赖注入 > 工厂模式 > 继承

## 代码坏味道 → 重构手法

| 坏味道 | 重构手法 |
|--------|---------|
| 长函数 (>80行) | Extract Method |
| 深嵌套 (>3层) | Guard Clause / Early Return |
| 重复代码 (>3次) | Extract Function / Template Method |
| 过长参数列表 | Parameter Object |
| 数据泥团 | Extract Class |

## 分层架构检查

### 后端

```
API → Service → Repository → Model
```

- API 不直接访问 Repository
- Service 不直接返回 HTTP 响应
- Repository 不管理事务
- Model 不包含业务逻辑

### 前端

```
Components → Hooks → API → Types
```

- 组件不直接调用 API
- Hooks 封装数据获取逻辑
- API 层统一管理请求
- Types 定义数据结构

## SOLID 原则速查

| 原则 | 检查点 |
|------|--------|
| S - 单一职责 | 一个类/函数是否只做一件事？ |
| O - 开闭原则 | 扩展是否不需要修改现有代码？ |
| L - 里氏替换 | 子类是否可以替换父类？ |
| I - 接口隔离 | 接口是否足够小？ |
| D - 依赖反转 | 是否依赖抽象而非具体？ |

## 命名规范

### Python
- 类：PascalCase
- 函数/变量：snake_case
- 常量：UPPER_SNAKE_CASE
- 私有：_leading_underscore

### TypeScript/React
- 组件：PascalCase
- 函数/变量：camelCase
- 类型：PascalCase
- 常量：UPPER_SNAKE_CASE
- Hook：use 前缀
