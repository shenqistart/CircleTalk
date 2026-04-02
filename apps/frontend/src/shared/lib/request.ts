import axios from 'axios'
import type { ApiResponse } from '@/shared/types/api'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  config.headers.set('X-Username', 'admin')
  config.headers.set('X-Roles', 'admin')
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error)) {
      console.error('API 请求错误:', error.response?.data ?? error.message)
    }
    return Promise.reject(error as Error)
  },
)

export async function request<T>(
  method: 'get' | 'post' | 'put' | 'delete',
  url: string,
  data?: unknown,
  params?: Record<string, unknown>,
): Promise<ApiResponse<T>> {
  const response = await api.request<ApiResponse<T>>({ method, url, data, params })
  return response.data
}

export { api }
