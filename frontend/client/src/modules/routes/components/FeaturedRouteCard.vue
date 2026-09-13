<script setup lang="ts">
import { formatNumber } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { FeaturedRoute } from '../data'

defineProps<{
  route: FeaturedRoute
  canStart: boolean
}>()

defineEmits<{ start: [] }>()
</script>

<template>
  <div class="z-40 -mt-6 w-full px-margin">
    <div class="flex w-full flex-col gap-space-sm rounded-sheet bg-surface-container-lowest p-space-md shadow-sheet">
      <div class="mb-0.5 h-1.5 w-10 self-center rounded-full bg-surface-container-highest" />

      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1.5 rounded-full bg-tertiary-fixed px-2.5 py-1 text-on-tertiary-fixed-variant">
          <MsIcon name="auto_awesome" :size="15" filled class="text-tertiary" />
          <span class="font-label-sm text-label-sm uppercase tracking-wide">Семейный квест дня</span>
        </div>
        <button
          type="button"
          aria-label="Добавить в избранное"
          class="flex h-8 w-8 items-center justify-center rounded-full bg-surface-container-low text-outline transition-colors hover:text-primary"
        >
          <MsIcon name="bookmark_border" :size="18" />
        </button>
      </div>

      <div>
        <h2 class="font-headline-md text-headline-md text-on-surface">{{ route.title }}</h2>
        <p class="mt-0.5 font-body-sm text-body-sm text-outline">{{ route.description }}</p>
      </div>

      <div class="flex flex-wrap items-center gap-space-xs pt-1">
        <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
          <MsIcon name="directions_walk" :size="15" class="text-secondary" />
          {{ formatNumber(route.distanceKm) }} км
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
          <MsIcon name="schedule" :size="15" class="text-outline" />
          {{ route.durationMinutes }} мин
        </span>
        <span
          class="inline-flex items-center gap-1 rounded-full bg-secondary-container px-2.5 py-1 font-label-md text-label-md font-bold text-on-secondary-container"
        >
          <MsIcon name="family_restroom" :size="14" />
          {{ route.difficulty }}
        </span>
        <span class="inline-flex items-center gap-1 rounded-full bg-surface-container-low px-2.5 py-1 font-label-md text-label-md text-on-surface">
          <MsIcon name="star" :size="15" filled class="text-tertiary" />
          {{ formatNumber(route.rating) }} ({{ route.reviews }})
        </span>
      </div>

      <div class="mt-1 flex items-start gap-space-sm rounded-2xl bg-quest p-space-sm">
        <div class="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-tertiary-fixed text-tertiary shadow-sm">
          <MsIcon name="podcasts" :size="22" />
        </div>
        <div class="min-w-0 flex-1">
          <p class="font-label-md text-label-md font-bold leading-snug text-on-tertiary-fixed-variant">{{ route.task.title }}</p>
          <p class="mt-0.5 font-body-sm text-body-sm leading-relaxed text-on-surface-variant">
            {{ route.task.text }} <span class="font-semibold text-tertiary">{{ route.task.reward }}</span>!
          </p>
        </div>
      </div>

      <div class="flex items-center gap-space-sm pt-2">
        <button
          type="button"
          class="flex h-13 flex-1 items-center justify-center gap-2 rounded-full bg-primary px-space-md font-headline-sm text-headline-sm text-on-primary shadow-lg shadow-primary/30 transition-transform hover:bg-primary-container active:scale-[0.98] disabled:opacity-60"
          :disabled="!canStart"
          @click="$emit('start')"
        >
          <MsIcon name="navigation" :size="22" />
          Начать путешествие
        </button>
        <button
          type="button"
          aria-label="Слушать аудиогид"
          class="flex h-13 w-13 items-center justify-center rounded-full bg-secondary-fixed text-on-secondary-fixed transition-colors hover:bg-secondary-fixed-dim"
        >
          <MsIcon name="headphones" :size="22" />
        </button>
      </div>
    </div>
  </div>
</template>
