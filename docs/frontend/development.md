# 前端开发指南

> 版本: v1.0

## 技术栈

- **React 19** + **TypeScript 5.9**（严格模式）
- **Vite** 构建
- **Tailwind CSS 4.x** + **shadcn/ui**
- **TanStack Query** 数据请求
- **React Router 7** 路由
- **lucide-react** 图标
- **framer-motion** 动画

## 构建工具选型

### 当前选择：Vite

B 端管理后台使用 Vite + React SPA 架构，原因：

- 后端已有独立的 FastAPI 服务，Next.js 全栈能力（API Routes / Server Actions / RSC 直连数据库）无法发挥
- 登录后使用的 B 端系统无 SEO 需求，SSR 收益极小
- Vite 开发体验更优：冷启动 ~300ms，插件生态 800+，Vite 8 已切换 Rolldown (Rust) 引擎

### 何时引入 Next.js

当出现以下场景时，在 monorepo 中新增 Next.js 应用（如 `apps/portal/`），与现有 Vite 应用共存：

| 场景 | 收益 |
|------|------|
| C 端招聘门户 / 官网 | SSR 首屏 + SEO + `next/image` 响应式优化 |
| 移动端弱网访问的公开页面 | Streaming SSR + 渐进渲染，TTFB/FCP/LCP 显著优于 CSR |
| 全栈一体的轻量独立应用 | API Routes + RSC 减少前后端协调成本 |

### 共享组件库

跨应用共享的 UI 组件使用 Vite Library Mode 打包，放在 `packages/ui/`，B 端和 C 端应用均可引用。

## 项目结构

```
src/
├── App.tsx                          # 根组件
├── main.tsx                         # 入口文件
├── index.css                        # 全局样式
├── app/                             # 应用层
│   ├── layouts/AppLayout.tsx        # 主布局
│   ├── providers/QueryProvider.tsx  # TanStack Query 配置
│   ├── providers/ThemeProvider.tsx  # 主题 Provider
│   └── routes/index.tsx             # 路由定义
├── features/                        # 功能模块：按业务划分
│   └── user/                        # 用户管理（示例模块）
│       ├── api/userApi.ts           # API 请求
│       ├── components/              # 业务组件
│       │   ├── UserForm.tsx
│       │   ├── UserStatusToggle.tsx
│       │   └── UserTable.tsx
│       ├── hooks/useUsers.ts        # 业务 hooks
│       └── types/index.ts           # 类型定义
├── shared/                          # 全局共享
│   ├── hooks/usePagination.ts       # 通用 hooks
│   ├── lib/                         # 工具函数
│   │   ├── request.ts               # HTTP 请求封装
│   │   └── utils.ts                 # 通用工具
│   └── types/api.ts                 # 全局类型
└── styles/                          # 设计系统
    └── tokens/colors.css            # 设计 token（CSS 变量）
```

## 组件规范

- PascalCase 命名，文件名 = 组件名
- 禁止 `any` 类型
- 组件 >150 行考虑拆分
- Hook 依赖必须完整

## API 请求模式

```typescript
// features/user/api/userApi.ts
import { request } from '@/shared/lib/request'

export const userApi = {
  search(params) { return request('get', '/users', undefined, params) },
  create(data) { return request('post', '/users', data) },
}

// features/user/hooks/useUsers.ts
import { useQuery } from '@tanstack/react-query'

export function useUsers(params) {
  return useQuery({ queryKey: ['users', params], queryFn: () => userApi.search(params) })
}
```

## 设计 Token

通过 CSS 变量定义，Tailwind 引用：

```css
:root {
  --color-primary: 222.2 47.4% 11.2%;
  --color-background: 0 0% 100%;
  --radius: 0.5rem;
}
```

## 开发命令

```bash
pnpm --filter @bedrock/frontend dev     # 开发服务器
pnpm --filter @bedrock/frontend build   # 构建
pnpm --filter @bedrock/frontend lint    # ESLint 检查
```
