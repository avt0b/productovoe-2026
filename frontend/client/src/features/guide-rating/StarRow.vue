<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import { formatRating } from './format'

/** Пять звёзд по средней оценке. Округление — как в GuideRatingBadge. */
const props = withDefaults(defineProps<{ value: number; size?: number }>(), { size: 16 })

const icons = computed(() =>
  [1, 2, 3, 4, 5].map((n) => (props.value >= n - 0.25 ? 'star' : props.value >= n - 0.75 ? 'star_half' : 'star_border')),
)
</script>

<template>
  <span class="inline-flex items-center gap-0.5" role="img" :aria-label="`Оценка ${formatRating(value)} из 5`">
    <MsIcon v-for="(icon, i) in icons" :key="i" :name="icon" :size="size" filled class="text-tertiary" />
  </span>
</template>
