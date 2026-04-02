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
├── app/           # 应用层：路由、布局、Provider
├── features/      # 功能模块：按业务划分
│   └── user/
│       ├── components/   # 业务组件
│       ├── hooks/        # 业务 hooks
│       ├── api/          # API 请求
│       └── types/        # 类型定义
├── shared/        # 全局共享
│   ├── components/ui/    # shadcn/ui 组件
│   ├── hooks/            # 通用 hooks
│   ├── lib/              # 工具函数
│   └── types/            # 全局类型
└── styles/        # 设计系统
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
