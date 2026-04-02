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
