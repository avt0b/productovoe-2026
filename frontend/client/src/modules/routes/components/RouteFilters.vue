<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { RouteFilter } from '../data'

const active = defineModel<Set<string>>({ required: true })

defineProps<{ filters: RouteFilter[] }>()

function toggle(id: string): void {
  // Новый Set, а не мутация: так изменение гарантированно дойдёт до родителя через v-model.
  const next = new Set(active.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  active.value = next
}

function chipClass(filter: RouteFilter): string {
  if (active.value.has(filter.id)) return 'bg-primary text-on-primary shadow-md shadow-primary/25'
  if (filter.highlight) return 'bg-tertiary-fixed text-on-tertiary-fixed-variant'
  return 'bg-surface-container-lowest text-on-surface shadow-sm hover:bg-surface-container-low'
}
</script>

<template>
  <div class="no-scrollbar -mx-margin flex items-center gap-space-xs overflow-x-auto px-margin py-0.5">
    <button
      v-for="filter in filters"
      :key="filter.id"
      type="button"
      :aria-pressed="active.has(filter.id)"
      class="flex h-9 shrink-0 items-center gap-1.5 rounded-full px-space-md font-label-md text-label-md transition-transform active:scale-95"
      :class="chipClass(filter)"
      @click="toggle(filter.id)"
    >
      <MsIcon
        :name="filter.icon"
        :size="16"
        :filled="filter.filledIcon"
        :class="active.has(filter.id) ? undefined : filter.iconClass"
      />
      {{ filter.title }}
    </button>
  </div>
</template>
