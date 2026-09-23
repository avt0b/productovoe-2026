<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { MyEntry, MyTrip } from '../data'

/**
 * Значки — только за то, что человек действительно сделал в сервисах: выезд
 * с отрядом, подтверждённая краеведом запись, экскурсия. Выдуманных наград нет:
 * пока не заслужил — значок серый и подсказывает, как его получить.
 */
const props = defineProps<{
  trips: MyTrip[] | null
  entries: MyEntry[] | null
  excursions: number | null
}>()

interface Badge {
  id: string
  title: string
  hint: string
  icon: string
  tone: string
  earned: boolean
}

const badges = computed<Badge[]>(() => [
  {
    id: 'trip',
    title: 'В поле с отрядом',
    hint: 'Запишитесь на выезд в «Штабе»',
    icon: 'hiking',
    tone: 'bg-primary-fixed text-primary',
    earned: (props.trips?.length ?? 0) > 0,
  },
  {
    id: 'keeper',
    title: 'Хранитель истории',
    hint: 'Запись в архиве, подтверждённая краеведом',
    icon: 'auto_stories',
    tone: 'bg-tertiary-fixed text-tertiary',
    earned: (props.entries ?? []).some((entry) => entry.status === 'verified'),
  },
  {
    id: 'excursion',
    title: 'Тропа памяти',
    hint: 'Экскурсия с краеведом',
    icon: 'groups',
    tone: 'bg-secondary-fixed text-secondary',
    earned: (props.excursions ?? 0) > 0,
  },
])
</script>

<template>
  <section class="mt-1 flex flex-col gap-space-sm">
    <div class="flex items-center gap-space-xs px-1">
      <MsIcon name="workspace_premium" :size="20" class="text-tertiary" />
      <h3 class="font-headline-sm text-headline-sm text-on-surface">Значки следопыта</h3>
    </div>

    <div class="grid grid-cols-3 gap-space-xs">
      <div
        v-for="badge in badges"
        :key="badge.id"
        class="flex flex-col items-center rounded-DEFAULT bg-surface-container-lowest p-space-sm text-center shadow-sm"
        :class="{ 'opacity-60': !badge.earned }"
      >
        <div
          class="mb-1.5 flex h-12 w-12 items-center justify-center rounded-full shadow-sm"
          :class="badge.earned ? badge.tone : 'bg-surface-container-high text-outline'"
        >
          <MsIcon :name="badge.earned ? badge.icon : 'lock'" :filled="badge.earned" />
        </div>
        <span class="font-label-sm text-label-sm leading-tight text-on-surface">{{ badge.title }}</span>
        <span class="mt-0.5 font-body-sm text-label-sm font-normal leading-tight text-on-surface-variant">
          {{ badge.earned ? 'Получен' : badge.hint }}
        </span>
      </div>
    </div>
  </section>
</template>
