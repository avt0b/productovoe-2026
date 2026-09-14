<script setup lang="ts">
import MsIcon from '@/ui/MsIcon.vue'

defineProps<{
  title: string
  season: string
  nextRank: string
  progress: number
  hint: string
}>()
</script>

<template>
  <div class="relative flex flex-col gap-space-sm overflow-hidden rounded-lg bg-secondary-container p-space-md text-on-secondary-container shadow-sm">
    <div class="flex items-center justify-between gap-space-sm">
      <div class="flex items-center gap-space-xs">
        <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-on-secondary shadow-sm">
          <MsIcon name="military_tech" :size="18" />
        </div>
        <div>
          <span class="block font-label-sm text-label-sm font-bold uppercase tracking-wider text-secondary">Текущий статус</span>
          <h3 class="font-label-lg text-label-lg font-bold leading-tight text-on-secondary-fixed">{{ title }}</h3>
        </div>
      </div>
      <span class="shrink-0 rounded-full bg-secondary/15 px-2 py-0.5 font-label-sm text-label-sm text-secondary">{{ season }}</span>
    </div>

    <div class="mt-1 flex flex-col gap-1.5">
      <div class="flex items-center justify-between">
        <span class="font-label-sm text-label-sm">{{ nextRank }}</span>
        <span class="font-label-sm text-label-sm">{{ progress }}%</span>
      </div>
      <div
        class="h-2.5 w-full overflow-hidden rounded-full bg-surface-container-lowest/80 p-0.5 shadow-inner"
        role="progressbar"
        :aria-valuenow="progress"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="nextRank"
      >
        <div class="h-full rounded-full bg-secondary transition-all duration-700" :style="{ width: `${progress}%` }" />
      </div>
      <p class="font-body-sm text-body-sm leading-normal text-on-secondary-container/80">{{ hint }}</p>
    </div>
  </div>
</template>
