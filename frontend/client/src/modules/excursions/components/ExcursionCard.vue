<script setup lang="ts">
import { computed } from 'vue'

import MsIcon from '@/ui/MsIcon.vue'

import type { Excursion } from '../data'
import { formatStart } from '../format'
import StatusChip from './StatusChip.vue'

const props = defineProps<{
  excursion: Excursion
  /** Выбрана меткой на карте — подсвечиваем. */
  selected?: boolean
}>()

/** Кем экскурсия приходится смотрящему — одной подписью. */
const myRole = computed(() => {
  const viewer = props.excursion.viewer
  if (!viewer) return null
  if (viewer.is_guide) return { icon: 'record_voice_over', text: 'Вы ведёте' }
  if (viewer.checked_in_at) return { icon: 'task_alt', text: 'Вы в группе' }
  if (viewer.registered) return { icon: 'how_to_reg', text: 'Вы записаны' }
  return null
})
</script>

<template>
  <RouterLink
    :to="{ name: 'excursion', params: { excursionId: excursion.id } }"
    class="flex flex-col gap-space-xs rounded-lg bg-surface-container-lowest p-space-md shadow-sm transition-shadow hover:shadow-md"
    :class="{ 'ring-2 ring-primary': selected }"
  >
    <div class="flex flex-wrap items-center justify-between gap-space-xs">
      <StatusChip :status="excursion.status" />
      <span
        v-if="myRole"
        class="inline-flex items-center gap-1 rounded-full bg-tertiary-fixed px-2.5 py-1 font-label-sm text-label-sm text-on-tertiary-fixed-variant"
      >
        <MsIcon :name="myRole.icon" :size="14" />
        {{ myRole.text }}
      </span>
    </div>

    <h3 class="font-headline-sm text-headline-sm text-on-surface">{{ excursion.title }}</h3>

    <p class="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
      <MsIcon name="schedule" :size="16" class="shrink-0 text-outline" />
      {{ formatStart(excursion.starts_at) }}
    </p>
    <p v-if="excursion.place_name" class="flex items-center gap-1.5 font-body-sm text-body-sm text-on-surface-variant">
      <MsIcon name="location_on" :size="16" class="shrink-0 text-outline" />
      <span class="truncate">{{ excursion.place_name }}</span>
    </p>

    <p class="flex items-center gap-1.5 font-label-md text-label-md text-on-surface">
      <MsIcon name="groups" :size="16" class="shrink-0 text-secondary" />
      <template v-if="excursion.status === 'gathering' || excursion.status === 'finished'">
        Пришли {{ excursion.checked_in_count }} из {{ excursion.registered_count }}
      </template>
      <template v-else>Записались {{ excursion.registered_count }} из {{ excursion.capacity }}</template>
    </p>
  </RouterLink>
</template>
