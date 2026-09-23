<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber, plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { SeasonStats } from '../data'

const props = defineProps<{ stats: SeasonStats }>()

/** Итоги «Последнего боя» по Орловщине: найдено, подтверждено, поднято. */
const tiles = computed(() => [
  {
    value: props.stats.discovered,
    label: plural(props.stats.discovered, ['место ждёт проверки', 'места ждут проверки', 'мест ждут проверки']),
    tone: 'text-primary',
  },
  {
    value: props.stats.confirmed,
    label: plural(props.stats.confirmed, ['подтверждено архивом', 'подтверждены архивом', 'подтверждено архивом']),
    tone: 'text-secondary',
  },
  {
    value: props.stats.raised,
    label: plural(props.stats.raised, ['останки подняты', 'останков поднято', 'останков поднято']),
    tone: 'text-tertiary',
  },
])
</script>

<template>
  <section class="relative overflow-hidden rounded-lg bg-surface-container-low p-5 shadow-sm">
    <div class="pointer-events-none absolute -bottom-6 -right-6 h-32 w-32 rounded-full bg-primary-fixed/30 blur-2xl" />

    <div class="mb-4 flex items-center gap-space-sm">
      <div class="flex h-10 w-10 items-center justify-center rounded-full bg-tertiary-fixed text-tertiary shadow-sm">
        <MsIcon name="military_tech" :size="22" filled />
      </div>
      <div>
        <span class="block font-label-sm text-label-sm uppercase tracking-wider text-outline">Экспедиционный свод</span>
        <h2 class="font-headline-sm text-headline-sm text-on-surface">«Последний бой» на Орловщине</h2>
      </div>
    </div>

    <div class="my-1 grid grid-cols-3 gap-space-xs py-3">
      <div
        v-for="tile in tiles"
        :key="tile.tone"
        class="flex flex-col items-center rounded-md bg-surface-container-lowest p-2 text-center shadow-sm"
      >
        <span class="font-headline-xl-mobile text-headline-xl-mobile font-extrabold tracking-tight" :class="tile.tone">
          {{ formatNumber(tile.value) }}
        </span>
        <span class="mt-1 font-label-sm text-label-sm leading-tight text-on-surface-variant">{{ tile.label }}</span>
      </div>
    </div>

    <div class="mt-4 flex items-start gap-2 rounded-DEFAULT bg-surface-container/60 p-3">
      <MsIcon name="format_quote" :size="18" class="mt-0.5 shrink-0 text-tertiary" />
      <p class="font-body-sm text-body-sm italic leading-relaxed text-on-surface-variant">
        «Война не окончена, пока не похоронен последний солдат»
      </p>
    </div>
  </section>
</template>
