import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

const UserListPage = lazy(() => import('@/features/user/components/UserTable'))
const RoundtableWorkbench = lazy(() => import('@/features/roundtable/components/RoundtableWorkbench'))

export function UserRoutes() {
  return (
    <Suspense fallback={<div className="text-center py-8">加载中...</div>}>
      <Routes>
        <Route index element={<UserListPage />} />
      </Routes>
    </Suspense>
  )
}

export function RoundtableRoutes() {
  return (
    <Suspense fallback={<div className="text-center py-8">加载中...</div>}>
      <RoundtableWorkbench />
    </Suspense>
  )
}
