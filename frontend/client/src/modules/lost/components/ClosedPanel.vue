<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import MsIcon from '@/ui/MsIcon.vue'

import type { LostAlertController } from '../useLostAlert'

/** Карточка закрытого поиска: «нашлись», «отбой» или «закрыт по времени». */
const props = defineProps<{ lost: LostAlertController }>()

const router = useRouter()
const alert = computed(() => props.lost.alert.value)
const name = computed(() => alert.value?.lost.display_name ?? 'участник')

const view = computed(() => {
  const status = alert.value?.status
  if (status === 'found') {
    return { icon: 'celebration', title: 'Нашлись! Все вместе', note: alert.value?.resolved_by ? `Отметил(а): ${alert.value.resolved_by.display_name}` : '' }
  }
  if (status === 'cancelled') return { icon: 'info', title: `Отбой тревоги — ${name.value} не потерялся(-ась)`, note: '' }
  return { icon: 'schedule', title: 'Поиск закрыт по времени', note: '' }
})

function toGroup(): void {
  const excursionId = alert.value?.excursion_id
  if (excursionId && router.hasRoute('excursion-walk')) void router.push({ name: 'excursion-walk', params: { excursionId } })
  else if (router.hasRoute('excursions')) void router.push({ name: 'excursions' })
}

// Поиск закрыт — маршрут больше не нужен.
onMounted(() => props.lost.pointRoute.stop())
</script>

<template>
  <div class="flex flex-col gap-space-sm">
    <div class="flex items-center gap-space-sm">
      <span class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-tertiary text-on-tertiary">
        <MsIcon :name="view.icon" :size="24" />
      </span>
      <div class="flex min-w-0 flex-col">
        <p class="font-headline-sm text-headline-sm text-white">{{ view.title }}</p>
        <p v-if="view.note" class="font-body-sm text-body-sm text-white/70">{{ view.note }}</p>
      </div>
    </div>
    <button
      type="button"
      class="flex h-11 items-center justify-center gap-space-xs rounded-full bg-primary-container font-label-lg text-label-lg text-white shadow-stamp transition-colors hover:bg-primary active:scale-[0.98]"
      @click="toGroup"
    >
      <MsIcon name="map" :size="18" />
      К карте группы
    </button>
  </div>
</template>
