import { useToggleUserStatus } from '../hooks/useUsers'
import { useTranslation } from 'react-i18next'
import type { User } from '../types'

export function UserStatusToggle({ user }: { user: User }) {
  const { t } = useTranslation()
  const toggleMutation = useToggleUserStatus()

  return (
    <button
      type="button"
      onClick={() => toggleMutation.mutate(user.id)}
      disabled={toggleMutation.isPending}
      className={`px-2 py-1 text-xs rounded-full font-medium ${
        user.status === 'active'
          ? 'bg-green-100 text-green-700 hover:bg-green-200'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
      }`}
    >
      {user.status === 'active' ? t('users.enabled') : t('users.disabled')}
    </button>
  )
}
