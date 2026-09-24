import { Capacitor } from '@capacitor/core'

/**
 * «Поделиться» текущим экраном.
 *
 * В браузере отправляем его адрес. В APK окно живёт на `https://localhost` —
 * такую ссылку получателю не открыть, поэтому берём тот же путь на веб-версии
 * (`VITE_PUBLIC_WEB_URL`). Адрес не задан — отправляем один текст, без ссылки:
 * лучше без неё, чем с неработающей.
 *
 * Системного окна отправки в Android WebView нет (Web Share API там не
 * реализован) — тогда ссылка или текст уходит в буфер обмена. Возвращаем, что
 * именно произошло, — экрану этого хватает, чтобы показать «Скопировано».
 */

const PUBLIC_WEB_URL = (import.meta.env.VITE_PUBLIC_WEB_URL ?? '').replace(/\/+$/, '')

function shareUrl(): string | undefined {
  if (!Capacitor.isNativePlatform()) return window.location.href
  return PUBLIC_WEB_URL ? `${PUBLIC_WEB_URL}${window.location.pathname}${window.location.search}` : undefined
}

export async function shareCurrentPage(title?: string, text?: string): Promise<'shared' | 'copied' | 'failed'> {
  const url = shareUrl()
  try {
    if (navigator.share) {
      await navigator.share({ title, text, url })
      return 'shared'
    }
    const payload = url ?? [title, text].filter(Boolean).join(' — ')
    if (!payload) return 'failed'
    await navigator.clipboard.writeText(payload)
    return 'copied'
  } catch {
    // Отмена системного окна — тоже исключение; это не ошибка, просто ничего не делаем.
    return 'failed'
  }
}

/**
 * Поделиться коротким текстом — например кодом приглашения в семью. Ссылки
 * здесь нет намеренно: код набирают руками в приложении, а не открывают.
 */
export async function shareText(title: string, text: string): Promise<'shared' | 'copied' | 'failed'> {
  try {
    if (navigator.share) {
      await navigator.share({ title, text })
      return 'shared'
    }
    await navigator.clipboard.writeText(text)
    return 'copied'
  } catch {
    return 'failed'
  }
}
