import { useCallback, useState } from 'react'

export function usePagination(initialPage = 1, initialSize = 10) {
  const [page, setPage] = useState(initialPage)
  const [size, setSize] = useState(initialSize)

  const goToPage = useCallback((newPage: number) => {
    setPage(Math.max(1, newPage))
  }, [])

  const nextPage = useCallback(() => {
    setPage((prev) => prev + 1)
  }, [])

  const prevPage = useCallback(() => {
    setPage((prev) => Math.max(1, prev - 1))
  }, [])

  const resetPage = useCallback(() => {
    setPage(initialPage)
  }, [initialPage])

  return { page, size, setSize, goToPage, nextPage, prevPage, resetPage }
}
