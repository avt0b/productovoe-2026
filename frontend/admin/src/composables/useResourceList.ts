import { ref, shallowRef } from 'vue'

import type { Page } from '@/api/types'
import { errorText } from '@/lib'

/**
 * Постраничный список: три состояния, пагинация и перезагрузка.
 *
 * Фильтры остаются во вьюхе — сюда передаётся замыкание, которое их читает.
 * Так список остаётся полностью типизированным и не требует `any`.
 */
export function useResourceList<T>(
  fetcher: (limit: number, offset: number) => Promise<Page<T>>,
  pageSize = 20,
) {
  const items = shallowRef<T[]>([])
  const total = ref(0)
  const offset = ref(0)
  const limit = ref(pageSize)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function load(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const page = await fetcher(limit.value, offset.value)
      items.value = page.items
      total.value = page.total
    } catch (e) {
      error.value = errorText(e)
      items.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  /** Смена фильтра всегда возвращает на первую страницу. */
  async function reload(): Promise<void> {
    offset.value = 0
    await load()
  }

  async function setOffset(value: number): Promise<void> {
    offset.value = value
    await load()
  }

  return { items, total, offset, limit, loading, error, load, reload, setOffset }
}
