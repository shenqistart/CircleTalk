import { useState } from 'react'
import { useCreateUser } from '../hooks/useUsers'
import type { UserCreate } from '../types'

export function UserForm({ onClose }: { onClose: () => void }) {
  const createMutation = useCreateUser()
  const [form, setForm] = useState<UserCreate>({
    username: '',
    display_name: '',
    email: '',
    phone: '',
    roles: [],
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(form, {
      onSuccess: () => onClose(),
    })
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <form onSubmit={handleSubmit} className="bg-white rounded-xl p-6 w-full max-w-md shadow-xl">
        <h2 className="text-lg font-semibold mb-4">新建用户</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">用户名 *</label>
            <input
              type="text"
              required
              value={form.username}
              onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">显示名 *</label>
            <input
              type="text"
              required
              value={form.display_name}
              onChange={(e) => setForm((prev) => ({ ...prev, display_name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">邮箱</label>
            <input
              type="email"
              value={form.email ?? ''}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value || undefined }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">手机号</label>
            <input
              type="text"
              value={form.phone ?? ''}
              onChange={(e) => setForm((prev) => ({ ...prev, phone: e.target.value || undefined }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg">
            取消
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
          >
            {createMutation.isPending ? '创建中...' : '创建'}
          </button>
        </div>
      </form>
    </div>
  )
}
