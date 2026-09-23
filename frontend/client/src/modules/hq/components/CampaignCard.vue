<script setup lang="ts">
import { computed } from 'vue'

import { formatMoney } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { Need, Squad } from '../data'

const props = defineProps<{
  need: Need
  squad: Squad | undefined
  /** Командир этого отряда или модератор: может закрыть сбор. */
  canManage: boolean
}>()

defineEmits<{ donate: []; close: [] }>()

const percent = computed(() => {
  const target = props.need.target_amount
  return target ? Math.min(100, Math.round((props.need.collected_amount / target) * 100)) : null
})

const isOpen = computed(() => props.need.status === 'open')
</script>

<template>
  <article class="relative flex flex-col gap-4 rounded-lg bg-surface-container-lowest p-5 shadow-sm">
    <div class="flex items-center justify-between gap-2">
      <span
        v-if="isOpen"
        class="flex items-center gap-1 rounded-full bg-primary-fixed px-3 py-1 font-label-sm text-label-sm text-on-primary-fixed-variant"
      >
        <span class="h-2 w-2 animate-pulse rounded-full bg-primary" />
        Сбор открыт
      </span>
      <span v-else class="rounded-full bg-secondary-container px-3 py-1 font-label-sm text-label-sm text-on-secondary-container">
        Сбор закрыт
      </span>
      <span v-if="squad?.region" class="flex items-center gap-1 font-label-sm text-label-sm text-outline">
        <MsIcon name="location_on" :size="14" />{{ squad.region }}
      </span>
    </div>

    <div class="flex items-center gap-3">
      <div class="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-secondary-container text-secondary">
        <MsIcon name="flag" />
      </div>
      <div class="min-w-0">
        <h3 class="font-headline-sm text-headline-sm leading-tight text-on-surface">{{ need.title }}</h3>
        <p class="truncate font-body-sm text-body-sm text-outline">{{ squad?.name ?? 'Поисковый отряд' }}</p>
      </div>
    </div>

    <div v-if="need.description" class="rounded-DEFAULT bg-surface-container-low p-3.5">
      <p class="font-body-md text-body-md leading-snug text-on-surface">{{ need.description }}</p>
    </div>

    <div class="flex flex-col gap-2">
      <div class="flex items-baseline justify-between">
        <span class="font-headline-sm text-headline-sm font-extrabold text-on-surface">{{ formatMoney(need.collected_amount) }}</span>
        <span v-if="need.target_amount" class="font-body-sm text-body-sm text-outline">
          из {{ formatMoney(need.target_amount) }} ({{ percent }}%)
        </span>
      </div>
      <div
        v-if="percent !== null"
        class="h-3 w-full overflow-hidden rounded-full bg-surface-container-high p-0.5"
        role="progressbar"
        :aria-valuenow="percent"
        aria-valuemin="0"
        aria-valuemax="100"
        :aria-label="`Собрано ${percent}%`"
      >
        <div class="h-full rounded-full bg-primary-container transition-all duration-500" :style="{ width: `${percent}%` }" />
      </div>
    </div>

    <button
      v-if="isOpen"
      type="button"
      class="flex w-full items-center justify-center gap-2 rounded-full bg-primary px-6 py-3.5 font-label-lg text-label-lg text-on-primary shadow-md shadow-primary/25 transition-all hover:brightness-105 active:scale-[0.98]"
      @click="$emit('donate')"
    >
      <MsIcon name="volunteer_activism" :size="20" filled />
      Помочь отряду
    </button>
    <button
      v-if="isOpen && canManage"
      type="button"
      class="-mt-2 self-center font-label-md text-label-md text-on-surface-variant underline-offset-2 hover:underline"
      @click="$emit('close')"
    >
      Закрыть сбор
    </button>
  </article>
</template>
