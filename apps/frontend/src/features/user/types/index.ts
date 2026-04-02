export type User = {
  id: string
  username: string
  display_name: string
  email: string | null
  phone: string | null
  avatar: string | null
  status: 'active' | 'disabled'
  roles: string[]
  last_login_at: string | null
  created_at: string | null
  updated_at: string | null
}

export type UserCreate = {
  username: string
  display_name: string
  email?: string
  phone?: string
  roles?: string[]
}

export type UserUpdate = {
  display_name?: string
  email?: string
  phone?: string
  avatar?: string
  roles?: string[]
}

export type UserSearchParams = {
  keyword?: string
  status?: string
  role?: string
  page?: number
  size?: number
}
