<script setup lang="ts" generic="T extends string">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

/**
 * Два-три режима экрана. Подложка выбранного едет трансформацией, как вкладки
 * на экране входа: перекраска кнопок переключалась бы рывком, а так видно,
 * куда ушёл выбор.
 */
const props = defineProps<{
  tabs: readonly { value: T; title: string; icon: string; count?: number }[]
  label: string
  /** Префикс id панелей: у вкладки `aria-controls="<idPrefix>-<value>"`. */
  idPrefix: string
}>()

const model = defineModel<T>({ required: true })

const index = computed(() => Math.max(0, props.tabs.findIndex((tab) => tab.value === model.value)))
</script>

<template>
  <div class="relative grid rounded-xl bg-surface-container p-1" :style="{ gridTemplateColumns: `repeat(${tabs.length}, minmax(0, 1fr))` }" role="tablist" :aria-label="label">
    <span
      class="absolute inset-y-1 left-1 rounded-lg bg-surface-container-lowest shadow-float transition-transform duration-300 ease-out"
      :style="{ width: `calc((100% - 8px) / ${tabs.length})`, transform: `translateX(${index * 100}%)` }"
      aria-hidden="true"
    />
    <button
      v-for="tab in tabs"
      :id="`${idPrefix}-tab-${tab.value}`"
      :key="tab.value"
      type="button"
      role="tab"
      :aria-selected="model === tab.value"
      :aria-controls="`${idPrefix}-${tab.value}`"
      class="relative z-10 flex min-w-0 items-center justify-center gap-1 rounded-lg px-1 py-2 font-label-md text-label-md transition-colors duration-200"
      :class="model === tab.value ? 'text-on-surface' : 'text-on-surface-variant hover:text-on-surface'"
      @click="model = tab.value"
    >
      <MsIcon :name="tab.icon" :size="18" :filled="model === tab.value" class="shrink-0" />
      <span class="truncate">{{ tab.title }}</span>
      <span
        v-if="tab.count"
        class="shrink-0 rounded-full px-1.5 font-label-sm text-label-sm transition-colors duration-200"
        :class="model === tab.value ? 'bg-secondary-container text-on-secondary-container' : 'bg-surface-container-high'"
      >
        {{ tab.count }}
      </span>
    </button>
  </div>
</template>
