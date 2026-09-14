<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { ExcursionStatus } from '../data'
import { STATUS_LABELS } from '../format'

defineProps<{ status: ExcursionStatus }>()

const TONES: Record<ExcursionStatus, { chip: string; icon: string }> = {
  scheduled: { chip: 'bg-secondary-container text-on-secondary-container', icon: 'event_available' },
  gathering: { chip: 'bg-primary text-on-primary', icon: 'vibration' },
  finished: { chip: 'bg-surface-container-high text-on-surface-variant', icon: 'task_alt' },
  cancelled: { chip: 'bg-error-container text-on-error-container', icon: 'event_busy' },
}
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 font-label-sm text-label-sm"
    :class="TONES[status].chip"
  >
    <MsIcon :name="TONES[status].icon" :size="14" :class="{ 'animate-pulse': status === 'gathering' }" />
    {{ STATUS_LABELS[status] }}
  </span>
</template>
