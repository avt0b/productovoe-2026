<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { FindStatus, SectorPin } from '../data'

/**
 * План сектора поиска.
 *
 * Подложки-снимка у сектора пока нет, поэтому — сетка квадратов поверх
 * нейтрального фона, как в макете. Когда подключим карту, заменится этот
 * компонент; метки уже приходят в процентах плана.
 */
const selected = defineModel<string | null>('selected', { required: true })

defineProps<{
  pins: SectorPin[]
  sector: string
}>()

const PIN_TONES: Record<FindStatus, string> = {
  found: 'bg-tertiary text-on-tertiary ring-tertiary-fixed',
  confirmed: 'bg-primary text-on-primary ring-primary-fixed',
  raised: 'bg-secondary text-on-secondary ring-secondary-fixed',
}
</script>

<template>
  <div class="relative h-80 w-full overflow-hidden rounded-lg bg-surface-container-high shadow-md">
    <div class="absolute inset-0 bg-gradient-to-br from-secondary-container/60 via-surface-container-high to-tertiary-fixed/40" />
    <div class="pointer-events-none absolute inset-0 bg-gradient-to-t from-inverse-surface/80 via-transparent to-transparent" />

    <!-- Сетка квадратов 4×4 -->
    <div class="pointer-events-none absolute inset-0 grid grid-cols-4 grid-rows-4 opacity-25" aria-hidden="true">
      <div
        v-for="cell in 16"
        :key="cell"
        class="border-surface-container-lowest"
        :class="{ 'border-r': cell % 4 !== 0, 'border-b': cell <= 12 }"
      />
    </div>

    <div
      class="absolute left-3 top-3 flex items-center gap-1.5 rounded-full bg-surface-container-lowest/90 px-2.5 py-1 font-label-sm text-label-sm text-on-surface shadow-sm backdrop-blur-md"
    >
      <MsIcon name="explore" :size="16" class="text-primary" />
      <span>{{ sector }}</span>
    </div>

    <div class="absolute right-3 top-3 flex flex-col gap-1.5">
      <button
        type="button"
        aria-label="Слои карты"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-lowest/90 text-on-surface shadow-sm backdrop-blur-md transition-transform active:scale-90"
      >
        <MsIcon name="layers" :size="18" />
      </button>
      <button
        type="button"
        aria-label="Мое местоположение"
        class="flex h-9 w-9 items-center justify-center rounded-full bg-surface-container-lowest/90 text-primary shadow-sm backdrop-blur-md transition-transform active:scale-90"
      >
        <MsIcon name="my_location" :size="18" />
      </button>
    </div>

    <button
      v-for="pin in pins"
      :key="pin.id"
      type="button"
      class="group absolute flex -translate-x-1/2 -translate-y-1/2 flex-col items-center"
      :style="{ left: `${pin.x}%`, top: `${pin.y}%` }"
      :aria-label="pin.label"
      :aria-pressed="selected === pin.id"
      @click="selected = pin.id"
    >
      <!-- nowrap: метка позиционирована абсолютно и сжимается по содержимому — без него подпись ломается на строки. -->
      <span class="mb-1 whitespace-nowrap rounded-full bg-surface-container-lowest/90 px-2 py-0.5 font-label-sm text-label-sm text-on-surface shadow">
        {{ pin.label }}
      </span>
      <span
        class="flex items-center justify-center rounded-full shadow-lg ring-4 transition-transform group-hover:scale-110"
        :class="[PIN_TONES[pin.status], selected === pin.id ? 'h-9 w-9 animate-bounce' : 'h-7 w-7']"
      >
        <MsIcon :name="pin.icon" :size="selected === pin.id ? 18 : 15" />
      </span>
    </button>
  </div>
</template>
