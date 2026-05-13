import { createRoot } from 'react-dom/client'
import './index.css'
import { AppI18nProvider } from '@/app/i18n'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <AppI18nProvider>
    <App />
  </AppI18nProvider>,
)
