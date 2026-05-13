import { useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { type AppLanguage, normalizeLanguage } from '@/app/i18n/language'

export function useAppLanguage() {
  const { i18n } = useTranslation()
  const language = normalizeLanguage(i18n.resolvedLanguage ?? i18n.language)
  return useMemo(
    () => ({
      language,
      setLanguage: (nextLanguage: AppLanguage) => void i18n.changeLanguage(nextLanguage),
    }),
    [i18n, language],
  )
}
