import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { userApi } from '../api/userApi'
import type { UserCreate, UserSearchParams, UserUpdate } from '../types'

const USER_QUERY_KEY = 'users'

export function useUsers(params: UserSearchParams) {
  return useQuery({
    queryKey: [USER_QUERY_KEY, params],
    queryFn: () => userApi.search(params),
    select: (response) => response.data,
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: UserCreate) => userApi.create(data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useUpdateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) => userApi.update(id, data),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useDeleteUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => userApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}

export function useToggleUserStatus() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => userApi.toggleStatus(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: [USER_QUERY_KEY] })
    },
  })
}
