import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'

const UserListPage = lazy(() => import('@/features/user/components/UserTable'))
const RoundtableWorkbench = lazy(() => import('@/features/roundtable/components/RoundtableWorkbench'))

function RouteFallback() {
  return <div className="py-8 text-center">加载中...</div>
}

export function UserRoutes() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route index element={<UserListPage />} />
      </Routes>
    </Suspense>
  )
}

export function RoundtableRoute() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <RoundtableWorkbench />
    </Suspense>
  )
}
