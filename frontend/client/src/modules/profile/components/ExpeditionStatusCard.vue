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
  <section class="flex items-start gap-space-sm rounded-2xl bg-surface-container-lowest p-space-md shadow-document">
    <span class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-secondary-container text-on-secondary-container" aria-hidden="true">
      <MsIcon name="backpack" :size="20" />
    </span>
    <div class="flex min-w-0 flex-1 flex-col gap-0.5">
      <p class="font-archival text-archival uppercase text-on-surface-variant">
        {{ trip ? 'Ближайший выезд' : 'Выходные с поисковиком' }}
      </p>
      <h2 class="font-headline-sm text-headline-sm text-on-surface">
        {{ trip ? trip.title : 'Вы пока не записаны ни на один выезд' }}
      </h2>
      <p v-if="trip" class="flex items-center gap-1 font-body-sm text-body-sm text-on-surface-variant">
        <MsIcon name="calendar_month" :size="15" class="shrink-0 text-secondary" />
        {{ formatDate(trip.starts_on) }}<template v-if="trip.location"> · {{ trip.location }}</template>
      </p>
      <RouterLink
        v-if="canOpenHq"
        :to="{ name: 'hq', query: { tab: 'trips' } }"
        class="mt-space-xs flex items-center gap-space-xs self-start rounded-full bg-surface-container-high px-space-md py-2 font-label-md text-label-md text-on-surface active:scale-95"
      >
        {{ trip ? 'Чек-лист и детали' : 'Выбрать выезд' }}
        <MsIcon name="arrow_forward" :size="18" />
      </RouterLink>
    </div>
  </section>
</template>
