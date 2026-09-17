import { ref, shallowRef, type Ref, type ShallowRef } from 'vue'

import { errorText } from './format'

export interface AsyncState<T> {
  data: ShallowRef<T | null>
  loading: Ref<boolean>
  error: Ref<string | null>
  /** Повторить загрузку — для кнопки «Повторить» в `StateBlock`. */
  retry: () => Promise<void>
}

/**
 * Загрузка данных экрана с тремя состояниями.
 *
 * Запускается сразу. Если экран ушёл раньше, чем пришёл ответ, результат
 * просто некому показать — ничего не ломается.
 */
export function useAsync<T>(load: () => Promise<T>): AsyncState<T> {
  const data = shallowRef<T | null>(null)
  const loading = ref(true)
  const error = ref<string | null>(null)

  async function retry(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      data.value = await load()
    } catch (reason) {
      error.value = errorText(reason)
    } finally {
      loading.value = false
    }
  }

  void retry()
  return { data, loading, error, retry }
}
