import { Outlet } from 'react-router-dom'

export function AppLayout() {
  return (
    <div className="flex h-screen w-full overflow-hidden bg-gray-50">
      <aside className="hidden md:flex w-60 flex-col border-r bg-white p-4">
        <h1 className="text-xl font-bold mb-8">Bedrock</h1>
        <nav className="space-y-2">
          <a href="/roundtable" className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm font-medium">
            圆桌对话
          </a>
          <a href="/users" className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm font-medium">
            用户管理
          </a>
          <a href="/roundtable" className="block px-3 py-2 rounded-lg hover:bg-gray-100 text-sm font-medium">
            圆桌对话
          </a>
        </nav>
      </aside>
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  )
}
