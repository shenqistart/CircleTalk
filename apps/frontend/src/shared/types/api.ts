export type ApiResponse<T> = {
  code: number
  message: string
  data: T | null
}

export type PageData<T> = {
  content: T[]
  total: number
  page: number
  size: number
  total_pages: number
}
