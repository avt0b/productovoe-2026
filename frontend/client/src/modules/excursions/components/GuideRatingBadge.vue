<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { plural } from '@/core/format'
import { formatRating, placeLabel } from '@/features/guide-rating'
import MsIcon from '@/ui/MsIcon.vue'

import type { GuideRatingSummary } from '../data'

/**
 * Оценка краеведа там, где выбирают, к кому идти. Ведёт в карточку краеведа,
 * если модуль рейтинга подключён; иначе остаётся простой плашкой. Пока оценок
 * нет, пишем это словами: пять серых звёзд читаются как «оценка ноль».
 */
const props = defineProps<{ summary: GuideRatingSummary | null; guideId?: string }>()

const router = useRouter()
const link = computed(() =>
  props.guideId && router.hasRoute('guide') ? { name: 'guide', params: { guideId: props.guideId } } : null,
)

const name = computed(() => props.summary?.profile?.display_name || 'Краевед')
const stars = computed(() => {
  const average = props.summary?.average ?? 0
  return [1, 2, 3, 4, 5].map((position) => (average >= position - 0.25 ? 'star' : average >= position - 0.75 ? 'star_half' : 'star_border'))
})
</script>

<template>
  <component
    :is="link ? 'RouterLink' : 'div'"
    :to="link ?? undefined"
    class="flex items-center gap-space-sm rounded-2xl bg-surface-container-lowest p-space-sm shadow-document"
  >
    <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary">
      <MsIcon name="record_voice_over" :size="20" />
    </div>

    <div class="min-w-0 flex-1">
      <p class="flex items-center gap-1 font-archival text-archival uppercase text-on-surface-variant">
        <span class="truncate">{{ name }}</span>
        <span
          v-if="summary?.place"
          class="rounded-full bg-tertiary-fixed px-1.5 py-0.5 font-label-sm text-label-sm normal-case tracking-normal text-tertiary"
        >{{ placeLabel(summary.place) }}</span>
      </p>
      <p v-if="summary && summary.count > 0" class="flex items-center gap-1 font-label-lg text-label-lg text-on-surface">
        <MsIcon v-for="(icon, index) in stars" :key="index" :name="icon" :size="16" filled class="text-tertiary" />
        <!-- Запятая, как в рейтинге и карточке краеведа: «4,5», а не «4.5». -->
        <span class="ml-1">{{ formatRating(summary.average) }}</span>
        <span class="font-label-sm text-label-sm text-on-surface-variant">
          · {{ summary.count }} {{ plural(summary.count, ['оценка', 'оценки', 'оценок']) }}
        </span>
      </p>
      <p v-else class="font-body-sm text-body-sm text-on-surface-variant">Экскурсии этого краеведа ещё не оценивали</p>
    </div>

    <MsIcon v-if="link" name="chevron_right" :size="20" class="shrink-0 text-on-surface-variant" />
  </component>
</template>
