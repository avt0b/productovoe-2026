<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from './MsIcon.vue'

/** Сообщение внутри экрана: что получилось, что нет и почему. */
const props = withDefaults(
  defineProps<{
    tone?: 'info' | 'success' | 'error'
    icon?: string
  }>(),
  { tone: 'info', icon: undefined },
)

const STYLE = {
  info: { box: 'bg-surface-container-low text-on-surface-variant', icon: 'info' },
  success: { box: 'bg-secondary-container text-on-secondary-container', icon: 'check_circle' },
  error: { box: 'bg-error-container text-on-error-container', icon: 'error' },
} as const

const style = computed(() => STYLE[props.tone])
</script>

<template>
  <p
    class="flex items-start gap-space-sm rounded-DEFAULT px-space-sm py-2 font-body-sm text-body-sm"
    :class="style.box"
    :role="tone === 'error' ? 'alert' : 'status'"
  >
    <MsIcon :name="icon ?? style.icon" :size="18" class="mt-0.5 shrink-0" />
    <span class="min-w-0"><slot /></span>
  </p>
</template>
