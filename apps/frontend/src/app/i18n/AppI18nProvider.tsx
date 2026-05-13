import { I18nextProvider } from 'react-i18next'
import { type PropsWithChildren, useEffect, useState } from 'react'
import { appI18n, type AppLanguage, documentLanguage, normalizeLanguage, storeLanguage } from '@/app/i18n/language'

export function AppI18nProvider({ children }: PropsWithChildren) {
  const [language, setLanguage] = useState<AppLanguage>(normalizeLanguage(appI18n.resolvedLanguage ?? appI18n.language))

  useEffect(() => {
    const handleLanguageChanged = (nextLanguage: string) => setLanguage(normalizeLanguage(nextLanguage))
    appI18n.on('languageChanged', handleLanguageChanged)
    return () => appI18n.off('languageChanged', handleLanguageChanged)
  }, [])

  useEffect(() => {
    document.documentElement.lang = documentLanguage(language)
    storeLanguage(language)
  }, [language])

  return <I18nextProvider i18n={appI18n}>{children}</I18nextProvider>
}
