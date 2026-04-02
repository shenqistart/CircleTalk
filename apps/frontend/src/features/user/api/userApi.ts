import { request } from '@/shared/lib/request'
import type { ApiResponse, PageData } from '@/shared/types/api'
import type { User, UserCreate, UserSearchParams, UserUpdate } from '../types'

export const userApi = {
  search(params: UserSearchParams): Promise<ApiResponse<PageData<User>>> {
    return request('get', '/users', undefined, params as Record<string, unknown>)
  },

  getById(id: string): Promise<ApiResponse<User>> {
    return request('get', `/users/${id}`)
  },

  create(data: UserCreate): Promise<ApiResponse<User>> {
    return request('post', '/users', data)
  },

  update(id: string, data: UserUpdate): Promise<ApiResponse<User>> {
    return request('put', `/users/${id}`, data)
  },

  remove(id: string): Promise<ApiResponse<null>> {
    return request('delete', `/users/${id}`)
  },

  toggleStatus(id: string): Promise<ApiResponse<User>> {
    return request('put', `/users/${id}/status`)
  },
}
