import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import { resources } from '@/app/i18n/resources'

export type AppLanguage = 'zh' | 'en'

const LANGUAGE_STORAGE_KEY = 'bedrock.language'

export function normalizeLanguage(value?: string | null): AppLanguage {
  return (value ?? '').toLowerCase().startsWith('en') ? 'en' : 'zh'
}

function storedLanguage(): AppLanguage | null {
  try {
    const value = window.localStorage.getItem(LANGUAGE_STORAGE_KEY)
    return value ? normalizeLanguage(value) : null
  } catch {
    return null
  }
}

function browserLanguage(): AppLanguage {
  if (typeof window === 'undefined') return 'zh'
  return normalizeLanguage(window.navigator.language)
}

function initialLanguage(): AppLanguage {
  return storedLanguage() ?? browserLanguage()
}

export function documentLanguage(language: AppLanguage): string {
  return language === 'zh' ? 'zh-CN' : 'en'
}

export function storeLanguage(language: AppLanguage): void {
  try {
    window.localStorage.setItem(LANGUAGE_STORAGE_KEY, language)
  } catch {
    // localStorage can be unavailable in private or embedded contexts.
  }
}

if (!i18n.isInitialized) {
  void i18n.use(initReactI18next).init({
    fallbackLng: 'zh',
    interpolation: { escapeValue: false },
    lng: initialLanguage(),
    resources,
    supportedLngs: ['zh', 'en'],
  })
}

export const appI18n = i18n
