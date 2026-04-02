---
paths: apps/desktop/**/*.{ts,tsx}
---

# Electron 桌面端开发规范

本规则仅在编辑 `apps/desktop/` 下的 TypeScript 文件时生效。

## 进程职责

| 进程 | 职责 | 禁止 |
|------|------|------|
| **Main** | 窗口管理、系统 API、IPC 调度 | 禁止 UI 逻辑、禁止阻塞操作 |
| **Preload** | contextBridge 桥接，暴露最小化 API | 禁止业务逻辑、禁止透传 ipcRenderer |
| **Renderer** | UI 渲染（React），遵循 react.md 全部规范 | 禁止访问 Node.js API |

## 安全基线（不可违背）

- `contextIsolation: true` — 永远开启（Electron 12+ 默认）
- `nodeIntegration: false` — 永远关闭
- `sandbox: true` — 永远开启（Electron 20+ 默认）
- `webSecurity: true` — 保持同源策略
- **禁止** 使用已废弃的 `remote` 模块
- **禁止** 在 Preload 中透传 `ipcRenderer` 全量对象
- **禁止** `@ts-ignore` 或 `eslint-disable`

## IPC 通信

### 通道命名

格式：`<namespace>:<action>`，如 `file:read`、`app:get-version`、`dialog:open-file`

### 通信模式

| 模式 | 场景 | API |
|------|------|-----|
| 请求/响应（首选） | 读取数据、执行操作 | `ipcRenderer.invoke` / `ipcMain.handle` |
| 单向（Renderer→Main） | 日志、通知 | `ipcRenderer.send` / `ipcMain.on` |
| 推送（Main→Renderer） | 状态变更、事件广播 | `webContents.send` / preload 注册监听 |

- **首选** `invoke/handle`（Promise-based，最安全）
- **禁止** `ipcRenderer.sendSync`（阻塞 UI 线程）

### 类型安全

所有 IPC 通道必须在 `src/shared/types/electron.d.ts` 中声明类型：

```typescript
export interface IElectronAPI {
  readFile: (path: string) => Promise<{ success: boolean; content?: string }>
  getAppInfo: () => Promise<{ version: string; platform: string }>
  onUpdateAvailable: (callback: (data: { version: string }) => void) => void
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
```

### Preload 暴露规范

只暴露具名方法，不暴露通用通道：

```typescript
// 正确：暴露具名方法
contextBridge.exposeInMainWorld('electronAPI', {
  loadPreferences: () => ipcRenderer.invoke('settings:load'),
})

// 错误：暴露通用 send
contextBridge.exposeInMainWorld('electronAPI', {
  send: (channel, ...args) => ipcRenderer.send(channel, ...args),
})
```

## 路由

Renderer 使用 **HashRouter**（`file://` 协议不支持 History API）

## 构建工具

- 构建：**electron-vite**（`defineConfig` 管理 main/preload/renderer 三进程）
- 打包：**electron-builder**
- 更新：**electron-updater**
- TypeScript：双 tsconfig（`tsconfig.node.json` + `tsconfig.web.json`）

## 性能约束

- Main 进程禁止阻塞操作，CPU 密集任务用 Worker Threads
- IPC 避免高频小消息，大数据批量传输
- Renderer 侧遵循 react.md 性能规范

## 详细文档

- Electron 开发指南：@docs/frontend/electron.md
