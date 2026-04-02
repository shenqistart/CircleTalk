# Electron 桌面端开发指南

> 版本: v1.0

## 技术栈

- **Electron 39** + **TypeScript 5.9**（严格模式）
- **electron-vite** 构建（统一管理 main/preload/renderer 三进程）
- **electron-builder** 打包分发
- **electron-updater** 自动更新
- **@electron-toolkit/utils** 主进程工具
- **@electron-toolkit/preload** Preload 脚本桥接
- Renderer 侧复用 Web 前端技术栈（React 19 + shadcn/ui + Tailwind CSS 4.x + Zustand + TanStack Query）

## 构建工具选型

### 当前选择：electron-vite

Electron 专用 Vite 集成，原因：

- 一套 `defineConfig` 统一配置 main / preload / renderer 三进程构建
- 零配置约定（默认 `src/main`、`src/preload`、`src/renderer` 入口）
- 开箱支持 TypeScript、React、HMR
- renderer 侧开发体验与 Web 前端 Vite 项目完全一致

## 项目结构

```
apps/desktop/
├── src/
│   ├── main/                        # 主进程
│   │   ├── index.ts                 # 入口：应用生命周期 + 窗口创建
│   │   └── ...
│   ├── preload/                     # 预加载脚本
│   │   ├── index.ts                 # contextBridge 暴露安全 API
│   │   └── ...
│   ├── renderer/                    # 渲染进程（React 应用）
│   │   ├── src/
│   │   │   ├── app/                 # 应用层（layouts / providers / routes）
│   │   │   ├── features/            # 功能模块（按业务划分）
│   │   │   ├── shared/              # 全局共享（hooks / lib / types）
│   │   │   └── styles/              # 设计系统
│   │   └── index.html
│   └── shared/                      # 跨进程共享
│       └── types/
│           └── electron.d.ts        # IPC 通道类型定义
├── resources/                       # 应用图标等静态资源
├── electron-builder.yml             # 打包配置
├── electron.vite.config.ts          # 三进程构建配置
├── tsconfig.node.json               # main + preload（Node 环境）
├── tsconfig.web.json                # renderer（浏览器环境）
└── package.json
```

## 进程架构

```
┌──────────────┐     IPC (invoke/handle)     ┌──────────────┐
│  Renderer    │  ◄──────────────────────►   │  Main        │
│  (React UI)  │     contextBridge 桥接       │  (Node.js)   │
│              │                              │              │
│  沙箱环境     │  ◄── webContents.send ────  │  窗口管理     │
│  无 Node 访问 │                              │  系统 API    │
└──────────────┘                              │  文件/网络    │
       ▲                                      └──────────────┘
       │ exposeInMainWorld                            │
┌──────────────┐                              ┌──────────────┐
│  Preload     │                              │  Workers     │
│  最小化桥接   │                              │  CPU 密集任务 │
└──────────────┘                              └──────────────┘
```

### 进程职责

| 进程 | 职责 | 关键约束 |
|------|------|----------|
| **Main** | 应用生命周期、窗口管理、系统 API（文件/对话框/菜单）、IPC 调度 | 保持轻量，作为编排层；CPU 密集任务委托 Worker Threads |
| **Preload** | 通过 `contextBridge.exposeInMainWorld` 暴露安全 API | 只暴露具名方法，不暴露通用通道，不包含业务逻辑 |
| **Renderer** | UI 渲染，遵循 Web 前端全部规范 | 沙箱环境，通过 `window.electronAPI` 调用系统能力 |

## 安全配置

### BrowserWindow 安全基线

```typescript
const mainWindow = new BrowserWindow({
  webPreferences: {
    preload: path.join(__dirname, '../preload/index.js'),
    // 以下为 Electron 20+ 默认值，显式声明以确保安全意图清晰
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,
    webSecurity: true,
  },
})
```

### 安全检查清单

| # | 要求 | 说明 |
|---|------|------|
| 1 | 只加载安全内容 | 使用 HTTPS / WSS / FTPS |
| 2 | 禁用 Node 集成 | `nodeIntegration: false` |
| 3 | 启用上下文隔离 | `contextIsolation: true` |
| 4 | 启用进程沙箱 | `sandbox: true` |
| 5 | 启用 Web 安全 | `webSecurity: true` |
| 6 | 定义 CSP | 限制资源加载来源 |
| 7 | 验证 IPC 发送者 | 检查 `event.sender` 身份 |
| 8 | 限制导航 | 使用 `will-navigate` 拦截 |
| 9 | 限制窗口创建 | 使用 `setWindowOpenHandler` |
| 10 | 验证外部链接 | `shell.openExternal` 前校验 URL |
| 11 | 禁用 remote 模块 | 已废弃，不使用 |
| 12 | 避免 file:// 协议 | 生产环境使用自定义协议 |

## IPC 通信规范

### 通道命名

格式 `<namespace>:<action>`，语义清晰：

```typescript
// 命名示例
'file:read'           // 文件读取
'file:save'           // 文件保存
'dialog:open-file'    // 打开文件对话框
'app:get-version'     // 获取应用版本
'settings:load'       // 加载设置
'settings:save'       // 保存设置
'update:check'        // 检查更新
```

### 类型定义

所有 IPC 通道在 `src/shared/types/electron.d.ts` 集中定义：

```typescript
// src/shared/types/electron.d.ts

export interface IElectronAPI {
  // 文件操作
  readFile: (filePath: string) => Promise<{ success: boolean; content?: string; error?: string }>
  saveFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>

  // 对话框
  openFile: () => Promise<string | null>

  // 应用信息
  getAppInfo: () => Promise<{ version: string; platform: string; userData: string }>

  // 事件监听（Main → Renderer）
  onUpdateAvailable: (callback: (data: { version: string }) => void) => void
}

declare global {
  interface Window {
    electronAPI: IElectronAPI
  }
}
```

### Preload 实现

```typescript
// src/preload/index.ts
import { contextBridge, ipcRenderer } from 'electron'

contextBridge.exposeInMainWorld('electronAPI', {
  readFile: (filePath: string) => ipcRenderer.invoke('file:read', filePath),
  saveFile: (filePath: string, content: string) => ipcRenderer.invoke('file:save', filePath, content),
  openFile: () => ipcRenderer.invoke('dialog:open-file'),
  getAppInfo: () => ipcRenderer.invoke('app:get-info'),
  onUpdateAvailable: (callback: (data: { version: string }) => void) => {
    ipcRenderer.on('update:available', (_event, data) => callback(data))
  },
})
```

### Main 进程处理

```typescript
// src/main/index.ts
import { app, BrowserWindow, ipcMain, dialog } from 'electron'
import fs from 'node:fs/promises'

ipcMain.handle('file:read', async (_event, filePath: string) => {
  try {
    const content = await fs.readFile(filePath, 'utf-8')
    return { success: true, content }
  } catch (error) {
    return { success: false, error: (error as Error).message }
  }
})

ipcMain.handle('dialog:open-file', async () => {
  const { canceled, filePaths } = await dialog.showOpenDialog({ properties: ['openFile'] })
  return canceled ? null : filePaths[0]
})

ipcMain.handle('app:get-info', () => ({
  version: app.getVersion(),
  platform: process.platform,
  userData: app.getPath('userData'),
}))
```

### Renderer 使用

```tsx
// src/renderer/src/features/settings/hooks/useAppInfo.ts
import { useQuery } from '@tanstack/react-query'

export function useAppInfo() {
  return useQuery({
    queryKey: ['app-info'],
    queryFn: () => window.electronAPI.getAppInfo(),
  })
}
```

## 路由

Renderer 使用 **HashRouter**（Electron 的 `file://` 协议不支持 History API）：

```tsx
import { HashRouter, Route, Routes } from 'react-router-dom'

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<Home />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </HashRouter>
  )
}
```

## 构建配置

### electron.vite.config.ts

```typescript
import { defineConfig, externalizeDepsPlugin } from 'electron-vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
  },
  renderer: {
    plugins: [tailwindcss(), react()],
    resolve: {
      alias: {
        '@': resolve('src/renderer/src'),
      },
    },
  },
})
```

### TypeScript 配置

双 tsconfig 分离 Node 和浏览器环境：

**tsconfig.node.json**（main + preload）：
```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "types": ["electron-vite/node"],
    "strict": true
  },
  "include": ["src/main/**/*", "src/preload/**/*", "src/shared/**/*", "electron.vite.config.ts"]
}
```

**tsconfig.web.json**（renderer）：
```json
{
  "compilerOptions": {
    "composite": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "jsx": "react-jsx",
    "strict": true,
    "paths": {
      "@/*": ["./src/renderer/src/*"]
    }
  },
  "include": ["src/renderer/**/*", "src/shared/**/*"]
}
```

## 窗口管理

```typescript
import { BrowserWindow, shell } from 'electron'
import { is } from '@electron-toolkit/utils'

function createWindow(): void {
  const mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    show: false, // 就绪后再显示，避免白屏闪烁
    webPreferences: {
      preload: path.join(__dirname, '../preload/index.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  })

  // 就绪后显示
  mainWindow.on('ready-to-show', () => {
    mainWindow.show()
  })

  // 外部链接在系统浏览器打开
  mainWindow.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  // 开发环境加载 dev server，生产环境加载本地文件
  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    mainWindow.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'))
  }
}
```

## 自动更新

```typescript
import { autoUpdater } from 'electron-updater'

// 应用就绪后检查更新
app.whenReady().then(() => {
  autoUpdater.checkForUpdatesAndNotify()
})

// 通知 Renderer
autoUpdater.on('update-available', (info) => {
  mainWindow.webContents.send('update:available', { version: info.version })
})
```

## 性能优化

| 策略 | 说明 |
|------|------|
| 窗口延迟显示 | `show: false` + `ready-to-show` 事件，避免白屏闪烁 |
| Main 进程不阻塞 | CPU 密集任务用 Worker Threads 或 fork 子进程 |
| IPC 批量传输 | 避免高频小消息，大数据一次传输 |
| 模块懒加载 | 按需 `import()` 减少启动时间 |
| Renderer 优化 | React.memo / useMemo / 虚拟列表，与 Web 前端一致 |

## 开发命令

```bash
pnpm --filter @bedrock/desktop dev          # 开发模式（HMR）
pnpm --filter @bedrock/desktop build        # 构建
pnpm --filter @bedrock/desktop build:mac    # macOS 打包
pnpm --filter @bedrock/desktop build:win    # Windows 打包
pnpm --filter @bedrock/desktop build:linux  # Linux 打包
```
