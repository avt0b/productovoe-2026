/**
 * «Поделиться» текущей страницей.
 *
 * В браузере телефона и в APK открывается системное окно отправки. Где его нет
 * (десктоп), ссылка копируется в буфер. Возвращает, что именно произошло, —
 * экрану этого хватает, чтобы показать «Ссылка скопирована».
 */
export async function shareCurrentPage(title?: string, text?: string): Promise<'shared' | 'copied' | 'failed'> {
  const url = window.location.href
  try {
    if (navigator.share) {
      await navigator.share({ title, text, url })
      return 'shared'
    }
    await navigator.clipboard.writeText(url)
    return 'copied'
  } catch {
    // Отмена системного окна — тоже исключение; это не ошибка, просто ничего не делаем.
    return 'failed'
  }
}
