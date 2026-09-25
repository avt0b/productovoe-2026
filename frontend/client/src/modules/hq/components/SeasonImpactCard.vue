<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber, plural } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { SeasonStats } from '../data'

const props = defineProps<{ stats: SeasonStats }>()

/** Итоги «Последнего боя» по Орловщине. Цвета — как у стадий на его карте. */
const tiles = computed(() => [
  {
    key: 'found',
    value: props.stats.discovered,
    label: plural(props.stats.discovered, ['ждёт проверки', 'ждут проверки', 'ждут проверки']),
    tone: 'text-primary',
  },
  {
    key: 'confirmed',
    value: props.stats.confirmed,
    label: plural(props.stats.confirmed, ['подтверждено архивом', 'подтверждены архивом', 'подтверждено архивом']),
    tone: 'text-tertiary',
  },
  {
    key: 'raised',
    value: props.stats.raised,
    label: plural(props.stats.raised, ['останки подняты', 'останков поднято', 'останков поднято']),
    tone: 'text-secondary',
  },
])
</script>

<template>
  <section class="flex flex-col gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <div class="flex items-center justify-between gap-space-sm">
      <p class="font-archival text-archival uppercase text-on-surface-variant">Итоги «Последнего боя»</p>
      <RouterLink
        :to="{ name: 'last-stand' }"
        class="flex shrink-0 items-center gap-0.5 font-label-md text-label-md text-secondary transition-opacity hover:opacity-80"
      >
        Карта мест
        <MsIcon name="arrow_forward" :size="18" />
      </RouterLink>
    </div>

    <dl class="grid grid-cols-3 divide-x divide-outline-variant/60">
      <div v-for="tile in tiles" :key="tile.key" class="flex flex-col-reverse items-center justify-end px-1 text-center">
        <dt class="font-label-sm text-label-sm leading-tight text-on-surface-variant">{{ tile.label }}</dt>
        <dd class="font-headline-lg text-headline-lg short:text-headline-lg-mobile" :class="tile.tone">{{ formatNumber(tile.value) }}</dd>
      </div>
    </dl>

    <p class="flex items-start gap-space-xs border-t border-outline-variant/60 pt-space-sm font-body-sm text-body-sm italic text-on-surface-variant short:hidden">
      <MsIcon name="format_quote" :size="18" class="shrink-0 text-tertiary" />
      Война не окончена, пока не похоронен последний солдат
    </p>
  </section>
</template>
