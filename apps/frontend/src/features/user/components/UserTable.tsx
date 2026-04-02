import { useState } from 'react'
import { useUsers, useDeleteUser } from '../hooks/useUsers'
import { UserForm } from './UserForm'
import { UserStatusToggle } from './UserStatusToggle'
import { usePagination } from '@/shared/hooks/usePagination'
import type { UserSearchParams } from '../types'
import { Search, Plus, Trash2, ChevronLeft, ChevronRight } from 'lucide-react'

export default function UserTable() {
  const { page, size, goToPage, nextPage, prevPage } = usePagination()
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [showForm, setShowForm] = useState(false)
  const deleteMutation = useDeleteUser()

  const params: UserSearchParams = {
    page,
    size,
    keyword: keyword || undefined,
    status: statusFilter || undefined,
  }

  const { data, isLoading } = useUsers(params)

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">用户管理</h1>
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg text-sm hover:bg-gray-800"
        >
          <Plus className="w-4 h-4" />
          新建用户
        </button>
      </div>

      <div className="flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            placeholder="搜索用户..."
            value={keyword}
            onChange={(e) => { setKeyword(e.target.value); goToPage(1) }}
            className="w-full pl-9 pr-3 py-2 border rounded-lg text-sm"
          />
        </div>
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); goToPage(1) }}
          className="border rounded-lg px-3 py-2 text-sm"
        >
          <option value="">全部状态</option>
          <option value="active">已启用</option>
          <option value="disabled">已禁用</option>
        </select>
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">用户名</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">显示名</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">邮箱</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">状态</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">角色</th>
              <th className="px-4 py-3 text-right font-medium text-gray-600">操作</th>
            </tr>
          </thead>
          <tbody>
            {isLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">加载中...</td></tr>
            ) : data?.content.length === 0 ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-400">暂无用户数据</td></tr>
            ) : (
              data?.content.map((user) => (
                <tr key={user.id} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{user.username}</td>
                  <td className="px-4 py-3">{user.display_name}</td>
                  <td className="px-4 py-3 text-gray-500">{user.email ?? '-'}</td>
                  <td className="px-4 py-3"><UserStatusToggle user={user} /></td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {user.roles.map((role) => (
                        <span key={role} className="px-2 py-0.5 bg-blue-50 text-blue-600 rounded text-xs">{role}</span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      type="button"
                      onClick={() => deleteMutation.mutate(user.id)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-500">
          <span>共 {data.total} 个用户</span>
          <div className="flex items-center gap-2">
            <button type="button" onClick={prevPage} disabled={page <= 1} className="p-1 hover:bg-gray-100 rounded disabled:opacity-30">
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span>第 {page} / {data.total_pages} 页</span>
            <button type="button" onClick={nextPage} disabled={page >= data.total_pages} className="p-1 hover:bg-gray-100 rounded disabled:opacity-30">
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {showForm && <UserForm onClose={() => setShowForm(false)} />}
    </div>
  )
}
