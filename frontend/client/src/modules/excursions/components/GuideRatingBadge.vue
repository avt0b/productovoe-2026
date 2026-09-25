<script setup lang="ts">
import { computed } from 'vue'

import { plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { GuideRatingSummary } from '../data'

/**
 * Оценка краеведа из ТЗ: рейтинг гидов виден там, где человек выбирает, к кому
 * идти, — на самой экскурсии. Пока оценок нет, вместо пустых звёзд пишем это
 * словами: пять серых звёзд читаются как «оценка ноль».
 */
const props = defineProps<{ summary: GuideRatingSummary | null }>()

const stars = computed(() => {
  const average = props.summary?.average ?? 0
  return [1, 2, 3, 4, 5].map((position) => (average >= position - 0.25 ? 'star' : average >= position - 0.75 ? 'star_half' : 'star_border'))
})
</script>

<template>
  <div class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm shadow-document">
    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
      <MsIcon name="record_voice_over" :size="20" />
    </div>

    <div class="min-w-0 flex-1">
      <p class="font-archival text-archival uppercase text-on-surface-variant">Краевед</p>
      <p v-if="summary && summary.count > 0" class="flex items-center gap-1 font-label-lg text-label-lg text-on-surface">
        <MsIcon v-for="(icon, index) in stars" :key="index" :name="icon" :size="16" filled class="text-tertiary" />
        <span class="ml-1">{{ summary.average.toFixed(1) }}</span>
        <span class="font-label-sm text-label-sm text-on-surface-variant">
          · {{ summary.count }} {{ plural(summary.count, ['оценка', 'оценки', 'оценок']) }}
        </span>
      </p>
      <p v-else class="font-body-sm text-body-sm text-on-surface-variant">Экскурсии этого краеведа ещё не оценивали</p>
    </div>
  </div>
</template>
