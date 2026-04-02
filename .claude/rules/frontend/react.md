---
paths: apps/frontend/**/*.{ts,tsx}
---

# React 前端开发规范

本规则仅在编辑 `apps/frontend/` 下的 TypeScript/React 文件时生效。

## 类型安全

- **禁止** 使用 `any` 类型
- 启用 strict mode
- 使用 `type` 而非 `interface`（除非需要扩展）

## Hooks 规范

- 所有依赖必须声明
- 使用函数式更新 `setState(prev => ...)`

## 校验

- 单文件 eslint 由 PostToolUse hook 自动执行
- 全量检查：`/enforcing-project-standards`（eslint + tsc）
- `pnpm build` 必须成功
- **禁止** `@ts-ignore` 或 `eslint-disable`

## 技术栈

- **React 19**（React Router 7）：函数组件 + Hooks
- **TypeScript 5.9**：严格模式
- **shadcn/ui**：可定制的 Radix UI 组件
- **Tailwind CSS 4.x**：实用优先 CSS
- **framer-motion**：声明式动画
- **lucide-react**：一致的图标系统

## 组件命名

- PascalCase 命名
- 文件名 = 组件名

## 快速示例

```tsx
// shadcn/ui 组件
import { Button } from "@/shared/components/ui/button"
<Button variant="default">Click me</Button>

// Tailwind 样式
<div className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow">

// framer-motion 动画
import { motion } from "framer-motion"
<motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>

// lucide 图标
import { Search } from "lucide-react"
<Search className="w-4 h-4 text-gray-500" />
```

## CSS 陷阱

- `hanging-punctuation` Chrome 不支持，禁用
- Tailwind utility 类会覆盖自定义 CSS，注意优先级
- 禁止 `!important`（反模式）

## 详细文档

- 前端开发指南：@docs/frontend/development.md
