import type { AppModule, ModuleTab } from '@/core/module'

/**
 * Подключённые модули.
 *
 * Vite собирает все `src/modules/<имя>/index.ts` на этапе сборки — отдельного
 * списка, который надо не забыть поправить, нет. Модуль попадает в приложение,
 * если его папка существует и в нём не выставлено `enabled: false`.
 */
const discovered = import.meta.glob<{ default: AppModule }>('/src/modules/*/index.ts', { eager: true })

function collect(): AppModule[] {
  const ids = new Map<string, string>()
  const list: AppModule[] = []

  for (const [path, entry] of Object.entries(discovered)) {
    const module = entry.default
    if (!module) {
      console.warn(`[модули] ${path} ничего не экспортирует по умолчанию — пропущен`)
      continue
    }
    if (module.enabled === false) continue

    // Два модуля с одним id дали бы роуты с одинаковыми именами, и один молча
    // затёр бы другой. Лучше упасть сразу и с понятным текстом.
    const previous = ids.get(module.id)
    if (previous) {
      throw new Error(`Модуль «${module.id}» объявлен дважды: ${previous} и ${path}`)
    }
    ids.set(module.id, path)
    list.push(module)
  }

  return list
}

export const modules: readonly AppModule[] = collect()

export const tabs: readonly ModuleTab[] = modules
  .flatMap((module) => (module.tab ? [module.tab] : []))
  .sort((a, b) => a.order - b.order)
