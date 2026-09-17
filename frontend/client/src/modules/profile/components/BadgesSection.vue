<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

import type { Badge } from '../data'

defineProps<{
  badges: Badge[]
  total: number
}>()

const TONES: Record<Badge['tone'], string> = {
  primary: 'bg-primary-fixed text-primary',
  secondary: 'bg-secondary-fixed text-secondary',
  tertiary: 'bg-tertiary-fixed text-tertiary',
}
</script>

<template>
  <section class="mt-1 flex flex-col gap-space-sm">
    <div class="flex items-center justify-between px-1">
      <div class="flex items-center gap-space-xs">
        <MsIcon name="workspace_premium" :size="20" class="text-tertiary" />
        <h3 class="font-headline-sm text-headline-sm text-on-surface">Мои награды и значки</h3>
      </div>
      <button type="button" class="font-label-sm text-label-sm text-primary hover:underline">Все {{ total }}</button>
    </div>

    <div class="grid grid-cols-3 gap-space-xs">
      <div
        v-for="badge in badges"
        :key="badge.id"
        class="flex flex-col items-center rounded-DEFAULT bg-surface-container-lowest p-space-sm text-center shadow-sm"
      >
        <div class="mb-1.5 flex h-12 w-12 items-center justify-center rounded-full shadow-sm" :class="TONES[badge.tone]">
          <MsIcon :name="badge.icon" :filled="badge.filled" />
        </div>
        <span class="font-label-sm text-label-sm leading-tight text-on-surface">{{ badge.title }}</span>
        <span class="mt-0.5 font-body-sm text-label-sm font-normal text-on-surface-variant">{{ badge.subtitle }}</span>
      </div>
    </div>
  </section>
</template>
