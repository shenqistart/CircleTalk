import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { useCreateUser } from '../hooks/useUsers'
import type { UserCreate } from '../types'

export function UserForm({ onClose }: { onClose: () => void }) {
  const { t } = useTranslation()
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
        <h2 className="text-lg font-semibold mb-4">{t('users.newUser')}</h2>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium mb-1">{t('users.username')} *</label>
            <input
              type="text"
              required
              value={form.username}
              onChange={(e) => setForm((prev) => ({ ...prev, username: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('users.displayName')} *</label>
            <input
              type="text"
              required
              value={form.display_name}
              onChange={(e) => setForm((prev) => ({ ...prev, display_name: e.target.value }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('users.email')}</label>
            <input
              type="email"
              value={form.email ?? ''}
              onChange={(e) => setForm((prev) => ({ ...prev, email: e.target.value || undefined }))}
              className="w-full border rounded-lg px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t('users.phone')}</label>
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
            {t('users.cancel')}
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="px-4 py-2 text-sm bg-gray-900 text-white rounded-lg hover:bg-gray-800 disabled:opacity-50"
          >
            {createMutation.isPending ? t('users.creating') : t('users.create')}
          </button>
        </div>
      </form>
    </div>
  )
}
