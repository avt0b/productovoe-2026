<script setup lang="ts">
import { computed } from 'vue'

import { formatNumber } from '@/lib'

const props = withDefaults(
  defineProps<{
    label: string
    value: number | null
    hint?: string | null
    tone?: 'neutral' | 'attention' | 'error'
    icon?: string
  }>(),
  { hint: null, tone: 'neutral', icon: 'analytics' },
)

/** `null` приходит, когда сервис-источник недоступен — это не ноль. */
const unavailable = computed(() => props.value === null)

const valueColor = computed(() => {
  if (unavailable.value) return 'text-outline'
  if (props.tone === 'error') return 'text-error'
  if (props.tone === 'attention') return 'text-tertiary'
  return 'text-primary'
})
</script>

<template>
  <div class="card flex flex-col justify-between">
    <div class="flex items-start justify-between gap-space-2">
      <span
        class="font-label-archive-code text-label-archive-code uppercase tracking-wider text-on-surface-variant"
      >
        {{ label }}
      </span>
      <span class="ms-icon text-[20px]" :class="valueColor">{{ icon }}</span>
    </div>

    <div class="my-space-2 h-px bg-surface-container-highest" />

    <div class="flex flex-col gap-space-1">
      <div class="font-headline-lg text-headline-lg tracking-tight" :class="valueColor">
        {{ unavailable ? '—' : formatNumber(value) }}
      </div>
      <span class="font-body-sm text-body-sm text-on-surface-variant">
        {{ unavailable ? 'Сервис недоступен' : (hint ?? ' ') }}
      </span>
    </div>
  </div>
</template>
