import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

const UserListPage = lazy(() => import('@/features/user/components/UserTable'))

export function UserRoutes() {
  return (
    <Suspense fallback={<div className="text-center py-8">加载中...</div>}>
      <Routes>
        <Route index element={<UserListPage />} />
      </Routes>
    </Suspense>
  )
}
