<script setup lang="ts">
import { TIMELINE_YEARS } from '../data'

/**
 * Хронология слоя «ВОВ»: карта показывает не только «где», но и «когда».
 *
 * Год без единого места на карте не выключается, а гаснет: пустая клетка
 * шкалы — это тоже знание («в 1944-м здесь уже не воевали»), и шкала не
 * скачет по ширине, когда фильтр по виду места меняет набор годов.
 */
const active = defineModel<Set<number>>({ required: true })

defineProps<{
  /** Сколько мест приходится на каждый год — с учётом остальных фильтров. */
  counts: Record<number, number>
}>()

function toggle(year: number): void {
  // Новый Set, а не мутация: так изменение гарантированно дойдёт до родителя через v-model.
  const next = new Set(active.value)
  if (next.has(year)) next.delete(year)
  else next.add(year)
  active.value = next
}
</script>

<template>
  <div class="flex items-center gap-space-sm">
    <span class="shrink-0 font-archival text-archival uppercase text-on-surface-variant">Годы</span>

    <div class="flex flex-1 items-center gap-space-xs">
      <button
        v-for="year in TIMELINE_YEARS"
        :key="year"
        type="button"
        class="flex h-8 flex-1 items-center justify-center gap-1 rounded-full font-label-md text-label-md transition-colors disabled:opacity-40"
        :class="
          active.has(year)
            ? 'bg-tertiary text-on-tertiary shadow-float'
            : 'bg-surface-container-lowest text-on-surface shadow-document hover:bg-surface-container-low'
        "
        :aria-pressed="active.has(year)"
        :aria-label="`${year} год`"
        :disabled="!counts[year]"
        @click="toggle(year)"
      >
        {{ year }}
      </button>
    </div>

    <button
      v-if="active.size"
      type="button"
      class="shrink-0 font-label-md text-label-md text-primary underline underline-offset-2"
      @click="active = new Set()"
    >
      Все
    </button>
  </div>
</template>
