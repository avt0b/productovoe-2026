<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { formatDate } from '@/core/format'
import MsIcon from '@/ui/MsIcon.vue'

import type { MyTrip } from '../data'

/** Ближайший выезд, на который человек записан, — или приглашение в «Штаб». */
defineProps<{ trip: MyTrip | null }>()

const router = useRouter()
const canOpenHq = computed(() => router.hasRoute('hq'))
</script>

<template>
  <div class="relative flex flex-col gap-space-sm overflow-hidden rounded-lg bg-secondary-container p-space-md text-on-secondary-container shadow-sm">
    <div class="flex items-center gap-space-xs">
      <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-on-secondary shadow-sm">
        <MsIcon name="backpack" :size="18" />
      </div>
      <div class="min-w-0">
        <span class="block font-label-sm text-label-sm font-bold uppercase tracking-wider text-secondary">
          {{ trip ? 'Ближайший выезд' : 'Выходные с поисковиком' }}
        </span>
        <h3 class="font-label-lg text-label-lg font-bold leading-tight text-on-secondary-fixed">
          {{ trip ? trip.title : 'Вы пока не записаны ни на один выезд' }}
        </h3>
      </div>
    </div>
    <p v-if="trip" class="flex items-center gap-1.5 font-body-sm text-body-sm">
      <MsIcon name="calendar_month" :size="16" />
      {{ formatDate(trip.starts_on) }}<template v-if="trip.location"> • {{ trip.location }}</template>
    </p>
    <RouterLink
      v-if="canOpenHq"
      :to="{ name: 'hq' }"
      class="self-start rounded-full bg-secondary px-space-md py-2 font-label-md text-label-md text-on-secondary active:scale-95"
    >
      {{ trip ? 'Чек-лист и детали' : 'Выбрать выезд' }}
    </RouterLink>
  </div>
</template>
