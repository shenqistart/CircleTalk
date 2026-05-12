import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryProvider } from '@/app/providers/QueryProvider'
import { AppLayout } from '@/app/layouts/AppLayout'
import { RoundtableRoutes, UserRoutes } from '@/app/routes'

export default function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/users" replace />} />
            <Route path="/users/*" element={<UserRoutes />} />
            <Route path="/roundtable" element={<RoundtableRoutes />} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryProvider>
  )
}
