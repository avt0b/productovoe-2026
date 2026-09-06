<script setup lang="ts">
import { computed } from 'vue'

export type BadgeTone = 'verified' | 'pending' | 'error' | 'neutral' | 'info'

const props = withDefaults(defineProps<{ label: string; tone?: BadgeTone }>(), { tone: 'neutral' })

const TONES: Record<BadgeTone, { box: string; dot: string }> = {
  verified: { box: 'bg-verified-container text-verified', dot: 'bg-verified' },
  pending: { box: 'bg-tertiary-fixed text-on-tertiary-fixed', dot: 'bg-tertiary' },
  error: { box: 'bg-error-container text-on-error-container', dot: 'bg-error' },
  info: { box: 'bg-secondary-container text-on-secondary-container', dot: 'bg-secondary' },
  neutral: { box: 'bg-surface-container-high text-on-surface-variant', dot: 'bg-outline' },
}

const style = computed(() => TONES[props.tone])
</script>

<template>
  <span class="chip font-bold" :class="style.box">
    <span class="h-1.5 w-1.5 rounded-full" :class="style.dot" />
    {{ label }}
  </span>
</template>
