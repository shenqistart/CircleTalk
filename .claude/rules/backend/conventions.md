---
paths: apps/backend/**/*.py
---

# 后端结构约定

条件加载：编辑 apps/backend/ 下文件时自动加载。

## 目录放置

| 新增内容 | 放置位置 |
|---------|---------|
| 新业务域 | `domain/{api,service,repository,model,schema}/` |
| 新配置项 | `core/config.py` 对应 Settings 类 |
| 新外部适配器 | `core/adapter/<name>/` |
| 新工具函数 | `core/utils/`（禁止在 domain 内建 utils） |

## 配置文件

- `.env` 变量 → `core/config.py` 中用 pydantic-settings 声明
- 禁止直接 `os.environ`，通过 Settings 类注入
- 新增配置项时检查是否已有相关 Settings 类

## 新 API 端点检查清单

新增 API 端点前确认：
1. 路由顺序：静态路径在参数化路径之前
2. 响应格式：`success_response` / `pageable_success_response`
3. 权限：是否需要权限检查
4. Session：HTTP 用 `Depends(db_session)`，后台任务用 `scoped_session(tenant)`
5. 注入：`@inject` 紧贴函数，路由装饰器在外层
